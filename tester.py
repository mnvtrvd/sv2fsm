import argparse
import os
import subprocess

# get file name
parser = argparse.ArgumentParser(description='sv2fsm_tester: automatically generates a FSM diagram from SystemVerilog code.')
parser.add_argument('--no_bg', nargs='?', type=bool, const=True, default=False, help='this will output a image with no background (useful for papers).')
parser.add_argument('--dark', nargs='?', type=bool, const=True, default=False, help='this will output a dark-mode image.')
parser.add_argument('--circle', nargs='?', type=bool, const=True, default=False, help='this generates a basic circular non-planar graph.')

# testing args
parser.add_argument('--test', nargs='?', type=int, const=-1, default=-2, help='this will run script on test files (add arg for specific).')
parser.add_argument('--stress', nargs='?', type=int, const=10, default=1, help='this will run the given file(s) many times.')
parser.add_argument('--clean', nargs='?', type=bool, const=True, default=False, help='this deletes all the testX.png files in the working directory.')

args = parser.parse_args()

if args.clean:
    count = 0
    filename = "test/test"+str(count)+".sv"
    while os.path.exists(filename):
        count += 1
        filename = "test/test"+str(count)+".sv"
    
    for i in range(count):
        filename = "test"+str(i)+".png"
        if os.path.exists(filename):
            os.remove(filename)
    
    exit()

flags = "python3 sv2fsm.py "
if args.no_bg:
    flags = flags + "--no_bg "
if args.dark:
    flags = flags + "--dark "
if args.circle:
    flags = flags + "--circle "

flags = flags + "--filename "

for i in range(args.stress):
    if args.test == -2:
        print("add the --test flag to test everything")
        break
    elif args.test == -1:
        i = 0
        filename = "test/test"+str(i)+".sv"
        while os.path.exists(filename):
            command = flags + filename
            subprocess.call(command, shell=True)

            i += 1
            filename = "test/test"+str(i)+".sv"
    else:
        filename = "test/test"+str(args.test)+".sv"

        command = flags + filename
        subprocess.call(command, shell=True)