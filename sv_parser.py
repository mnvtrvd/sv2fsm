import os

TMP = "tmp/"

def get_depth(line):
    tabs = 0
    for c in line:
        if c == "\t":
            tabs += 1
        else:
            break
    
    return tabs

def found(word, line):
    spl = line.partition(word)
    if spl[1] == "":
        return False
    if (spl[0] != "") and (spl[0][-1].isalpha()):
        return False
    if (spl[2] != "") and (spl[2][0].isalpha()):
        return False
    return True

def get_equiv_parens(line):
    equiv = ""

    for c in line:
        if (c == "(") or (c == ")"):
            equiv = equiv + c

    return equiv    

def rem_parens(line):
    equiv = get_equiv_parens(line)
    if len(equiv)%2 == 1:
        # print("WARNING: parens don't match at start " + equiv)
        line = line + ")"
        equiv = equiv + ")"
    spl = equiv.partition("(())")

    while spl[1] != "":
        nline = ""
        count = 0
        for c in line:
            if (c == "(") or (c == ")"):
                count += 1
                if (count == len(spl[0]) + 1) or (count == len(spl[0] + spl[1])):
                    continue
                else:
                    nline = nline + c
            else:
                nline = nline + c

        line = nline
        equiv = get_equiv_parens(line)
        if len(equiv)%2 == 1:
            print("WARNING: parens don't match " + equiv)
        spl = equiv.partition("(())")
    
    return line

################################################################################

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

def strip_comments(path):
    with open(path, "r") as f:
        lines = f.readlines()

    filename = TMP + path.split("/")[-1]
    with open(filename, "w") as f:
        multiline = False
        for line in lines:
            commentless_line, multiline = rem_comments(line, multiline)
            f.write(commentless_line)

    return filename

################################################################################

def parse_always_combs(path):
    with open(path, "r") as f:
        lines = f.readlines()

    comb = ""
    parens = 0
    count = 0

    for line in lines:
        if (comb == "") and found("always_comb",line):
            comb = line

        if comb != "":
            if found("begin", line):
                parens += 1
            if found("end", line):
                parens -= 1

            if comb != line:
                comb = comb + line

            if parens == 0:
                filename = TMP + "always" + str(count) + ".sv"
                with open(filename, "w") as f:
                    f.write(comb)
                count += 1
                comb = ""

    if count == 0:
        print("ERROR: this file does not contain any always_comb blocks")
        exit()
    else:
        return count

# figures out which always_comb block indicates state transitions
def which_comb(ns):
    i = 0
    filename = TMP + "always" + str(i) + ".sv"
    while os.path.exists(filename):
        with open(filename, "r") as f:
            lines = f.readlines()
    
        for line in lines:
            if ns in line:
                return i
                break
        
        i += 1
        filename = TMP + "always" + str(i) + ".sv"
    
    print("ERROR: this file does not contain any always_comb blocks with state transitions")
    exit()

def get_states(path):
    with open(path, "r") as f:
        lines = f.readlines()

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
            if ";" in line:
                break

    tmp = enum.partition("{")[2].partition("}")
    states = tmp[0].replace(" ", "").split(",")
    state_vars = tmp[2].replace(";", "").replace(" ", "").split(",")

    if len(states) == 0:
        print("ERROR: this file does not contain any enum to specify states")
        exit()
    else:
        return (states, state_vars)

def get_vars(count, state_vars):
    cs = ""
    ns = ""
    i = 0
    filename = TMP + "always" + str(i) + ".sv"
    while os.path.exists(filename):
        with open(filename, "r") as f:
            lines = f.readlines()

        for line in lines:
            if found("case", line):
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

        i += 1
        filename = TMP + "always" + str(i) + ".sv"
    
    if (cs == "") or (ns == ""):
        print("ERROR: could not locate current and/or next state variables")
        exit()
    else:
        return (cs, ns)

################################################################################

def format_states(states):
    for state in states:
        filename = TMP + state + ".sv"
        if not os.path.exists(filename):
            print("WARNING: " + filename + " does not exist")
            break

        with open(filename, "r") as f:
            lines = f.readlines()
        
        os.remove(filename)
        with open(filename, "w") as f:
            for i, line in enumerate(lines):
                if i == 0:
                    continue
                blocks = line.partition("begin")
                for block in blocks:
                    if block.rstrip() != "":
                        f.write(block.rstrip()+"\n")

        with open(filename, "r") as f:
            lines = f.readlines()

        with open(filename, "w") as f:
            parens = 0
            for line in lines:
                if found("begin", line):
                    parens += 1
                elif found("end", line):
                    parens -= 1
                else:
                    f.write("\t"*parens + line)

