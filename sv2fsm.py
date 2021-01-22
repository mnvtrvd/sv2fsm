import argparse
import math
import os
import shutil
from PIL import Image, ImageDraw, ImageFont

''' steps

use argparse to take in file
be able to parse file and get enum
-get states, and variable names for cs and ns
be able to parse file and get always_comb begin .... 
'''

# get file name
parser = argparse.ArgumentParser(description='sv2fsm: automatically generates a FSM diagram from SystemVerilog code.')
parser.add_argument('--filename', type=str, help='this is the file you want to create a FSM from.')
parser.add_argument('--image', nargs='?', type=bool, const=True, default=False, help='this determines whether or not you generate an image.')
args = parser.parse_args()

FILENAME = args.filename
IMAGE = args.image
TMP = "tmp/"
WOC = TMP + "woc_" + FILENAME
ALWAYS = TMP + "always_comb"
SV = ".sv"

def setup():
    if os.path.isdir(os.getcwd() + "/tmp"):
        cleanup()

    os.mkdir(TMP)

def cleanup():
    if os.path.isdir(os.getcwd() + "/tmp"):
        shutil.rmtree("tmp")

################################################################################

def get_depth(line):
    tabs = 0
    for c in line:
        if c == "\t":
            tabs += 1
        else:
            break
    
    return tabs

def get_equiv_parens(line):
    equiv = ""

    for c in line:
        if (c == "(") or (c == ")"):
            equiv = equiv + c

    return equiv    

def rem_parens(line):
    equiv = get_equiv_parens(line)
    if len(equiv)%2 == 1:
        print("parens don't match at start")
    spl = equiv.partition("(())")

    while spl[1] != "":
        nline = ""
        count = 0
        for c in line:
            if (c == "(") or (c == ")"):
                count += 1
                if (count == len(spl[0]) + 1) or (count == len(spl[0] + spl[1])):
                    continue
                else:
                    nline = nline + c
            else:
                nline = nline + c

        line = nline
        equiv = get_equiv_parens(line)
        if len(equiv)%2 == 1:
            print("parens don't match")
        spl = equiv.partition("(())")
    
    return line

################################################################################

def rem_comments(line, multiline):
    if line == "":
        return (line, multiline)

    if multiline: # if currently in multiline comment
        end = line.partition("*/")
        if end[1] != "": # found the end
            return rem_comments(end[2], False)
        else: # still in multiline comment
            return ("", True)
    else: # not in multiline comment
        start = line.partition("/*")
        if start[1] != "": # found a new multiline comment
            end = start[2].partition("*/")
            if end[1] != "": # multiline comment ends in this line
                research = rem_comments(end[2], False)
                return (start[0] + research[0], research[1])
            else: # start to new multiline comment block
                return (start[0], True)
        else: # no multiline comment
            start = line.partition("//")
            if start[1] != "": # found a new single line comment
                return (start[0] + "\n", False) # return line left of comment and newline
            else:
                return (line, False) # return original line

def commentless_file(filename):
    with open(FILENAME, "r") as f:
        lines = f.readlines()

    with open(WOC, "w") as f:
        multiline = False
        for line in lines:
            commentless_line, multiline = rem_comments(line, multiline)
            f.write(commentless_line)

################################################################################

def get_states(lines):
    enum = ""
    found = False

    # get state names and variable names
    for line in lines:
        if found:
            enum = enum + line.strip()
            if ";" in line:
                break
        elif "enum " in line:
            enum = line.strip()
            found = True
            if ";" in line:
                break

    tmp = enum.partition("{")[2].partition("}")
    states = tmp[0].replace(" ", "").split(",")
    state_vars = tmp[2].replace(";", "").replace(" ", "").split(",")

    return (states, state_vars)

def get_always_combs(lines):
    comb = ""
    parens = 0
    count = 0

    for line in lines:
        if (comb == "") and ("always_comb" in line):
            comb = line

        if comb != "":
            if "begin" in line:
                parens += 1
            if ("end" in line) and not ("endcase" in line):
                parens -= 1

            if comb != line:
                comb = comb + line

            if parens == 0:
                with open(ALWAYS + str(count) + SV, "w") as f:
                    f.write(comb)
                count += 1
                comb = ""
    
    return count

