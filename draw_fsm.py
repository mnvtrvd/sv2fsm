import math
import matplotlib.pyplot as plt
import networkx as nx
import random
import time
from PIL import Image, ImageDraw, ImageFont, ImageOps

DARK = True
WHITE = (255,255,255,255)
BLACK = (0,0,0,255)
RED = (255,0,0,255)
GREEN = (0,255,0,255)
BLUE = (0,0,255,255)

W = 8000
H = 8000

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
    x = (x2-x1)/2
    y = (y2-y1)/2
    return x, y

def get_longest(states):
    length = 0
    longest = ""
    for state in states:
        if len(state) > length:
            length = len(state)
            longest = state
    
    return length, longest

def get_slope(edge):
    x1 = edge[0][0]
    y1 = edge[0][1]
    x2 = edge[1][0]
    y2 = edge[1][1]

    return (y2-y1)/(x2-x1)

def get_angle(x1, y1, x2, y2):
    delta = math.atan2(y2, x2) - math.atan2(y1, x1)

    while (delta > math.pi) or (delta < -math.pi):
        if (delta < -math.pi):
            delta += 2*math.pi
        else:    
            delta -= 2*math.pi

    return delta

# https://www.eecs.umich.edu/courses/eecs380/HANDOUTS/PROJ2/InsidePoly.html#:~:text=To%20determine%20the%20status%20of,point%20is%20outside%20the%20polygon.
def in_face(face, pos, state):
    angle = 0
    count = len(face)

    for i in range(count):
        x1 = pos[face[i]][0] - pos[state][0]
        y1 = pos[face[i]][1] - pos[state][1]
        x2 = pos[face[(i+1)%count]][0] - pos[state][0]
        y2 = pos[face[(i+1)%count]][1] - pos[state][1]
        angle += get_angle(x1, y1, x2, y2)
    
    return abs(angle) >= math.pi

################################################################################

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
        degree = 2*i*math.pi/count + offset
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

def get_edges(states, pos, digraph=False):
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
            if digraph or (dst != state):
                if (state in pos) and (dst in pos):
                    edges[(state, dst)] = (pos[state], pos[dst])
            # else:
            #     print("skipping same state transitions for now")

    return edges

def get_edge_count(states, edges, include_self_loops=True):
    undirected = []

    for edge in edges:
        var0 = edge[0] + ":" + edge[1]
        var1 = edge[1] + ":" + edge[0]

        if (var0 not in undirected) and (var1 not in undirected):
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

def get_values(outer, inner, r, center=(W,H), offset=0, r_in=0, skip=False):
    states = outer + inner
    pos = get_xy(r, outer)
    if skip:
        for istate in inner:
            pos[istate] = (round(W/2), round(H/2))
    else:
        while 2**r_in < len(inner):
            r_in += 1
        pos.update(get_xy(r_in, inner, center[0], center[1], offset))
    edges = get_edges(states, pos)
    points = get_points(edges)
    return pos, edges, points

def get_faces(target, trans, outer):
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
            i = random.randrange(len(valid))
            path = [list(valid)[i]]
            visited = []
        else:
            start = path[0]
            curr = path[-1]
            if (len(path) > 2) and (start in trans[curr]):
                valid = set(trans) & set(outer)
                if (target == 1) or not all(face in path for face in valid):
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

################################################################################

def move_inwards(r, pos, edges, points, outer, inner):
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
        pos, edges, points = get_values(outer, inner, r, skip=True)

        if time.time() - start > 10:
            print("WARNING: exceeded maximum runtime of 10 secs")
            break
    
    return get_values(outer, inner, r)

def decrowd(r, outer, inner):
    if len(outer) < len(inner):
        _, _, points = get_values(inner, outer, r)
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

    return get_values(outer, inner, r)

def recenter_inner(r, pos, edges, outer, inner):
    trans = get_transitions(edges, outer)
    chains = rem_chains(trans)

    v = len(trans)
    e  = 0
    for tran in trans:
        e += len(trans[tran])

    # based off euler's formula v - e + f = 2
    f = 2 + round(e/2) - v
    faces = get_faces(f-1, trans, outer)

    # for face in faces:
    #     for node in inner:
    #         if in_face(face, pos, node):
    #             centroids.append(get_centroid(face, pos))

    # simpler method of just placing all the inner nodes in the largest face
    new_center = (W, H)
    if len(faces) > 0:
        _, face = get_longest(faces)
        new_center = get_centroid(face, pos)

    pface = []
    for state in face:
        pface.append(pos[state])

    pos, edges, points = get_values(outer, inner, r, new_center)
    return pos, edges, points, new_center