def get_state_blocks(ns, states):
    # determine which always_comb block has state transitions
    stf = which_comb(ns)

    filename = TMP + "always" + str(stf) + ".sv"
    with open(filename, "r") as f:
        lines = f.readlines()

    block = ""
    parens = 0
    cs = ""

    for line in lines:
        if block == "":
            for state in states:
                before_colon = line.partition(":")[0].strip()
                if (state == before_colon) or ("default" == before_colon):
                    cs = state
                    block = line.lstrip()

        if block != "":
            if found("begin", line):
                parens += 1
            if found("end", line):
                parens -= 1

            if parens == 0:
                filename = TMP + cs + ".sv"
                with open(filename, "w") as f:
                    f.write(block)
                block = ""
                cs = ""
            elif block != line.lstrip():
                block = block + line.lstrip()

    format_states(states)

################################################################################

def get_condition(index, lines):
    cond = ""
    parens = 0
    found = False
    while (index < len(lines)) and (parens != 0 or not found):
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
    
    return (cond[1:], index)

def get_next_state(index, lines):
    next_state = lines[index].partition("=")[2].strip()
    if next_state.partition(";")[1] != "":
        next_state = next_state.partition(";")[0]
        index += 1
    else:
        found = False
        index += 1
        while (index < len(lines)) and not found:
            line = lines[index]
            if line.partition(";")[1] != "":
                next_state = next_state + line.partition(";")[0].strip()
                break
            index += 1
    
    return (next_state.strip(), index)

################################################################################

def format_transition(cond_layer, transition):
    tran_layer = ""
    if cond_layer[-1] == "": # in else case
        for condition in cond_layer[:-1]:
            if tran_layer == "":
                tran_layer = "(" + condition + ")"
            else:
                tran_layer = tran_layer + " || (" + condition + ")"
        
        tran_layer = "!(" + tran_layer + ")"
    elif len(cond_layer) > 1: # in else if case
        for condition in cond_layer[:-1]:
            if tran_layer == "":
                tran_layer = "(" + condition + ")"
            else:
                tran_layer = tran_layer + " || (" + condition + ")"
        
        tran_layer = "!(" + tran_layer + ") && (" + cond_layer[-1] + ")"
    else: # in if case
        tran_layer = cond_layer[0]
    
    if transition == "":
        return "(" + tran_layer + ")"
    else:
        return transition + " && (" +  tran_layer + ")"

def combine_transitions(transitions):
    combined = {}
    for c, t in transitions:
        if c in combined:
            combined[c] = combined[c] + " || (" + t
        elif t != "":
            combined[c] = "(" + t + ")"
        else:
            combined[c] = ""
    
    return combined

################################################################################

def get_transitions(state, ns):
    filename = TMP + state + ".sv"
    with open(filename, "r") as f:
        lines = f.readlines()

    conditions = []
    transitions = []
    i = 0
    while i < len(lines):
        d = get_depth(lines[i])

        if found("else if", lines[i]):
            cond, i = get_condition(i, lines)
            if d < len(conditions): # reaching else if on this level after if
                conditions[d].append(cond)
            else: # reaching else if before if condition
                print("ERROR: should not get here")

        elif found("if", lines[i]):
            cond, i = get_condition(i, lines)
            if d < len(conditions): # reaching if on this level again, overwrite
                conditions[d] = [cond]
            else: # reaching if on this level for the first time
                conditions.append([cond])

        elif found("else", lines[i]):
            cond, i = "", i+1
            if d < len(conditions): # reaching else on this level after if
                conditions[d].append(cond)
            else: # reaching else before if condition
                print("ERROR: should not get here")

        elif ns in lines[i]:
            transition = ""
            for layer in range(d):
                transition = format_transition(conditions[layer], transition)
            
            next_state, i = get_next_state(i, lines)
            transitions.append((next_state,transition))
        else:
            i += 1

    return combine_transitions(transitions)

def save_transitions(state, cs, transitions):
    filename = TMP + state + ".sv"
    os.remove(filename)
    with open(filename, "w") as f:
        needs_else = True
        for s in transitions:
            t = transitions[s]
            if s == state:
                needs_else = False
                if len(transitions) > 2:
                    # print("NOTE: reducing " + state + "->" + state + " to 'else'")
                    t = "otherwise"

            if cs == s:
                s = state
                needs_else = False

            if t == "":
                needs_else = False

            f.write(s + ", " + rem_parens(t) + "\n")

        if needs_else:
            if len(transitions) > 1:
                if state not in transitions:
                    else_case = (state, "otherwise")
                else:
                    return
            elif len(transitions) == 0:
                print("ERROR: are you sure all case and conditional statements have a begin/end?")
                return
            else:
                s = list(transitions.keys())[0]
                t = transitions[s]
                if t == "":
                    return
                new_trans = rem_parens("!(" + t + ")")
                else_case = (state, new_trans)
            f.write(else_case[0] + ", " + else_case[1] + "\n")