import argparse
import draw_fsm
import os
import sv_parser as svp
import shutil
import time

def setup():
    if os.path.isdir(os.getcwd() + "/tmp"):
        shutil.rmtree("tmp")

    os.mkdir("tmp/")

def cleanup():
    if os.path.isdir(os.getcwd() + "/tmp"):
        shutil.rmtree("tmp")

def run(path):
    start = time.time()
    # make sure file exists
    if not os.path.exists(path):
        print("ERROR: this file does not exist in the directory you are calling it from")

    setup()

    # strip file of comments for performance
    svp.strip_comments(path)

    # parse out all the always_comb blocks
    working = "tmp/" + FILENAME
    count = svp.parse_always_combs(working)

    # get state names and variable names
    states, state_vars = svp.get_states(working)

    # define name for current and next states
    cs, ns = svp.get_vars(count, state_vars)

    # create formatted file for each state containing state transtions
    svp.get_state_blocks(ns, states)

    # get transitions from every state and save it in a file
    for state in states:
            transitions = svp.get_transitions(state, ns)
            svp.save_transitions(state, cs, transitions)

    draw_fsm.drawer(states, "out/" + FILENAME[:-3] + '.png', IMAGE, CIRCULAR)

    print("finished", path, ": it took", time.time()-start, "secs")
    cleanup()

# get file name
parser = argparse.ArgumentParser(description='sv2fsm: automatically generates a FSM diagram from SystemVerilog code.')
parser.add_argument('--test', nargs='?', type=int, const=-1, default=-2, help='this will run script on all test files.')
parser.add_argument('--filename', type=str, default = "", help='this is the file you want to create a FSM from.')
parser.add_argument('--image', nargs='?', type=bool, const=True, default=False, help='this determines whether or not you generate an image.')
parser.add_argument('--circular', nargs='?', type=bool, const=True, default=False, help='this generates a circular graph (may have crossing), instead of the default planar (no line crossings).')
args = parser.parse_args()

TEST = args.test
FILENAME = args.filename
IMAGE = args.image
CIRCULAR = args.circular

PATH = FILENAME

if TEST == -2:
    run(FILENAME)
if TEST == -1:
    i = 0
    FILENAME = "test"+str(i)+".sv"
    while os.path.exists("test/" + FILENAME):
        i += 1
        if (i == 13) or (i == 9) or (i == 8):
            continue
        run("test/" + FILENAME)
        FILENAME = "test"+str(i)+".sv"
else:
    FILENAME = "test"+str(TEST)+".sv"
    run("test/" + FILENAME)