# sv2fsm
Automatically generate a FSM from SystemVerilog code

## Background:
This was designed using Python3.

## Style Requirements:

I tried to make it pretty style ambiguous, so this should work regardless of your particular branch of SystemVerilog.
Given that your code compiles and you have generally good SystemVerilog style habits, this should work. 

For this to work seemlessly, there need to be a few hard style requirements listed below:

- State transitions must be enclosed in an always_comb block. This works with multiple always_comb blocks, but NOT multiple FSMs in the same file.

- Must use enum to define state names and variables.

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

## Build/Run:

To start using this tool, run `python sv2fsm.py --setup` to move this to your home directory.

You would find it useful to add `alias sv2fsm='python3 ~/sv2fsm/sv2fsm.py ---filename'` to your bash profile.
(*shameless plug* this is really seemless with my other project bash-manager)

Simply run `python3 ~/sv2fsm/sv2fsm.py --filename your_file.sv` or `sv2fsm your_file.sv` (if you created an alias) to generate the FSM.

## Usage:
