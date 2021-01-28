# sv2fsm
Automatically generate a FSM from SystemVerilog code

## Background:
This was designed using Python3.

## Style Requirements:

I tried to make it pretty style ambiguous, so this should work regardless of your particular branch of SystemVerilog.
Given that your code compiles and you have generally good SystemVerilog style habits, this should work. 

For this to work seemlessly, there need to be a few hard style requirements listed below:

- State transitions must be enclosed in an always_comb block. This works with multiple always_comb blocks, but NOT multiple FSMs in the same file.

- Must use enum to define state names and variables
DO:
```verilog
enum logic [1:0] {IDLE, SEND_ADDR, READ, WRITE} cs, ns;
```

- All cases in a case statement NEED a "begin" and "end".
DO:
```verilog
case (cs)
    IDLE: begin
        ns = READ
    end
```
DO NOT:
```verilog
case (cs)
    IDLE: ns = READ
```

- This tool is not able to parse ternary operators, so you may see odd some odd behavior if you use them for state transitions.
DO NOT:
```verilog
case (cs)
    IDLE: ns = (flag) ? READ : WRITE;
```

## Build/Run:
Simply run `python sv2fsm.py --filename "your_file.sv"` to generate the FSM.

## Usage:
