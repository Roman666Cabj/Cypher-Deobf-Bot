import os
import chalk
import luamin
import binary
import emulation

opcodes = {}

def createNL(n):
return {
"Type": "NumberLiteral",
"Token": {
"Type": "Number",
"LeadingWhite": "",
"Source": str(n)
},
"GetFirstToken": lambda: None,
"GetLastToken": lambda: None
}

replace_known = None
replace_unknown = None

def find(Enum, tokens, clause=None, parent=None):
clause = clause or tokens["Clauses"]
ifstat = clause["Condition"]
elsestats = clause["ElseClauseList"]
if ifstat["Type"] != "BinopExpr" or ifstat["Lhs"]["Type"] != "VariableExpr":
return parent
if ifstat["Lhs"]["Variable"]["Name"] != tokens["Enum"]:
return parent
if ifstat["Rhs"]["Type"] == "UnopExpr":
solved = emulation.unopexpr(ifstat["Rhs"])
if solved:
ifstat["Rhs"] = createNL(solved)
else:
return None
elif ifstat["Rhs"]["Type"] != "NumberLiteral":
raise Exception("Unhandled comparison in control flow")
def handle(clause):
if clause["Body"]["StatementList"][0]["Type"] == "IfStat":
return find(Enum, tokens, clause["Body"]["StatementList"][0], clause["Body"]["StatementList"])
else:
return clause["Body"]["StatementList"]
if emulation.expression(Enum, ifstat["Token_Op"]["Source"], ifstat["Rhs"]["Token"]["Source"]):
return handle(clause)
for i in range(len(elsestats)):
clause = elsestats[i]
ifstat = clause["Condition"]
if clause["ClauseType"] == "elseif":
if ifstat["Rhs"]["Type"] == "UnopExpr":
solved = emulation.unopexpr(ifstat["Rhs"])
if solved:
ifstat["Rhs"] = createNL(solved)
else:
return None
elif ifstat["Rhs"]["Type"] != "NumberLiteral":
raise Exception("Unhandled comparison in control flow")
if emulation.expression(Enum, ifstat["Token_Op"]["Source"], ifstat["Rhs"]["Token"]["Source"]):
return handle(clause)
elif clause["ClauseType"] == "else":
return handle(clause)
return None

