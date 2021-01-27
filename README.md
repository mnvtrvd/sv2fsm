# sv2fsm
Automatically generate a FSM from SystemVerilog code

## Background:

This was designed using Python3.

## Style Requirements:

I tried to make it pretty style ambiguous, so this should work
regardless of your particular branch of SystemVerilog.
Given that your code compiles and you have generally good SystemVerilog style habits, this should work. 

For this to work seemlessly, there need to be a few hard style requirements listed below:

- all case and conditional (if/else if/else) statements NEED a "begin" and "end". (I know one-liners
are possible, but the parser I created isn't currently capable of doing so)
- must use enum to define state names and variables (apparently this isn't universal)
- works with multiple always_comb blocks, but NOT multiple FSMs in the same file (only 1 enum)

## Build/Run:

Simply run `python sv2fsm.py --filename "your_file.sv"` to generate the FSM.

## Usage:
