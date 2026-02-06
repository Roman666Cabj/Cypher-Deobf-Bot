Call = {
"String": """local A = Inst[OP_A]
local Results = { Stk[A](Unpack(Stk, A + 1, Inst[OP_B])) };
local Edx = 0;
for Idx = A, Inst[OP_C] do 
Edx = Edx + 1;
Stk[Idx] = Results[Edx];
end""",
"Create": lambda instruction: instruction.update({"B": instruction["B"] - instruction["A"] + 1, "C": instruction["C"] - instruction["A"] + 2}) or instruction
}

CallB2 = {
"String": """local A = Inst[OP_A]
local Results = { Stk[A](Stk[A + 1]) };
local Edx = 0;
for Idx = A, Inst[OP_C] do 
Edx = Edx + 1;
Stk[Idx] = Results[Edx];
end""",
"Create": lambda instruction: instruction.update({"C": instruction["C"] - instruction["A"] + 2}) or instruction
}

CallB0 = {
"String": """local A = Inst[OP_A]
local Results = { Stk[A](Unpack(Stk, A + 1, Top)) };
local Edx = 0;
for Idx = A, Inst[OP_C] do 
Edx = Edx + 1;
Stk[Idx] = Results[Edx];
end""",
"Create": lambda instruction: instruction.update({"C": instruction["C"] - instruction["A"] + 2}) or instruction
}

CallB1 = {
"String": """local A = Inst[OP_A]
local Results = { StkA };
local Limit = Inst[OP_C];
local Edx = 0;
for Idx = A, Limit do 
Edx = Edx + 1;
Stk[Idx] = Results[Edx];
end""",
"Create": lambda instruction: instruction.update({"C": instruction["C"] - instruction["A"] + 2}) or instruction
}

CallC0 = {
"String": """local A = Inst[OP_A]
local Results, Limit = _R(Stk[A](Unpack(Stk, A + 1, Inst[OP_B])))
Top = Limit + A - 1
local Edx = 0;
for Idx = A, Top do 
Edx = Edx + 1;
Stk[Idx] = Results[Edx];
end;""",
"Create": lambda instruction: instruction.update({"B": instruction["B"] - instruction["A"] + 1}) or instruction
}

CallC0B2 = {
"String": """local A = Inst[OP_A]
local Results, Limit = _R(Stk[A](Stk[A + 1]))
Top = Limit + A - 1
local Edx = 0;
for Idx = A, Top do 
Edx = Edx + 1;
Stk[Idx] = Results[Edx];
end;""",
"Create": lambda instruction: instruction.update({"B": instruction["B"] - instruction["A"] + 1}) or instruction
}

CallC1 = {
"String": "local A = Inst[OP_A]\nStk[A](Unpack(Stk, A + 1, Inst[OP_B]))",
"Create": lambda instruction: instruction.update({"B": instruction["B"] - instruction["A"] + 1}) or instruction
}

CallC1B2 = {
"String": "local A = Inst[OP_A]\nStk[A](Stk[A + 1])",
"Create": lambda instruction: instruction
}

CallB0C0 = {
"String": """local A = Inst[OP_A]
local Results, Limit = _R(Stk[A](Unpack(Stk, A + 1, Top)))
Top = Limit + A - 1
local Edx = 0;
for Idx = A, Top do 
Edx = Edx + 1;
Stk[Idx] = Results[Edx];
end;""",
"Create": lambda instruction: instruction
}

CallB0C1 = {
"String": "local A = Inst[OP_A]\nStk[A](Unpack(Stk, A + 1, Top))",
"Create": lambda instruction: instruction
}

CallB1C0 = {
"String": """local A = Inst[OP_A]
local Results, Limit = _R(StkA)
Top = Limit + A - 1
local Edx = 0;
for Idx = A, Top do 
Edx = Edx + 1;
Stk[Idx] = Results[Edx];
end;""",
"Create": lambda instruction: instruction
}

CallB1C1 = {
"String": "StkInst[OP_A];",
"Create": lambda instruction: instruction
}

CallC2 = {
"String": "local A = Inst[OP_A]\nStk[A] = Stk[A](Unpack(Stk, A + 1, Inst[OP_B]))",
"Create": lambda instruction: instruction.update({"B": instruction["B"] - instruction["A"] + 1}) or instruction
}

CallC2B2 = {
"String": "local A = Inst[OP_A]\nStk[A] = Stk[A](Stk[A + 1]) ",
"Create": lambda instruction: instruction
}

CallB0C2 = {
"String": "local A = Inst[OP_A]\nStk[A] = Stk[A](Unpack(Stk, A + 1, Top))",
"Create": lambda instruction: instruction
}

CallB1C2 = {
"String": "local A = Inst[OP_A]\nStk[A] = StkA",
"Create": lambda instruction: instruction
}