def match(instruction, operands, pc, tokens, nolocal=False):
def compare(srcstr, thorough):
def structure(a, b):
if a["Type"] != b["Type"]:
if b["Type"] == "NumberLiteral" and a["Type"] == "UnopExpr":
solved = emulation.unopexpr(a)
if solved:
a = createNL(solved)
else:
return False
else:
return False
if a["Type"] == "AssignmentStat":
return list_compare(a["Rhs"], b["Rhs"]) and list_compare(a["Lhs"], b["Lhs"])
elif a["Type"] == "IndexExpr":
names = True
if thorough and "Variable" in a["Base"] and a["Base"]["Variable"] is not None and b["Base"]["Type"] == "VariableExpr":
names = a["Base"]["Variable"]["Name"] == b["Base"]["Token"]["Source"]
return names and structure(a["Base"], b["Base"]) and structure(a["Index"], b["Index"])
elif a["Type"] == "VariableExpr":
return True
elif a["Type"] == "NumberLiteral":
return a["Source"] == b["Source"]
elif a["Type"] == "LocalVarStat":
return list_compare(a["ExprList"], b["ExprList"])
elif a["Type"] == "CallExprStat":
e1 = a["Expression"]
e2 = b["Expression"]
return structure(e1["Base"], e2["Base"]) and list_compare(e1["FunctionArguments"]["ArgList"], e2["FunctionArguments"]["ArgList"])
elif a["Type"] == "CallExpr":
return structure(a["Base"], b["Base"]) and list_compare(a["FunctionArguments"]["ArgList"], b["FunctionArguments"]["ArgList"])
elif a["Type"] == "BinopExpr":
t1 = a["Token_Op"]
t2 = b["Token_Op"]
return t1["Source"] == t2["Source"] and structure(a["Rhs"], b["Rhs"]) and structure(a["Lhs"], b["Lhs"])
elif a["Type"] == "DoStat":
return list_compare(a["Body"]["StatementList"], b["Body"]["StatementList"])
elif a["Type"] == "ReturnStat":
return list_compare(a["ExprList"], b["ExprList"])
elif a["Type"] == "NilLiteral":
return True
elif a["Type"] == "TableLiteral":
return True
elif a["Type"] == "NumericForStat":
return list_compare(a["RangeList"], b["RangeList"]) and list_compare(a["Body"]["StatementList"], b["Body"]["StatementList"])
elif a["Type"] == "ParenExpr":
return structure(a["Expression"], b["Expression"])
elif a["Type"] == "UnopExpr":
return a["Token_Op"]["Source"] == b["Token_Op"]["Source"] and structure(a["Rhs"], b["Rhs"])
elif a["Type"] == "IfStat":
if not structure(a["Condition"], b["Condition"]):
return False
if thorough and not list_compare(a["Body"]["StatementList"], b["Body"]["StatementList"]):
return False
o1 = a["ElseClauseList"]
o2 = b["ElseClauseList"]
if len(o1) != len(o2):
return False
for i in range(len(o1)):
c1 = o1[i]
c2 = o2[i]
t1 = c1["ClauseType"]
t2 = c2["ClauseType"]
if t1 != t2:
return False
if not list_compare(c1["Body"]["StatementList"], c2["Body"]["StatementList"]):
return False
return list_compare(a["Body"]["StatementList"], b["Body"]["StatementList"])
return False
def list_compare(a, b):
if len(a) != len(b):
return False
elif len(a) == 0:
return True
for i in range(len(a)):
if not structure(a[i], b[i]):
return False
return True
if nolocal:
srcstr = srcstr.replace("local", "")
srcstr = replace_known(srcstr)
ast = luamin.Parse(srcstr)
return list_compare(instruction, ast["StatementList"])
def isSuperJump(s):
if s["Type"] != "AssignmentStat":
return False
r = s["Rhs"][0]
l = s["Lhs"][0]
return (r["Type"] == "BinopExpr" and
r["Lhs"]["Type"] == "VariableExpr" and
r["Lhs"]["Variable"]["Name"] == tokens["InstrPoint"] and
r["Rhs"]["Type"] == "NumberLiteral" and
r["Rhs"]["Token"]["Source"] == "1" and
l["Type"] == "VariableExpr" and
l["Variable"]["Name"] == tokens["InstrPoint"])
for opcode_name in opcodes:
aliases = opcodes[opcode_name]
for v in aliases.values():
if ("Match" in v and v"Match") or ("String" in v and compare(v["String"], v.get("Thorough", False))):
operands[pc]["PC"] = pc
op = v"Create"
op["OpCode"] = binary.OpCodes.index(opcode_name)
op["OpName"] = binary.OpCodes[op["OpCode"]]
op["Type"] = binary.OpCodeTypes[op["OpCode"]]
return op
if any(isSuperJump(s) for s in instruction):
sub = []
instruction_dict = {
"Instructions": [],
"SuperInstruction": True,
"MatchedInstructions": [],
"SubCount": sum(1 for s in instruction if isSuperJump(s))
}
instruction_dict["Instructions"].append(sub)
spc = 0
while spc < len(instruction):
operation = instruction[spc]
if isSuperJump(operation):
spc += 1
sub = []
instruction_dict["Instructions"].append(sub)
continue
elif operation["Type"] == "LocalVarStat":
spc += 1
continue
else:
sub.append(operation)
spc += 1
for spc in range(len(instruction_dict["Instructions"])):
vminstruction = instruction_dict["Instructions"][spc]
instructionmt = match(vminstruction, operands, pc + spc, tokens, True)
if instructionmt is not None:
instructionmt["Enum"] = spc
instruction_dict["MatchedInstructions"].append(instructionmt)
else:
instruction_dict["MatchedInstructions"].append({
"PlaceHolder": True,
"Enum": spc
})
return instruction_dict
return None

