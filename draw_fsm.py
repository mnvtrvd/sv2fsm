import math
import networkx as nx
import random
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

TIMEOUT = 5
DARK = False
HOME = str(Path.home())

W = 2000
H = W
R_OUT = round(W/3)
R_STATE = round(R_OUT/10)
THICKNESS = round(W/750)
GLOBAL_OFFSET = math.pi/2
STEPS = 10

def scale_rstate(scale=1):
    global R_STATE
    R_STATE = round(scale*R_OUT/10)

################################################################################

# https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection
def get_intersection(edge1, edge2):
    x1 = edge1[0][0]
    y1 = edge1[0][1]
    x2 = edge1[1][0]
    y2 = edge1[1][1]
    x3 = edge2[0][0]
    y3 = edge2[0][1]
    x4 = edge2[1][0]
    y4 = edge2[1][1]

    denom = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
    t_num = (x1-x3)*(y3-y4)-(y1-y3)*(x3-x4)
    u_num = (x2-x1)*(y1-y3)-(y2-y1)*(x1-x3)

    if denom == 0:
        return (False, [])

    t = t_num/denom
    u = u_num/denom

    if (t == 0 and u == 0) or (t == 1 and u == 0) or (t == 0 and u == 1) or (t == 1 and u == 1):
        return (False, [])

    point = (round(x1+t*(x2-x1)), round(y1+t*(y2-y1)))
 
    if (t >= 0 and t <= 1) and (u >= 0 and u <= 1):
        return (True, point)
    else:
        return (False, [])

def get_length(x1, y1, x2, y2):
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)

def get_midpoint(x1, y1, x2, y2):
    minx = min(x1, x2)
    miny = min(y1, y2)
    maxx = max(x1, x2)
    maxy = max(y1, y2)
    x = minx + (maxx-minx)/2
    y = miny + (maxy-miny)/2
    return x, y

def get_slope(edge):
    x1 = edge[0][0]
    y1 = edge[0][1]
    x2 = edge[1][0]
    y2 = edge[1][1]
    
    if x2 != x1:
        return (y2-y1)/(x2-x1)
    else:
        return float('inf')

def get_angle(x1, y1, x2, y2):
    return math.atan2(y2-y1, x2-x1)

def get_closest(arr, x, y):
    l = 0
    shortest = []
    for p in arr:
        if l == 0:
            l = get_length(x, y, p[0], p[1])
            shortest = [p]
        else:
            length = get_length(x, y, p[0], p[1])
            if length < l:
                l = length
                shortest = [p]
            elif length == l:
                shortest.append(p)

    return l, shortest

def get_face_angle(x1, y1, x2, y2):
    delta = math.atan2(y2, x2) - math.atan2(y1, x1)

    while (delta > math.pi) or (delta < -math.pi):
        if (delta < -math.pi):
            delta += 2*math.pi
        else:    
            delta -= 2*math.pi

    return delta

def in_circle(pos, r, x, y):
    l = get_length(pos[0], pos[1], x, y)
    if l <= r:
        return True
    return False

# https://www.eecs.umich.edu/courses/eecs380/HANDOUTS/PROJ2/InsidePoly.html#:~:text=To%20determine%20the%20status%20of,point%20is%20outside%20the%20polygon.
def in_face(face, pos, x, y):
    angle = 0
    count = len(face)

    for i in range(count):
        x1 = pos[face[i]][0] - x
        y1 = pos[face[i]][1] - y
        x2 = pos[face[(i+1)%count]][0] - x
        y2 = pos[face[(i+1)%count]][1] - y
        angle += get_face_angle(x1, y1, x2, y2)
    
    return abs(angle) >= math.pi

################################################################################

def get_longest(states):
    length = 0
    longest = ""
    for state in states:
        if len(state) > length:
            length = len(state)
            longest = state
    
    return length, longest

def check_adjacent(states, outer, inner):
    if (states[0] in outer) != (states[1] in outer):
        return False

    l = outer
    if states[0] in inner:
        l = inner

    if len(l) < 3:
        return True
    
    i1 = l.index(states[0])
    i2 = l.index(states[1])

    if (abs(i1-i2) == 1) or (abs(i1-i2) == len(l)-1):
        return True
    
    return False

def is_planar_graph(states):
    fsm = nx.MultiDiGraph()
    for src in states:
        filename = "tmp/" + src + ".sv"
        with open(filename, "r") as f:
            lines = f.readlines()

        for line in lines:
            tup = line.partition(", ")
            dst = tup[0]
            transition = tup[2]
            fsm.add_edge(src, dst, cond=transition)

    is_planar, _ = nx.algorithms.planarity.check_planarity(fsm)
    return is_planar

################################################################################

def swap_nodes(pos, n1, n2, outer, inner):
    p1 = pos[n1]
    p2 = pos[n2]
    pos[n1] = p2
    pos[n2] = p1

    if n1 in outer:
        outer.remove(n1)
        outer.append(n2)
        inner.remove(n2)
        inner.append(n1)
    else:
        outer.remove(n2)
        outer.append(n1)
        inner.remove(n1)
        inner.append(n2)

    return pos

def rem_chains(trans):
    done = False
    chain = []
    start = time.time()

    while not done:
        single = []
        for state in trans:
            if len(trans[state]) == 1:
                dst = trans[state][0]
                trans[dst].remove(state)
                trans[state] = []
                single.append(state)
                chain.append(state)
        
        for state in single:
            del trans[state]

        done = all(len(trans[state]) != 1 for state in trans)
        
        if time.time() - start > TIMEOUT:
            print("WARNING: exceeded maximum runtime of", TIMEOUT, "secs trying to remove chains")
            break

    return chain

################################################################################

def get_xy(r, states, w=W, h=H, offset=0):
    pos = {}
    count = len(states)
    if count == 1:
        pos[states[0]] = (round(w/2), round(h/2))
        return pos

    for i in range(count):
        state = states[i]
        degree = 2*i*math.pi/count + offset - GLOBAL_OFFSET
        x = w/2 + r*math.cos(degree)
        y = h/2 + r*math.sin(degree)
        pos[state] = (round(x), round(y))

    return pos

def get_transitions(edges, states):
    trans = {}
    for state in states:
        trans[state] = []
        for edge in edges:
            n1 = edge[0]
            n2 = edge[1]
            if (n1 == state) != (n2 == state):
                n = n2 if n1 == state else n1
                if (n not in trans[state]) and (n in states):
                    trans[state].append(n)
    
    return trans

def get_edges(states, pos, self_loops=False):
    edges = {}
    count = len(states)
    for i in range(count):
        state = states[i]
        filename = "tmp/" + state + ".sv"
        with open(filename, "r") as f:
            lines = f.readlines()

        for line in lines:
            tup = line.partition(", ")
            dst = tup[0]
            tran = tup[2]

            if (dst == state) == self_loops:
                if (state in pos) and (dst in pos):
                    edges[(state, dst)] = (pos[state], pos[dst])

    return edges

def get_edge_count(states, edges, include_self_loops=True, directed=False):
    undirected = []

    for edge in edges:
        var0 = edge[0] + ":" + edge[1]
        var1 = edge[1] + ":" + edge[0]

        if directed or ((var0 not in undirected) and (var1 not in undirected)):
            undirected.append(var0)

    count = {}
    for state in states:
        count[state] = 0

        for uedge in undirected:
            nodes = uedge.split(":")
            if include_self_loops:
                if (nodes[0] == state) or (nodes[1] == state):
                    count[state] += 1
            else:
                if (nodes[0] == state) != (nodes[1] == state):
                    count[state] += 1

    return count

def get_points(edges):
    points = {}
    for edge in edges:
        found = False
        for other in edges:
            found, point = get_intersection(edges[edge], edges[other])
            if found:
                points[point] = (edge, other)
                break

    return points

def get_values(outer, inner, center=(W,H), offset=0, r_in=0, skip=False):
    states = outer + inner
    pos = get_xy(R_OUT, outer)
    if skip:
        for istate in inner:
            pos[istate] = (round(W/2), round(H/2))
    else:
        if r_in == 0:
            while 2**r_in < len(inner):
                r_in += 1
        pos.update(get_xy(r_in, inner, center[0], center[1], offset))
    edges = get_edges(states, pos)
    points = get_points(edges)
    return pos, edges, points

