import argparse
import os
import shutil

''' steps

use argparse to take in file
be able to parse file and get enum
-get states, and variable names for cs and ns
be able to parse file and get always_comb begin .... 
'''

# get file name
parser = argparse.ArgumentParser(description='sv2fsm: automatically generates a FSM diagram from SystemVerilog code.')
parser.add_argument('--filename', type=str, help='this is the file you want to create a FSM from.')
args = parser.parse_args()

FILENAME = args.filename
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

def get_state_blocks(states, lines):
    block = ""
    parens = 0
    cs = ""

    for line in lines:
        if block == "":
            for state in states:
                if state in line:
                    cs = state
                    block = line

        if block != "":
            if "begin" in line:
                parens += 1
            if "end" in line:
                parens -= 1

            if block != line:
                block = block + line

            if parens == 0:
                with open(TMP + cs + SV, "w") as f:
                    f.write(block)
                block = ""
                cs = ""

def get_condition(index, lines):
    cond = ""
    parens = 0
    found = False
    while parens != 0 or not found:
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
    
    return cond[1:]


# def get_transition(ns, line):
    # print(ns)

def get_transitions(state, ns):
    with open(TMP + state + SV, "r") as f:
        lines = f.readlines()


    for i, line in enumerate(lines):
        if "if" in line:
            cond = get_condition(i, lines)
            # get_transition(ns, line)


################################################################################

# make sure file exists
if not os.path.exists(FILENAME):
    print("this file does not exist in the directory you are calling it from")

# setup()

# strip file of comments for performance
commentless_file(FILENAME)

# get lines in file
with open(WOC, "r") as f:
    lines = f.readlines()

# get state names and variable names
states, state_vars = get_states(lines)
states.append("default")
# print(states)

# get always comb blocks
count = get_always_combs(lines)

# define name for current and next states
cs, ns = get_vars(count)
# print(cs)
# print(ns)

stf = get_stf(count, ns)
# print(stf)

with open(ALWAYS + str(stf) + SV, "r") as f:
    lines = f.readlines()

# get_state_blocks(states, lines)

get_transitions("IGNORE1", ns)

# cleanup()