def devirtualize(vmdata):
global opcodes, replace_known, replace_unknown
if vmdata["Version"] == "IronBrew V2.7.0":
for opcode_file in os.listdir("./obfuscators/ironbrew/opcodes/2.7.0"):
opcode_name = opcode_file.split(".")[0]
opcodes[opcode_name] = import(f"obfuscators.ironbrew.opcodes.2.7.0.{opcode_name}", fromlist=[''])
elif vmdata["Version"] in ["IronBrew V2.7.1", "AztupBrew V2.7.2"]:
for opcode_file in os.listdir("./obfuscators/ironbrew/opcodes/2.7.1"):
opcode_name = opcode_file.split(".")[0]
opcodes[opcode_name] = import(f"obfuscators.ironbrew.opcodes.2.7.1.{opcode_name}", fromlist=[''])
def replace_known_func(str):
res = str.replace("OP_A", "2").replace("OP_B", "3")
res = res.replace("InstrPoint", vmdata["Tokens"]["InstrPoint"])
res = res.replace("Upvalues", vmdata["Tokens"]["Upvalues"])
res = res.replace("Unpack", vmdata["Tokens"]["Unpack"])
res = res.replace("Const", vmdata["Tokens"]["Const"])
res = res.replace("Wrap", vmdata["Tokens"]["Wrap"])
res = res.replace("Inst", vmdata["Tokens"]["Inst"])
res = res.replace("Top", vmdata["Tokens"]["Top"])
res = res.replace("Stk", vmdata["Tokens"]["Stk"])
res = res.replace("Env", vmdata["Tokens"]["Env"])
if vmdata["Version"] == "IronBrew V2.7.0":
res = res.replace("OP_C", "5")
else:
res = res.replace("OP_C", "4")
return res
def replace_unknown_func(str):
res = str.replace("[2", "[OP_A").replace("[3", "[OP_B").replace("[4", "[OP_C")
res = res.replace(vmdata["Tokens"]["InstrPoint"], "InstrPoint")
res = res.replace(vmdata["Tokens"]["Upvalues"], "Upvalues")
res = res.replace(vmdata["Tokens"]["Unpack"], "Unpack")
res = res.replace(vmdata["Tokens"]["Const"], "Const")
res = res.replace(vmdata["Tokens"]["Wrap"], "Wrap")
res = res.replace(vmdata["Tokens"]["Inst"], "Inst")
res = res.replace(vmdata["Tokens"]["Top"], "Top")
res = res.replace(vmdata["Tokens"]["Stk"], "Stk")
res = res.replace(vmdata["Tokens"]["Env"], "Env")
if vmdata["Version"] == "IronBrew V2.7.0":
res = res.replace("[5", "[OP_C")
return res
replace_known = replace_known_func
replace_unknown = replace_unknown_func
def devirtualize_chunk(chunk):
instructions = chunk["Instructions"]
prototypes = chunk["Prototypes"]
matched = []
tokens = vmdata["Tokens"]
print()
for pc in range(len(instructions)):
Enum = instructions[pc]["Enum"]
vminstruction = find(Enum, tokens)
if vminstruction is not None:
instructionmt = match(vminstruction, instructions, pc, tokens)
if instructionmt is not None:
if "SuperInstruction" in instructionmt and instructionmt["SuperInstruction"]:
subInstructions = instructionmt["MatchedInstructions"]
print(f"[{chalk.magenta_bright('OUT')}] No {chalk.magenta_bright('Matched')} Instruction For #{Enum} ... SuperInstruction?")
pc += instructionmt["SubCount"]
for i in range(len(subInstructions)):
if "PlaceHolder" not in subInstructions[i] or not subInstructions[i]["PlaceHolder"]:
matched.append(subInstructions[i])
print(f"[{chalk.magenta_bright('OUT')}]   Matched Sub-Instruction For #{subInstructions[i]['Enum'] + 1}: {binary.OpCodes[subInstructions[i]['OpCode']].upper()}")
else:
str_repr = luamin.Print({"Type": "StatList", "StatementList": instructionmt["Instructions"][subInstructions[i]["Enum"]], "SemicolonList": []})
print(str_repr)
print(f"[{chalk.magenta_bright('OUT')}]   No Matched Sub-Instruction For #{subInstructions[i]['Enum'] + 1}")
raise Exception("ayo")
else:
matched.append(instructionmt)
print(f"[{chalk.magenta_bright('OUT')}] Matched Instruction #{Enum}: {binary.OpCodes[instructionmt['OpCode']].upper()}")
else:
str_repr = luamin.Print({"Type": "StatList", "StatementList": vminstruction, "SemicolonList": []})
str_repr = replace_unknown(str_repr)
print(str_repr)
print(f"[{chalk.magenta_bright('OUT')}] No {chalk.magenta_bright('Matched')} Instruction #{Enum}")
raise Exception("ayo")
else:
print(f"[{chalk.magenta_bright('OUT')}] No {chalk.magenta_bright('Found')} Instruction #{Enum}")
for i in range(len(prototypes)):
prototypes[i] = devirtualize_chunk(prototypes[i])
chunk["Instructions"] = matched
return chunk
print()
devirtualized = devirtualize_chunk(vmdata["Chunk"])
def do_vararg(chunk):
for i in range(len(chunk["Instructions"])):
instruction = chunk["Instructions"][i]
instruction_name = binary.OpCodes[instruction["OpCode"]]
if instruction_name == "VarArg":
chunk["VarArg"] = True
continue
for i in range(len(chunk["Prototypes"])):
do_vararg(chunk["Prototypes"][i])
do_vararg(devirtualized)
return devirtualized