def get_faces(target, trans, outer):
    start = time.time()
    path = []
    visited = []
    faces = []

    while len(faces) != target:
        for node in visited:
            if node in path:
                path.remove(node)

        if path == []:
            valid = set(trans) & set(outer)
            for face in faces:
                valid = valid - set(face)
            if len(valid) == 0:
                valid = set(trans) & set(outer)

            i = random.randrange(len(valid))
            path = [list(valid)[i]]
            visited = []
        else:
            src = path[0]
            curr = path[-1]
            if (len(path) > 2) and (src in trans[curr]):    
                valid = set(trans) & set(outer)
                if target == 1:
                    faces.append(path)
                elif all(set(face) != set(path) for face in faces):
                    if not all(node in path for node in valid):
                        faces.append(path)

                path = []
                visited = []
                continue
            
            flag = True
            nodes = trans[curr]
            random.shuffle(nodes)
            for nxt in nodes:
                if (nxt not in path) and (nxt not in visited) and (nxt in outer):
                    path = path + [nxt]
                    flag = False
                    break

            if flag:
                visited.append(curr)

        if time.time() - start > TIMEOUT:
            print("WARNING: exceeded maximum runtime of", TIMEOUT, "secs trying to get faces")

    return faces

def get_centroid(face, pos):
    x = 0
    y = 0

    for state in face:
        x += pos[state][0]
        y += pos[state][1]

    # multiplying by 2 to get bounding box it is center of
    return (round(2*x/len(face)), round(2*y/len(face)))

def get_edge_len(edges, outer):
    in_out_edges = []
    edge_len = 0
    for edge in edges:
        src = edge[0]
        dst = edge[1]
        if ((src in outer) != (dst in outer)) and (edge not in in_out_edges):
            in_out_edges.append(edge)
            x1 = edges[edge][0][0]
            y1 = edges[edge][0][1]
            x2 = edges[edge][1][0]
            y2 = edges[edge][1][1]
            edge_len += get_length(x1, y1, x2, y2)
    
    return edge_len

def get_arc_points(points, edge, height, step=0, angle=90):
    if step == STEPS:
        return

    x1 = edge[0][0]
    y1 = edge[0][1]
    x2 = edge[1][0]
    y2 = edge[1][1]

    x, y = get_midpoint(x1, y1, x2, y2)
    m = get_slope(((x1, y1), (x2, y2)))

    nh = height*math.sin(angle*math.pi/180)

    if abs(m) < 1:
        points[angle] = (x, y + nh)
    else:
        points[angle] = (x + nh, y)

    dtheta = 45/(2**step)

    return get_arc_points(points, ((x1, y1), (x, y)), height, step+1, angle - dtheta), get_arc_points(points, ((x, y), (x2, y2)), height, step+1, angle + dtheta)

def get_scale(states, edge, outer, inner):
    scale = 1
    x, y = get_midpoint(edge[0][0], edge[0][1], edge[1][0], edge[1][1])
    if x < W/2:
        scale *= -1

    length = get_length(edge[0][0], edge[0][1], edge[1][0], edge[1][1])
    scale *= length/12

    if check_adjacent(states, outer, inner):
        scale *= 2

    return round(scale)

def get_outer_midpoints(outer, pos):
    src = outer[0]
    tmp = outer[1:]
    edges = []
    midpoints = []
    for state in tmp:
        edges.append((src, state))
        midpoints.append(get_midpoint(pos[src][0], pos[src][1], pos[state][0], pos[state][1]))
        src = state
    
    edges.append((src, outer[0]))
    midpoints.append(get_midpoint(pos[src][0], pos[src][1], pos[outer[0]][0], pos[outer[0]][1]))

    return edges, midpoints

################################################################################

def move_inwards(pos, edges, points, outer, inner):
    start = time.time()
    states = outer + inner
    counts = get_edge_count(states, edges, False)

    while len(points) > 0:
        point = list(points.keys())[0]
        state_edges = points[point]
        nodes = {}
        for i in range(2):
            for j in range(2):
                nodes[state_edges[i][j]] = counts[state_edges[i][j]]
    
        min_edges = ("", 0)
        for node in nodes:
            if node not in inner:
                if min_edges[0] == "":
                    min_edges = (node, nodes[node])
                elif nodes[node] < min_edges[1]:
                    min_edges = (node, nodes[node])
        
        inner.append(min_edges[0])
        outer.remove(min_edges[0])

        # update position of that node
        pos, edges, points = get_values(outer, inner, skip=True)

        if time.time() - start > TIMEOUT:
            print("WARNING: exceeded maximum runtime of", TIMEOUT, "secs trying to move nodes inwards")
    
    pos, edges, points = get_values(outer, inner)
    return pos, edges, points

def resize_outer(inner):
    if len(inner) == 0:
        scale_rstate(1.5)
        return False

    return True

def decrowd(outer, inner):
    if len(outer) < len(inner):
        _, _, points = get_values(inner, outer)
        if len(points) == 0:
            # swap the two lists while maintaining pointer
            states = outer + inner

            outer.clear()
            for state in inner:
                outer.append(state)

            inner.clear()
            for state in states:
                if state not in outer:
                    inner.append(state)

    return get_values(outer, inner)

def recenter_inner(pos, edges, outer, inner):
    trans = get_transitions(edges, outer)
    chains = rem_chains(trans)
    new_center = (W, H)
    face = None

    v = len(trans)
    e  = 0
    for tran in trans:
        e += len(trans[tran])

    # based off euler's formula v - e + f = 2
    f = 2 + round(e/2) - v
    if f-1 > 0:
        faces = get_faces(f-1, trans, outer)

        # simpler method of just placing all the inner nodes in the largest face
        if len(faces) > 0:
            _, face = get_longest(faces)
            new_center = get_centroid(face, pos)

    pos, edges, points = get_values(outer, inner, new_center)

    return pos, edges, points, new_center, face

def rotate_inner(new_center, r_in, outer, inner):
    best = 0
    _, edges, points = get_values(outer, inner, new_center, offset=best, r_in=r_in)
    if len(inner) > 1:
        edge_sum = get_edge_len(edges, outer)
        intersections = len(points)
        for offset in range(1, 360, 1):
            _, edges, points = get_values(outer, inner, new_center, offset=offset, r_in=r_in)
            if len(points) <= intersections:
                edge_len = get_edge_len(edges, outer)
                if (len(points) < intersections) or (edge_len < edge_sum):
                    best = offset
                    edge_sum = edge_len
                    intersections = len(points)

    pos, edges, points = get_values(outer, inner, new_center, offset=best, r_in=r_in)
    return pos, edges, points, best

def resize_inner(new_center, face, outer, inner):
    r_in = 0
    states = outer + inner
    pos, edge, points = get_values(outer, inner, new_center)

    if len(inner) > 1:
        while 2**r_in < len(inner):
            r_in += 1
        
        while r_in < R_OUT/3:
            r_in += 10
            pos, edge, points = get_values(outer, inner, new_center, r_in=r_in)
            
            for angle in range(0, 360, 10):
                x = new_center[0]/2 + r_in*math.cos(angle)
                y = new_center[1]/2 + r_in*math.sin(angle)
                within = True
                if face != None:
                    within = in_face(face, pos, x, y)
                if not within:
                    if r_in > R_STATE:
                        r_in = r_in - R_STATE

                    r_in = r_in*0.8

                    pos, edge, points = get_values(outer, inner, new_center, r_in=r_in)
                    return pos, edge, points, r_in

    pos, edge, points = get_values(outer, inner, new_center)
    return pos, edge, points, r_in

def swap_inwards(pos, edges, points, outer, inner):
    start = time.time()
    states = outer + inner

    while len(points) > 0:
        nodes = {}
        for i in range(2):
            for j in range(2):
                n = list(points.values())[0][i][j]
                nodes[n] = "out" if (n in outer) else "in"
        
        loc = list(nodes.values())
        nodes = list(nodes.keys())

        if (loc[0] != loc[1]) and (loc[2] != loc[3]):
            if loc[0] != loc[2]:
                swap_nodes(pos, nodes[0], nodes[2], outer, inner)
            else:
                swap_nodes(pos, nodes[0], nodes[3], outer, inner)

        edges = get_edges(states, pos)
        points = get_points(edges)

        if time.time() - start > TIMEOUT:
            print("WARNING: exceeded maximum runtime of", TIMEOUT, "secs trying to swap nodes inwards")
            break
    
    return pos, edges, points

def rearrange_states(pos, edges, points, states):
    outer = states
    inner = []
    new_center = W/2, H/2

    pos, edges, points = move_inwards(pos, edges, points, outer, inner)
    complicated = resize_outer(inner)
    pos, edges, points = get_values(outer, inner)

    if complicated:
        pos, edges, points = decrowd(outer, inner)
        pos, edges, points, new_center, face = recenter_inner(pos, edges, outer, inner)
        pos, edges, points, r_in = resize_inner(new_center, face, outer, inner)
        pos, edges, points, offset = rotate_inner(new_center, r_in, outer, inner)
        pos, edges, points = swap_inwards(pos, edges, points, outer, inner)

    if len(points) > 0:
        print("WARNING: the graph is still not planar despite applying all transformations, returning as planar of a graph as possible")

    return pos, edges, new_center, outer, inner

################################################################################

def draw_point(draw, x, y, fill="green", r=80):
    leftUpPoint = (x-r, y-r)
    rightDownPoint = (x+r, y+r)
    twoPointList = [leftUpPoint, rightDownPoint]
    draw.ellipse(twoPointList, fill=fill)

def draw_arrow(draw, x, y, angle, fill):
    eqtri = math.pi/6
    p1 = x, y
    r = W/100
    p2 = x + r*math.cos(eqtri+angle), y + r*math.sin(eqtri+angle)
    p3 = x + r*math.cos(eqtri-angle), y - r*math.sin(eqtri-angle)

    draw.polygon((p1, p2, p3), fill=fill)

def draw_circle(draw, x, y, r, outline="red", fill=False):
    leftUpPoint = (x-r, y-r)
    rightDownPoint = (x+r, y+r)
    twoPointList = [leftUpPoint, rightDownPoint]
    bg = None
    if fill:
        bg = "black" if DARK else "white"
    draw.ellipse(twoPointList, outline=outline, fill=bg, width=THICKNESS)

def draw_loop(draw, pos, edges, state, p, outer, inner, fill):
    r = R_STATE
    x = p[0]
    y = p[1]
    
    out_edges, out_mid = get_outer_midpoints(outer, pos)

    if state in outer:
        r *= 1.25
        angle = get_angle(W/2, H/2, x, y)
        x = round(x + r*math.cos(angle))
        y = round(y + r*math.sin(angle))
        draw_circle(draw, x, y, r, outline=fill, fill=False)

        offset = math.pi - (math.pi/3.067)*(R_STATE/r)
        draw_arrow(draw, x+r*math.cos(angle+offset), y+r*math.sin(angle+offset), angle+0.96*offset-math.pi/2, fill)
    else:
        states = outer + inner
        counts = get_edge_count(states, edges, False, True)
        if counts[state] > 2:
            r *= 0.75

        el, closest_edge = get_closest(out_mid, x, y)

        for mid_point in closest_edge:
            src, dst = out_edges[out_mid.index(mid_point)]
            angle = get_angle(pos[src][0], pos[src][1], pos[dst][0], pos[dst][1]) - math.pi/2

        pos_outer = []
        for node in outer:
            pos_outer.append(pos[node])

        _, closest_node = get_closest(pos_outer, x, y)

        for p_out in closest_node:
            node = list(pos.keys())[list(pos.values()).index(p_out)]
            if ((state, node) not in edges) and ((node, state) not in edges):
                angle = get_angle(x, y, p_out[0], p_out[1])
                break

        if el - R_STATE < r:
            r = (el - R_STATE)

        x = round(x + r*math.cos(angle))
        y = round(y + r*math.sin(angle))
        
        draw_circle(draw, x, y, r, outline=fill, fill=False)
        offset = math.pi - (math.pi/3.067)*(R_STATE/r)
        draw_arrow(draw, x+r*math.cos(angle+offset), y+r*math.sin(angle+offset), angle+0.96*offset-math.pi/2, fill)


