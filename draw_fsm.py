import math
from PIL import Image, ImageDraw, ImageFont

DARK = True
WHITE = (255,255,255,255)
BLACK = (0,0,0,255)
RED = (255,0,0,255)

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

    point = [x1+t*(x2-x1), y1+t*(y2-y1)]
 
    if (t > 0.001 and t < 0.999) and (u > 0.001 and u < 0.999):
        return (True, point)
    else:
        return (False, [])

################################################################################

def get_edges(states, w, h, greater_r):
    edges = []
    count = len(states)
    for i in range(count):
        state = states[i]
        filename = "tmp/" + state + ".sv"
        with open(filename, "r") as f:
            lines = f.readlines()

        degree = 2*i*math.pi/count
        x = w/2 + greater_r*math.cos(degree)
        y = h/2 + greater_r*math.sin(degree)

        for line in lines:
            tup = line.partition(", ")
            dst = tup[0]
            tran = tup[2]
            if dst != state:
                j = i
                while states[j%count] != dst: j += 1
                displace = j-i
                nx = w/2 + greater_r*math.cos(degree+2*displace*math.pi/count)
                ny = h/2 + greater_r*math.sin(degree+2*displace*math.pi/count)
                points = [(x, y), (nx, ny)]
                edges.append(points)
            # else:
            #     print("skipping same state transitions for now")

    return edges

################################################################################

def draw_point(draw, x, y):
    r = 80
    leftUpPoint = (x-r, y-r)
    rightDownPoint = (x+r, y+r)
    twoPointList = [leftUpPoint, rightDownPoint]
    color = WHITE if DARK else BLACK
    draw.ellipse(twoPointList, fill=color)

def draw_circle(draw, x, y, r):
    leftUpPoint = (x-r, y-r)
    rightDownPoint = (x+r, y+r)
    twoPointList = [leftUpPoint, rightDownPoint]
    draw.ellipse(twoPointList, fill=(255,0,0,255))

def draw_edges(draw, edges):
    points = []
    for i in range(len(edges)):
        found = False
        for j in range(len(edges)):
            found, point = get_intersection(edges[i], edges[j])
            if found:
                points.append(point)
                break
    
        color = RED if found else (WHITE if DARK else BLACK)
        draw.line(edges[i], fill=color,width=10)

    return points

def draw_states(draw, w, h, r, states):
    count = len(states)
    for i in range(count):
        state = states[i]
        degree = 2*i*math.pi/count
        x = w/2 + r*math.cos(degree)
        y = h/2 + r*math.sin(degree)

        draw_circle(draw, x, y, r/5)

def draw_text(draw, w, h, r, states):
    count = len(states)

    longest = 0
    for state in states:
        if len(state) > longest:
            longest = len(state)

    for i in range(count):
        state = states[i]
        degree = 2*i*math.pi/count
        size = math.floor(r/2/longest)

        x = w/2 + r*math.cos(degree) - len(state)*size/3.5
        y = h/2 + r*math.sin(degree) - size/1.5

        fnt = ImageFont.truetype("lib/monospace.ttf", size)
        color = WHITE # BLACK if DARK else WHITE

        draw.text((x, y), text=state, font=fnt, fill=color)

def draw_fsm(draw, w, h, states, filename):
    r = w/3
    count = len(states)

    edges = get_edges(states, w, h, r)
    points = draw_edges(draw, edges)

    draw_states(draw, w, h, r, states)
    draw_text(draw, w, h, r, states)

    for x, y in points:
        draw_point(draw, x, y)

def drawer(states, filename):
    w = 8000
    h = 8000
    canvas = (w, h)

    scale = 5
    thumb = canvas[0]/scale, canvas[1]/scale

    background = BLACK if DARK else WHITE
    im = Image.new('RGBA', canvas, background)
    draw = ImageDraw.Draw(im)

    draw_fsm(draw, w, h, states, filename)

    # make thumbnail
    im.thumbnail(thumb)

    # save image
    im.save(filename)