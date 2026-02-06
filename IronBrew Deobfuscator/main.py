import os
import sys
import chalk
import luamin

input_file = "./input.lua"
output_file = "output.luac"

script = ""
with open(input_file, "r") as f:
script = f.read()

parsed = None
bytecode = None

try:
sys.stdout.write(f"[{chalk.blue_bright('INFO')}] Generating Syntax Tree...")
parsed = luamin.Parse(script)
print(f" {chalk.green_bright('Success')}")
except:
print(f" {chalk.red_bright('Syntax Error')}")
sys.exit(1)

try:
sys.stdout.write(f"[{chalk.blue_bright('INFO')}] Beautifying Syntax Tree...")
parsed = luamin.BeautifyAst(parsed, {"RenameVariables": True, "Format": True})
print(f" {chalk.green_bright('Success')}")
except Exception as err:
print(err)
print(f" {chalk.red_bright('Failed')}")
sys.exit(1)

for obfuscator in os.listdir("./obfuscators"):
try:
deobfuscator_module = import(f"obfuscators.{obfuscator}.deobfuscate", fromlist=[''])
if deobfuscator_module.detect(script):
print(f"[{chalk.blue_bright('INFO')}] Detected obfuscator: {deobfuscator_module.name}")
bytecode = deobfuscator_module.deobfuscate(parsed)
break
except:
continue

if bytecode is not None:
with open(output_file, "w") as f:
f.write(bytecode)
else:
raise Exception("Failed to detect obfuscator")

obfuscators/ironbrew/deobfuscate.py
import chalk
from .analyze import analyze
from .deserialize import deserialize
from .devirtualize import devirtualize
import luamin
import binary

def detect(source):
import re
pattern1 = re.compile(r"return table\.concat[_\-a-zA-Z0-9]+")
pattern2 = re.compile(r"return [_\-a-zA-Z0-9]+true, ?\{\}, ?[_\-a-zA-Z0-9]+\(\);?")
pattern3 = re.compile(r"bit and bit\.bxor or function[_\-a-zA-Z0-9]+, ?[_\-a-zA-Z0-9]+")
return (pattern1.search(source) is not None or 
pattern2.search(source) is not None or 
pattern3.search(source) is not None)

def deobfuscate(ast):
import sys
sys.stdout.write(f"[{chalk.blue_bright('INFO')}] Finding Vm Data...")
vmdata = analyze(ast["StatementList"], True)
sys.stdout.write(f"[{chalk.blue_bright('INFO')}] Deserializing Bytecode...")
vmdata = deserialize(vmdata, True)
luamin.SolveMath(ast)
sys.stdout.write(f"[{chalk.blue_bright('INFO')}] Devirtualizing Bytecode...")
vmdata = devirtualize(vmdata)
return binary.sterilize(vmdata)

name = "IronBrew"