def get_vars(count):
    cs = ""
    ns = ""
    for i in range(count):
        with open(ALWAYS + str(i) + SV) as f:
            lines = f.readlines()

            for line in lines:
                if "case" in line:
                    cond = line.partition("(")[2].partition(")")[0]
                    if cond in state_vars:
                        cs = cond
                    break
        
        if cs != "":
            for var in state_vars:
                if var != cs:
                    ns = var
                    break
            break
    
    return (cs, ns)

# figures out which always_comb block indicates state transitions
def get_stf(count, ns):
    for i in range(count):
        with open(ALWAYS + str(i) + SV) as f:
            lines = f.readlines()

            for line in lines:
                if ns in line:
                    return i
                    break

def format_states(states):
    for state in states:
        if not os.path.exists(TMP + state + SV):
            print(TMP + state + SV + " does not exist")
            break

        with open(TMP + state + SV, "r") as f:
            lines = f.readlines()
        
        os.remove(TMP + state + SV)
        with open(TMP + state + SV, "w") as f:
            for i, line in enumerate(lines):
                if i == 0:
                    continue
                blocks = line.partition("begin")
                for block in blocks:
                    if block.rstrip() != "":
                        f.write(block.rstrip()+"\n")

        with open(TMP + state + SV, "r") as f:
            lines = f.readlines()

        with open(TMP + state + SV, "w") as f:
            parens = 0
            for line in lines:
                if "begin" in line:
                    parens += 1
                elif "end" in line:
                    parens -= 1
                else:
                    f.write("\t"*parens + line)

def get_state_blocks(states, lines):
    block = ""
    parens = 0
    cs = ""

    for line in lines:
        if block == "":
            for state in states:
                if state in line:
                    cs = state
                    block = line.lstrip()

        if block != "":
            if "begin" in line:
                parens += 1
            if "end" in line:
                parens -= 1

            if parens == 0:
                with open(TMP + cs + SV, "w") as f:
                    f.write(block)
                block = ""
                cs = ""
            elif block != line.lstrip():
                block = block + line.lstrip()

    format_states(states)

################################################################################

def get_condition(index, lines):
    cond = ""
    parens = 0
    found = False
    while (index < len(lines)) and (parens != 0 or not found):
        line = lines[index].strip()
        for c in line:
            if c == "(":
                if not found:
                    found = True
                parens += 1
            elif c == ")":
                parens -= 1

            if found:
                if parens == 0:
                    break
                else:
                    cond += c

        index += 1
    
    return (cond[1:], index)

def get_next_state(index, lines):
    next_state = lines[index].partition("=")[2].strip()
    if next_state.partition(";")[1] != "":
        next_state = next_state.partition(";")[0]
        index += 1
    else:
        found = False
        index += 1
        while (index < len(lines)) and not found:
            line = lines[index]
            if line.partition(";")[1] != "":
                next_state = next_state + line.partition(";")[0].strip()
                break
            index += 1
    
    return (next_state.strip(), index)

def format_transition(cond_layer, transition):
    tran_layer = ""
    if cond_layer[-1] == "": # in else case
        for condition in cond_layer[:-1]:
            if tran_layer == "":
                tran_layer = "(" + condition + ")"
            else:
                tran_layer = tran_layer + " || (" + condition + ")"
        
        tran_layer = "!(" + tran_layer + ")"
    elif len(cond_layer) > 1: # in else if case
        for condition in cond_layer[:-1]:
            if tran_layer == "":
                tran_layer = "(" + condition + ")"
            else:
                tran_layer = tran_layer + " || (" + condition + ")"
        
        tran_layer = "!(" + tran_layer + ") && (" + cond_layer[-1] + ")"
    else: # in if case
        tran_layer = cond_layer[0]
    
    if transition == "":
        return rem_parens("(" + tran_layer + ")")
    else:
        return rem_parens(transition + " && (" +  tran_layer + ")")