def rotate_inner(r, new_center, outer, inner):
    best = 0
    _, edges, points = get_values(outer, inner, r, new_center, best)
    if len(inner) > 1:
        edge_sum = get_edge_len(edges, outer)
        intersections = len(points)
        for offset in range(1, 360, 1):
            _, edges, points = get_values(outer, inner, r, new_center, offset)
            if len(points) <= intersections:
                edge_len = get_edge_len(edges, outer)
                if (len(points) < intersections) or (edge_len < edge_sum):
                    best = offset
                    edge_sum = edge_len
                    intersections = len(points)

    pos, edges, points = get_values(outer, inner, r, new_center, best)
    return pos, edges, points, best

def resize_inner(r_out, new_center, offset, outer, inner):
    r_in = 0
    pos, edge, points = get_values(outer, inner, r_out, new_center, offset)

    if len(inner) > 1:
        while 2**r_in < len(inner):
            r_in += 1
        
        intersections = len(points)
        while len(points) <= intersections:
            r_in += 1
            pos, edge, points = get_values(outer, inner, r_out, new_center, offset, r_in)

        r_in -= 1
        pos, edge, points = get_values(outer, inner, r_out, new_center, offset, round(r_in/2))
        
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

        if time.time() - start > 10:
            print("ERROR: exceeded maximum runtime of 10 secs")
            break
    
    return pos, edges, points

def rearrange_states(r, pos, edges, points, states):
    outer = states
    inner = []
    faces = []

    pos, edges, points = move_inwards(r, pos, edges, points, outer, inner)
    # if len(points) > 0: print("step1:", points)
    pos, edges, points = decrowd(r, outer, inner)
    # if len(points) > 0: print("step2:", points)
    pos, edges, points, new_center = recenter_inner(r, pos, edges, outer, inner)
    # if len(points) > 0: print("step3:", points)
    pos, edges, points, offset = rotate_inner(r, new_center, outer, inner)
    # if len(points) > 0: print("step4:", points)
    pos, edges, points, r_in = resize_inner(r, new_center, offset, outer, inner)
    # if len(points) > 0: print("step5:", points)
    pos, edges, points = swap_inwards(pos, edges, points, outer, inner)
    if len(points) > 0: print("step6:", points)

    return pos, edges, points

################################################################################

def draw_point(draw, x, y, fill=GREEN):
    r = 80
    leftUpPoint = (x-r, y-r)
    rightDownPoint = (x+r, y+r)
    twoPointList = [leftUpPoint, rightDownPoint]
    # color = GREEN # WHITE if DARK else BLACK
    draw.ellipse(twoPointList, fill=fill)

def draw_circle(draw, x, y, r):
    leftUpPoint = (x-r, y-r)
    rightDownPoint = (x+r, y+r)
    twoPointList = [leftUpPoint, rightDownPoint]
    draw.ellipse(twoPointList, fill=(255,0,0,255))

def draw_edges(draw, edges):
    for edge in edges:
        color = WHITE if DARK else BLACK
        draw.line(edges[edge], fill=color, width=10)

def draw_states(draw, r, pos):
    for state in pos:
        x = pos[state][0]
        y = pos[state][1]
        draw_circle(draw, x, y, r/5)

def draw_text(draw, r, pos):
    count = len(pos)

    states = list(pos.keys())
    longest, _ = get_longest(states)

    for state in pos:
        size = math.floor(r/2/longest)

        x = pos[state][0] - len(state)*size/3.5
        y = pos[state][1] - size/1.5

        fnt = ImageFont.truetype("lib/monospace.ttf", size)
        color = WHITE # BLACK if DARK else WHITE

        draw.text((x, y), text=state, font=fnt, fill=color)

def draw_fsm(draw, states, circular=False):
    r = W/3

    planar = is_planar_graph(states)
    pos = get_xy(r, states)
    edges = get_edges(states, pos)
    points = get_points(edges)

    if (len(points) != 0) and planar and not circular:
        pos, edges, points = rearrange_states(r, pos, edges, points, states)

    if draw != None:
        draw_edges(draw, edges)
        draw_states(draw, r/2, pos)
        draw_text(draw, r/2, pos)
        for point in points:
            draw_point(draw, point[0], point[1])

def drawer(states, filename, gen_im=True, circular=False):
    draw = None
    if gen_im:
        canvas = (W, H)

        scale = 5
        thumb = canvas[0]/scale, canvas[1]/scale

        background = BLACK if DARK else WHITE
        im = Image.new('RGBA', canvas, background)
        draw = ImageDraw.Draw(im)

    draw_fsm(draw, states, circular)

    if gen_im:
        im.thumbnail(thumb)
        im.save(filename)