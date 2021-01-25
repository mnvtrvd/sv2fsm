import argparse
import draw_fsm
import os
import sv_parser as svp
import shutil

def setup():
    if os.path.isdir(os.getcwd() + "/tmp"):
        shutil.rmtree("tmp")

    os.mkdir("tmp/")

def cleanup():
    if os.path.isdir(os.getcwd() + "/tmp"):
        shutil.rmtree("tmp")

def run(path):
    # make sure file exists
    if not os.path.exists(path):
        print("ERROR: this file does not exist in the directory you are calling it from")

    setup()
    print("starting " + path)

    # strip file of comments for performance
    svp.strip_comments(path)
    # print("finished stripping comments")

    # parse out all the always_comb blocks
    working = "tmp/" + FILENAME
    count = svp.parse_always_combs(working)
    # print("finished parsing always_comb blocks")

    # get state names and variable names
    states, state_vars = svp.get_states(working)
    # print("finished getting states: " + str(states))

    # define name for current and next states
    cs, ns = svp.get_vars(count, state_vars)
    # print("finished getting vars: " + cs + ", " + ns)

    # create formatted file for each state containing state transtions
    svp.get_state_blocks(ns, states)
    # print("finished getting state blocks")

    # get transitions from every state and save it in a file
    for state in states:
            transitions = svp.get_transitions(state, ns)
            svp.save_transitions(state, cs, transitions)
            # print("finished getting transitions for " + state)

    draw_fsm.drawer(states, "out/" + FILENAME[:-3] + '.png', IMAGE)

    if IMAGE:
        # draw_fsm.graph_fsm(states, "out/" + FILENAME[:-3] + ".png")
        print("finished creating image")
    
    # print("finished " + path)
    cleanup()

# get file name
parser = argparse.ArgumentParser(description='sv2fsm: automatically generates a FSM diagram from SystemVerilog code.')
parser.add_argument('--test', nargs='?', type=int, const=-1, default=-2, help='this will run script on all test files.')
parser.add_argument('--filename', type=str, default = "", help='this is the file you want to create a FSM from.')
parser.add_argument('--image', nargs='?', type=bool, const=True, default=False, help='this determines whether or not you generate an image.')
args = parser.parse_args()

TEST = args.test
FILENAME = args.filename
IMAGE = args.image

PATH = FILENAME

if TEST == -2:
    run(FILENAME)
if TEST == -1:
    i = 0
    FILENAME = "test"+str(i)+".sv"
    while os.path.exists("test/" + FILENAME):
        if (i == 13) or (i == 9) or (i == 8):
            i += 1
            continue
        run("test/" + FILENAME)
        FILENAME = "test"+str(i)+".sv"
        i += 1
else:
    FILENAME = "test"+str(TEST)+".sv"
    run("test/" + FILENAME)

'''
if edges intersect:
    get edges that intersect
    get all parent nodes for edges
    get the node with fewest edges
    move that node towards the other node with which it has a connecting edge until that edge no longer intersects
    if new intersection:
        repeat with new edges, node (but not one you already moved)

'''