def get_transitions(state, ns):
    with open(TMP + state + SV, "r") as f:
        lines = f.readlines()

    conditions = []
    transitions = []
    i = 0
    while i < len(lines):
        d = get_depth(lines[i])

        if "else if" in lines[i]:
            cond, i = get_condition(i, lines)
            if d < len(conditions): # reaching else if on this level after if
                conditions[d].append(cond)
            else: # reaching else if before if condition
                print("should not get here")

        elif "if" in lines[i]:
            cond, i = get_condition(i, lines)
            if d < len(conditions): # reaching if on this level again, overwrite
                conditions[d] = [cond]
            else: # reaching if on this level for the first time
                conditions.append([cond])

        elif "else" in lines[i]:
            cond, i = "", i+1
            if d < len(conditions): # reaching else on this level after if
                conditions[d].append(cond)
            else: # reaching else before if condition
                print("should not get here")

        elif ns in lines[i]:
            transition = ""
            for layer in range(d):
                transition = format_transition(conditions[layer], transition)
            
            next_state, i = get_next_state(i, lines)
            transitions.append((next_state,transition))
        else:
            i += 1
    
    return transitions

def save_transitions(state, cs, transitions):
    with open(TMP + "_" + state + SV, "w") as f:
        needs_else = True
        for t in transitions:

            if cs == t[0]:
                t = (state, t[1])
                needs_else = False
            
            if t[1] == "":
                needs_else = False

            f.write(str(t) + "\n")

        if needs_else:
            if len(transitions) > 1:
                else_case = (state, "otherwise")
            else:
                new_trans = rem_parens("!(" + transitions[0][1] + ")")
                else_case = (state, new_trans)
            f.write(str(else_case) + "\n")

################################################################################

def draw_circle(draw, x, y, r):
    leftUpPoint = (x-r, y-r)
    rightDownPoint = (x+r, y+r)
    twoPointList = [leftUpPoint, rightDownPoint]
    draw.ellipse(twoPointList, fill=(255,0,0,255))

def drawPics(states):
    # size of image
    w = 20000
    h = 20000
    canvas = (w, h)
    states = states[:-1]

    # scale ration
    scale = 5
    thumb = canvas[0]/scale, canvas[1]/scale

    # init canvas
    im = Image.new('RGBA', canvas, (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)

    degree = 0.0
    greater_r = w/3
    lesser_r = greater_r/4
    count = len(states)

    longest = 0
    for state in states:
        if len(state) > longest:
            longest = len(state)

    for i in range(count):
        state = states[i]
        with open(TMP+"_"+state+SV, "r") as f:
            lines = f.readlines()

        x = w/2 + greater_r*math.cos(degree)
        y = h/2 + greater_r*math.sin(degree)

        for line in lines:
            tup = line.partition(",")
            dst = tup[0].partition("'")[2].partition("'")[0]
            if dst == state:
                print("skipping same state transitions for now")
            else:
                j = i
                while states[j%count] != dst:
                    j += 1
                displace = j-i
                nx = w/2 + greater_r*math.cos(degree+2*displace*math.pi/count)
                ny = h/2 + greater_r*math.sin(degree+2*displace*math.pi/count)
                draw.line([(x, y), (nx, ny)], fill=(0,0,0,255),width=10)
        
        degree += 2*math.pi/count

    for i in range(count):
        state = states[i]
        x = w/2 + greater_r*math.cos(degree)
        y = h/2 + greater_r*math.sin(degree)

        draw_circle(draw, x, y, lesser_r)
        size = math.floor(2*lesser_r/longest)
        fnt = ImageFont.truetype("monospace.ttf", size)

        draw.text((x-len(state)*size/3.5, y-size/1.5), text=state, font=fnt, fill=(255,255,255,255), align="center")
        degree += 2*math.pi/count

    # make thumbnail
    im.thumbnail(thumb)

    # save image
    im.save('im.png')

################################################################################

# make sure file exists
if not os.path.exists(FILENAME):
    print("this file does not exist in the directory you are calling it from")

setup()

# strip file of comments for performance
commentless_file(FILENAME)

# get lines in file
with open(WOC, "r") as f:
    lines = f.readlines()

# get state names and variable names
states, state_vars = get_states(lines)
states.append("default")
print(states)

# get always_comb blocks
count = get_always_combs(lines)

# define name for current and next states
cs, ns = get_vars(count)

# determine which always_comb block has state transitions
stf = get_stf(count, ns)

print((cs, ns, stf))

with open(ALWAYS + str(stf) + SV, "r") as f:
    lines = f.readlines()

# create formatted file for each state containing state transtions
get_state_blocks(states, lines)

# get transitions from every state and save it in a file
for state in states:
    if state != "default":
        transitions = get_transitions(state, ns)
        save_transitions(state, cs, transitions)

if IMAGE:
    drawPics(states)

# cleanup()