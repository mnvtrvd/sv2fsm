# sv2fsm
Automatically generate a FSM from SystemVerilog code

## Background:

This was designed using Python3.

## Style Requirements:

For this to work seemlessly, there need to be a few hard style requirements.
Given that your code compiles and you have generally good SystemVerilog
style habits, this should work. If there are any special requirements, I will
list them below:

- all if/else if/else statements NEED a "begin" and "end". (I know one-liners
are possible, but the parser I created isn't currently capable of doing so)

## Build/Run:

Simply run `python sv2fsm.py --filename "your_file.sv"` to generate the FSM.s

## Usage:
