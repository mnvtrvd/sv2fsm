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

    draw_fsm.drawer(states, "out/" + FILENAME[:-3] + '.png', NO_BG, DARK, CIRCULAR, not NO_IMG)

    print("finished", path, ": it took", round(time.time()-start, 2), "secs")
    cleanup()

# get file name
parser = argparse.ArgumentParser(description='sv2fsm: automatically generates a FSM diagram from SystemVerilog code.')
parser.add_argument('--filename', type=str, default = "", help='this is the file you want to create a FSM from.')
parser.add_argument('--no_bg', nargs='?', type=bool, const=True, default=False, help='this will output a image with no background (useful for papers).')
parser.add_argument('--dark', nargs='?', type=bool, const=True, default=False, help='this will output a dark-mode image.')
parser.add_argument('--circle', nargs='?', type=bool, const=True, default=False, help='this generates a basic circular non-planar graph.')

# testing args
parser.add_argument('--test', nargs='?', type=int, const=-1, default=-2, help='this will run script on test files (add arg for specific).')
parser.add_argument('--stress', nargs='?', type=int, const=10, default=1, help='this will run the given file(s) many times.')
parser.add_argument('--no_img', nargs='?', type=bool, const=True, default=False, help='this will not generate an image for debugging purposes.')

args = parser.parse_args()

TEST = args.test
STRESS = args.stress
FILENAME = args.filename
NO_IMG = args.no_img
NO_BG = args.no_bg
DARK = args.dark
CIRCULAR = args.circle

for i in range(STRESS):
    NO_IMG = False
    if i == STRESS - 1:
        NO_IMG = args.no_img

    FILENAME = args.filename
    PATH = FILENAME

    if TEST == -2:
        run(FILENAME)
    if TEST == -1:
        i = 0
        FILENAME = "test"+str(i)+".sv"
        while os.path.exists("test/" + FILENAME):
            i += 1
            run("test/" + FILENAME)
            FILENAME = "test"+str(i)+".sv"
    else:
        FILENAME = "test"+str(TEST)+".sv"
        run("test/" + FILENAME)