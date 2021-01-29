import argparse
import os
import sv_parser as svp
import shutil
import time
from draw_fsm import drawer
from pathlib import Path

HOME = str(Path.home())

def setup():
    CUR_DIR = os.getcwd()
    ENC_DIR = CUR_DIR.split("/")[-1]
    if ENC_DIR != "sv2fsm":
        print("WARNING: seems like you have already run this script since enclosing folder is not /sv2fsm")
    elif CUR_DIR != HOME + '/sv2fsm':
        shutil.move(CUR_DIR, HOME)
        print("/sv2fsm has been moved to ~/sv2fsm\n")

def cleanup(terminate=True):
    # delete tmp directory
    if os.path.isdir(os.getcwd() + "/tmp"):
        shutil.rmtree("tmp")

    if terminate:
        exit()

# get file name
parser = argparse.ArgumentParser(description='sv2fsm: automatically generates a FSM diagram from SystemVerilog code.')
parser.add_argument('--setup', nargs='?', type=bool, const=True, default=False, help='this will allow sv2fsm to be accessed from anywhere.')
parser.add_argument('--filename', type=str, default = "", help='this is the file you want to create a FSM from.')
parser.add_argument('--no_bg', nargs='?', type=bool, const=True, default=False, help='this will output a image with no background (useful for papers).')
parser.add_argument('--dark', nargs='?', type=bool, const=True, default=False, help='this will output a dark-mode image.')
parser.add_argument('--circle', nargs='?', type=bool, const=True, default=False, help='this generates a basic circular non-planar graph.')

args = parser.parse_args()

path = args.filename
filename = path.split("/")[-1]

start = time.time()

if args.setup:
    setup()
    cleanup()

if not os.path.exists(HOME + "/sv2fsm/lib/monospace.ttf"):
    print("ERROR: are you sure you have run the --setup already?")
    cleanup()

# make sure file exists
if not os.path.exists(path):
    print("ERROR: this file does not exist in the directory you are calling it from")
    cleanup()

# delete tmp directory if it already exists
cleanup(False)

os.mkdir("tmp/")

# strip file of comments for performance
svp.strip_comments(path)

# parse out all the always_comb blocks
working = "tmp/" + filename
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

drawer(states, filename[:-3] + '.png', args.no_bg, args.dark, args.circle)

# delete tmp directory
cleanup(False)

print("finished", path, ": it took", round(time.time()-start, 2), "secs")