def draw_ray(draw, edge, fill):
    x1 = edge[0][0]
    y1 = edge[0][1]
    x2 = edge[1][0]
    y2 = edge[1][1]

    angle = get_angle(x2, y2, x1, y1)
    xoff = R_STATE*math.cos(angle)
    yoff = R_STATE*math.sin(angle)

    draw.line(((x1-xoff, y1-yoff), (x2+xoff, y2+yoff)), fill=fill, width=THICKNESS)
    draw_arrow(draw, x2+xoff, y2+yoff, angle, fill)

def draw_arc(draw, pos, states, edge, outer, inner, fill):
    points = {}
    scale = get_scale(states, edge, outer, inner)

    get_arc_points(points, edge, height=scale)

    indexes = list(points.keys())
    indexes.sort()

    prevx = edge[0][0]
    prevy = edge[0][1]

    endx1 = edge[0][0]
    endy1 = edge[0][1]
    endx2 = edge[1][0]
    endy2 = edge[1][1]

    for angle in indexes:
        x = points[angle][0]
        y = points[angle][1]

        c1 = in_circle(pos[states[0]], R_STATE, x, y)
        c2 = in_circle(pos[states[1]], R_STATE, x, y)
        if not c1 and not c2:
            if not c2:
                endx1 = x
                endy1 = y
            draw.line(((prevx, prevy), (x, y)), fill=fill, width=THICKNESS)
        
        prevx = x
        prevy = y
    
    x = edge[1][0]
    y = edge[1][1]
    draw.line(((prevx, prevy), (x, y)), fill=fill, width=THICKNESS)

    angle = get_angle(endx2, endy2, endx1, endy1)
    draw_arrow(draw, endx1, endy1, angle, fill)

def draw_edges(draw, pos, edges, outer, inner):
    color = "white" if DARK else "black"
    drawn = []
    
    for edge in edges:
        if edge[0] == edge[1]:
            draw_loop(draw, pos, edges, edge[0], edges[edge][0], outer, inner, color)
        elif edge not in drawn:
            drawn.append((edge[0], edge[1]))
            drawn.append((edge[1], edge[0]))
            draw_ray(draw, edges[edge], color)
        else:
            draw_arc(draw, pos, edge, edges[edge], outer, inner, color)

def draw_states(draw, pos):
    for state in pos:
        x = pos[state][0]
        y = pos[state][1]
        draw_circle(draw, x, y, R_STATE, fill=True)

def draw_text(draw, pos):
    color = "white" if DARK else "black"
    count = len(pos)

    states = list(pos.keys())
    longest, _ = get_longest(states)

    for state in pos:
        size = math.floor(10*R_STATE/4/longest)

        x = pos[state][0] - len(state)*size/3.5
        y = pos[state][1] - size/1.5

        fnt = ImageFont.truetype(HOME + "/sv2fsm/lib/monospace.ttf", size)

        draw.text((x, y), text=state, font=fnt, fill=color)

def drawer(states, filename, no_bg, dark, circular):
    global DARK
    DARK = dark
    scale_rstate()

    draw = None
    canvas = (W, H)

    background = "black" if DARK else "white"
    if no_bg:
        background = None            
    im = Image.new('RGBA', canvas, background)
    draw = ImageDraw.Draw(im)

    r_in = 0
    center = (0,0)
    outer = states
    inner = []

    planar = is_planar_graph(states)
    pos, edges, points = get_values(outer, inner)

    if planar and not circular:
        pos, edges, center, outer, inner = rearrange_states(pos, edges, points, states)
    elif not planar:
        print("Note: this graph is not planar, returning circular graph")

    # add the self loop edges back in
    edges.update(get_edges(outer + inner, pos, self_loops=True))

    if draw != None:
        draw_edges(draw, pos, edges, outer, inner)
        draw_states(draw, pos)
        draw_text(draw, pos)

    im.save(filename)