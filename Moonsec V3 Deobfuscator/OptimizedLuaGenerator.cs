using System.Text;
using MoonsecDeobfuscator.Bytecode.Models;

namespace MoonsecDeobfuscator.Deobfuscation.Bytecode
{
    public class OptimizedLuaGenerator(Function rootFunction)
    {
        private readonly StringBuilder _builder = new();
        private readonly Dictionary<int, string> _registerValues = new();
        private readonly Dictionary<string, string> _globalAliases = new();
        private readonly Dictionary<int, string> _temporaryNames = new();
        private int _tempCounter;
        private Function _currentFunction;

        public string Generate()
        {
            ProcessFunction(rootFunction);
            return _builder.ToString().Trim();
        }

        private void ProcessFunction(Function function)
        {
            _currentFunction = function;
            _registerValues.Clear();
            _temporaryNames.Clear();
            
            var instructions = function.Instructions;
            var optimized = new List<string>();
            
            for (var i = 0; i < instructions.Count; i++)
            {
                var instruction = instructions[i];
                var result = ProcessInstruction(instruction, i, instructions);
                
                if (!string.IsNullOrEmpty(result))
                {
                    optimized.Add(result);
                }
                
                if (instruction.OpCode == OpCode.Call && instruction.C == 1)
                {
                    PropagateCallResult(instruction, optimized);
                }
            }
            
            CleanRedundantAssignments(optimized);
            
            _builder.Append($"function {function.Name}(");
            for (var i = 0; i < function.NumParams; i++)
            {
                _builder.Append($"arg{i}");
                if (i + 1 < function.NumParams)
                    _builder.Append(", ");
            }
            if (function.IsVarArgFlag == 2)
                _builder.Append(function.NumParams > 0 ? ", ..." : "...");
            _builder.AppendLine(")");
            
            foreach (var line in optimized)
            {
                _builder.AppendLine($"    {line}");
            }
            
            _builder.AppendLine("end");
            
            foreach (var childFunction in function.Functions)
                ProcessFunction(childFunction);
        }

        private string ProcessInstruction(Instruction instruction, int index, List<Instruction> allInstructions)
        {
            var A = instruction.A;
            var B = instruction.B;
            var C = instruction.C;
            var function = _currentFunction;

            switch (instruction.OpCode)
            {
                case OpCode.GetGlobal:
                    var globalName = ((StringConstant)function.Constants[B]).Value;
                    _registerValues[A] = globalName;
                    
                    if (globalName == "print" || globalName == "warn" || globalName == "error" || 
                        globalName == "require" || globalName == "loadstring" || globalName == "type" ||
                        globalName == "tostring" || globalName == "tonumber" || globalName == "next" ||
                        globalName == "pairs" || globalName == "ipairs" || globalName == "rawget" ||
                        globalName == "rawset" || globalName == "rawequal" || globalName == "getfenv" ||
                        globalName == "setfenv")
                    {
                        return $"local R{A} = {globalName}";
                    }
                    
                    return null;

                case OpCode.LoadK:
                    var constant = function.Constants.ElementAtOrDefault(B);
                    if (constant is StringConstant strConst)
                    {
                        _registerValues[A] = $"\"{strConst.Value.Replace("\"", "\\\"")}\"";
                    }
                    else if (constant is NumberConstant numConst)
                    {
                        _registerValues[A] = numConst.Value.ToString();
                    }
                    else if (constant is BooleanConstant boolConst)
                    {
                        _registerValues[A] = boolConst.Value ? "true" : "false";
                    }
                    else if (constant is NilConstant)
                    {
                        _registerValues[A] = "nil";
                    }
                    return null;

                case OpCode.Move:
                    if (_registerValues.TryGetValue(B, out var movedValue))
                    {
                        _registerValues[A] = movedValue;
                        
                        if (A != B)
                        {
                            _registerValues.Remove(B);
                        }
                    }
                    return null;

                case OpCode.Call:
                    return FormatCall(instruction, allInstructions, index);

                case OpCode.SetGlobal:
                    var targetName = ((StringConstant)function.Constants[B]).Value;
                    if (_registerValues.TryGetValue(A, out var valueToSet))
                    {
                        return $"{targetName} = {valueToSet}";
                    }
                    return $"{targetName} = R{A}";

                case OpCode.LoadBool:
                    _registerValues[A] = B != 0 ? "true" : "false";
                    return null;

                case OpCode.LoadNil:
                    for (int r = A; r <= B; r++)
                    {
                        _registerValues[r] = "nil";
                    }
                    return null;

                case OpCode.GetUpval:
                    _registerValues[A] = $"upvalue{B}";
                    return $"local R{A} = upvalue{B}";

                case OpCode.SetUpval:
                    if (_registerValues.TryGetValue(A, out var upvalValue))
                    {
                        return $"upvalue_{B} = {upvalValue}";
                    }
                    return $"upvalue_{B} = R{A}";

                case OpCode.GetTable:
                    return FormatGetTable(instruction);

                case OpCode.SetTable:
                    return FormatSetTable(instruction);

                case OpCode.NewTable:
                    _registerValues[A] = $"table_{_tempCounter++}";
                    return $"local R{A} = {{}}";

                case OpCode.Self:
                    return FormatSelf(instruction);

                case OpCode.Add:
                case OpCode.Sub:
                case OpCode.Mul:
                case OpCode.Div:
                case OpCode.Mod:
                case OpCode.Pow:
                    return FormatArithmetic(instruction);

                case OpCode.Unm:
                    if (_registerValues.TryGetValue(B, out var unmValue))
                    {
                        _registerValues[A] = $"-{unmValue}";
                        return null;
                    }
                    return $"local R{A} = -R{B}";

                case OpCode.Not:
                    if (_registerValues.TryGetValue(B, out var notValue))
                    {
                        _registerValues[A] = $"not {notValue}";
                        return null;
                    }
                    return $"local R{A} = not R{B}";

                case OpCode.Len:
                    if (_registerValues.TryGetValue(B, out var lenValue))
                    {
                        _registerValues[A] = $"#{lenValue}";
                        return null;
                    }
                    return $"local R{A} = #R{B}";

                case OpCode.Concat:
                    return FormatConcat(instruction);

                case OpCode.Eq:
                case OpCode.Lt:
                case OpCode.Le:
                    return FormatComparison(instruction, allInstructions, index);

                case OpCode.Test:
                    return FormatTest(instruction, allInstructions, index);

                case OpCode.TestSet:
                    return FormatTestSet(instruction, allInstructions, index);

                case OpCode.TailCall:
                    return FormatTailCall(instruction);

                case OpCode.Return:
                    return FormatReturn(instruction);

                case OpCode.ForLoop:
                    return null;

                case OpCode.ForPrep:
                    return FormatForPrep(instruction);

                case OpCode.TForLoop:
                    return FormatTForLoop(instruction);

                case OpCode.Closure:
                    var proto = function.Functions[B];
                    _registerValues[A] = proto.Name;
                    return $"local R{A} = {proto.Name}";

                case OpCode.VarArg:
                    return FormatVarArg(instruction);

                case OpCode.Jmp:
                    return null;
            }

            return null;
        }

        private string FormatCall(Instruction instruction, List<Instruction> allInstructions, int index)
        {
            var A = instruction.A;
            var B = instruction.B;
            var C = instruction.C;
            var function = _currentFunction;

            string functionExpr;
            var args = new List<string>();

            if (_registerValues.TryGetValue(A, out var funcValue))
            {
                functionExpr = funcValue;
            }
            else
            {
                functionExpr = $"R{A}";
            }

            if (B > 1)
            {
                for (int i = A + 1; i <= A + B - 1; i++)
                {
                    if (_registerValues.TryGetValue(i, out var argValue))
                    {
                        args.Add(argValue);
                    }
                    else
                    {
                        args.Add($"R{i}");
                    }
                }
            }
            else if (B == 0)
            {
                if (_registerValues.TryGetValue(A + 1, out var singleArg) && singleArg != $"R{A + 1}")
                {
                    args.Add(singleArg);
                }
            }

            var callStr = $"{functionExpr}({string.Join(", ", args)})";

            if (functionExpr == "print" && args.Count == 1 && args[0].StartsWith("\"") && args[0].EndsWith("\""))
            {
                callStr = $"print({args[0]})";
            }
            else if (functionExpr == "require" && args.Count == 1)
            {
                callStr = $"require({args[0]})";
            }
            else if (functionExpr == "loadstring" && args.Count == 1)
            {
                callStr = $"loadstring({args[0]})()";
            }

            if (C == 1)
            {
                return callStr;
            }
            else if (C == 0)
            {
                _registerValues[A] = callStr;
                return null;
            }
            else
            {
                var rets = new List<string>();
                for (int i = A; i <= A + C - 2; i++)
                {
                    var rn = $"R{i}";
                    rets.Add(rn);
                    _registerValues[i] = rn;
                }
                return $"local {string.Join(", ", rets)} = {callStr}";
            }
        }

        private void PropagateCallResult(Instruction instruction, List<string> optimized)
        {
            var A = instruction.A;
            
            if (optimized.Count > 0)
            {
                var lastLine = optimized[^1];
                if (lastLine.StartsWith("print(") || lastLine.StartsWith("require(") || 
                    lastLine.StartsWith("loadstring("))
                {
                    _registerValues[A] = lastLine;
                }
            }
        }

        private void CleanRedundantAssignments(List<string> optimized)
        {
            for (int i = optimized.Count - 1; i >= 0; i--)
            {
                var line = optimized[i];
                
                if (line.StartsWith("local R") && line.Contains(" = print") && i + 1 < optimized.Count)
                {
                    var nextLine = optimized[i + 1];
                    if (nextLine.StartsWith("print("))
                    {
                        optimized.RemoveAt(i);
                    }
                }
                
                if (line.StartsWith("local R") && line.Contains(" = \"") && i + 1 < optimized.Count)
                {
                    var nextLine = optimized[i + 1];
                    var match = System.Text.RegularExpressions.Regex.Match(line, @"local R(\d+) = ""([^""]+)""");
                    if (match.Success)
                    {
                        var regNum = match.Groups[1].Value;
                        var strValue = match.Groups[2].Value;
                        var expectedCall = $"print(\"{strValue}\")";
                        
                        if (nextLine == expectedCall)
                        {
                            optimized.RemoveAt(i);
                        }
                    }
                }
            }
            
            var final = new List<string>();
            var printCalls = new HashSet<string>();
            
            foreach (var line in optimized)
            {
                if (line.StartsWith("print("))
                {
                    if (!printCalls.Contains(line))
                    {
                        printCalls.Add(line);
                        final.Add(line);
                    }
                }
                else
                {
                    final.Add(line);
                }
            }
            
            optimized.Clear();
            optimized.AddRange(final);
        }

        private string FormatGetTable(Instruction instruction)
        {
            var A = instruction.A;
            var B = instruction.B;
            var C = instruction.C;
            var function = _currentFunction;

            string objExpr;
            string keyExpr;

            if (_registerValues.TryGetValue(B, out var objValue))
            {
                objExpr = objValue;
            }
            else
            {
                objExpr = $"R{B}";
            }

            if (C >= 256 && function.Constants[C - 256] is StringConstant sc)
            {
                var name = sc.Value;
                if (IsIdentifier(name))
                {
                    _registerValues[A] = $"{objExpr}.{name}";
                    return null;
                }
                else
                {
                    keyExpr = $"\"{name}\"";
                }
            }
            else if (C >= 256)
            {
                keyExpr = function.Constants[C - 256].ToString();
            }
            else
            {
                if (_registerValues.TryGetValue(C, out var keyValue))
                {
                    keyExpr = keyValue;
                }
                else
                {
                    keyExpr = $"R{C}";
                }
            }

            _registerValues[A] = $"{objExpr}[{keyExpr}]";
            return null;
        }

        private string FormatSetTable(Instruction instruction)
        {
            var A = instruction.A;
            var B = instruction.B;
            var C = instruction.C;
            var function = _currentFunction;

            string objExpr;
            string keyExpr;
            string valExpr;

            if (_registerValues.TryGetValue(A, out var objValue))
            {
                objExpr = objValue;
            }
            else
            {
                objExpr = $"R{A}";
            }

            if (B >= 256 && function.Constants[B - 256] is StringConstant scKey)
            {
                var keyName = scKey.Value;
                if (IsIdentifier(keyName))
                {
                    keyExpr = $".{keyName}";
                }
                else
                {
                    keyExpr = $"[\"{keyName}\"]";
                }
            }
            else if (B >= 256)
            {
                keyExpr = $"[{function.Constants[B - 256]}]";
            }
            else
            {
                if (_registerValues.TryGetValue(B, out var keyValue))
                {
                    keyExpr = $"[{keyValue}]";
                }
                else
                {
                    keyExpr = $"[R{B}]";
                }
            }

            if (C >= 256)
            {
                valExpr = function.Constants[C - 256].ToString();
            }
            else
            {
                if (_registerValues.TryGetValue(C, out var valValue))
                {
                    valExpr = valValue;
                }
                else
                {
                    valExpr = $"R{C}";
                }
            }

            return $"{objExpr}{keyExpr} = {valExpr}";
        }

        private string FormatSelf(Instruction instruction)
        {
            var A = instruction.A;
            var B = instruction.B;
            var C = instruction.C;
            var function = _currentFunction;

            string objExpr;
            string keyExpr;

            if (_registerValues.TryGetValue(B, out var objValue))
            {
                objExpr = objValue;
            }
            else
            {
                objExpr = $"R{B}";
            }

            if (C >= 256 && function.Constants[C - 256] is StringConstant sc)
            {
                var name = sc.Value;
                if (IsIdentifier(name))
                {
                    _registerValues[A] = $"{objExpr}:{name}";
                    _registerValues[A + 1] = objExpr;
                    return null;
                }
                else
                {
                    keyExpr = $"\"{name}\"";
                }
            }
            else if (C >= 256)
            {
                keyExpr = function.Constants[C - 256].ToString();
            }
            else
            {
                if (_registerValues.TryGetValue(C, out var keyValue))
                {
                    keyExpr = keyValue;
                }
                else
                {
                    keyExpr = $"R{C}";
                }
            }

            _registerValues[A] = $"{objExpr}[{keyExpr}]";
            _registerValues[A + 1] = objExpr;
            return null;
        }

        private string FormatArithmetic(Instruction instruction)
        {
            var A = instruction.A;
            var B = instruction.B;
            var C = instruction.C;
            var function = _currentFunction;

            string leftExpr;
            string rightExpr;
            string op = instruction.OpCode switch
            {
                OpCode.Add => "+",
                OpCode.Sub => "-",
                OpCode.Mul => "*",
                OpCode.Div => "/",
                OpCode.Mod => "%",
                OpCode.Pow => "^",
                _ => "+"
            };

            if (B >= 256)
            {
                leftExpr = function.Constants[B - 256].ToString();
            }
            else
            {
                if (_registerValues.TryGetValue(B, out var leftValue))
                {
                    leftExpr = leftValue;
                }
                else
                {
                    leftExpr = $"R{B}";
                }
            }

            if (C >= 256)
            {
                rightExpr = function.Constants[C - 256].ToString();
            }
            else
            {
                if (_registerValues.TryGetValue(C, out var rightValue))
                {
                    rightExpr = rightValue;
                }
                else
                {
                    rightExpr = $"R{C}";
                }
            }

            _registerValues[A] = $"{leftExpr} {op} {rightExpr}";
            return null;
        }

        private string FormatConcat(Instruction instruction)
        {
            var A = instruction.A;
            var B = instruction.B;
            var C = instruction.C;

            var parts = new List<string>();
            for (int r = B; r <= C; r++)
            {
                if (_registerValues.TryGetValue(r, out var partValue))
                {
                    parts.Add(partValue);
                }
                else
                {
                    parts.Add($"R{r}");
                }
            }

            _registerValues[A] = string.Join(" .. ", parts);
            return null;
        }

        private string FormatComparison(Instruction instruction, List<Instruction> allInstructions, int index)
        {
            var A = instruction.A;
            var B = instruction.B;
            var C = instruction.C;
            var function = _currentFunction;

            string leftExpr;
            string rightExpr;
            string cmp = instruction.OpCode switch
            {
                OpCode.Eq => A == 0 ? "==" : "~=",
                OpCode.Lt => A == 0 ? "<" : ">",
                OpCode.Le => A == 0 ? "<=" : ">=",
                _ => "=="
            };

            if (B >= 256)
            {
                leftExpr = function.Constants[B - 256].ToString();
            }
            else
            {
                if (_registerValues.TryGetValue(B, out var leftValue))
                {
                    leftExpr = leftValue;
                }
                else
                {
                    leftExpr = $"R{B}";
                }
            }

            if (C >= 256)
            {
                rightExpr = function.Constants[C - 256].ToString();
            }
            else
            {
                if (_registerValues.TryGetValue(C, out var rightValue))
                {
                    rightExpr = rightValue;
                }
                else
                {
                    rightExpr = $"R{C}";
                }
            }

            var condition = $"{leftExpr} {cmp} {rightExpr}";
            
            if (index + 1 < allInstructions.Count && allInstructions[index + 1].OpCode == OpCode.Jmp)
            {
                return $"if {condition} then";
            }
            
            return $"if {condition} then";
        }

        private string FormatTest(Instruction instruction, List<Instruction> allInstructions, int index)
        {
            var A = instruction.A;
            var C = instruction.C;

            string expr;
            if (_registerValues.TryGetValue(A, out var testValue))
            {
                expr = testValue;
            }
            else
            {
                expr = $"R{A}";
            }

            var condition = C == 0 ? $"not {expr}" : expr;
            
            if (index + 1 < allInstructions.Count && allInstructions[index + 1].OpCode == OpCode.Jmp)
            {
                return $"if {condition} then";
            }
            
            return $"if {condition} then";
        }

        private string FormatTestSet(Instruction instruction, List<Instruction> allInstructions, int index)
        {
            var A = instruction.A;
            var B = instruction.B;
            var C = instruction.C;

            string expr;
            if (_registerValues.TryGetValue(B, out var testValue))
            {
                expr = testValue;
            }
            else
            {
                expr = $"R{B}";
            }

            var condition = C == 0 ? $"not {expr}" : expr;
            _registerValues[A] = expr;
            
            if (index + 1 < allInstructions.Count && allInstructions[index + 1].OpCode == OpCode.Jmp)
            {
                return $"if {condition} then";
            }
            
            return $"if {condition} then";
        }

        private string FormatTailCall(Instruction instruction)
        {
            var A = instruction.A;
            var B = instruction.B;

            string functionExpr;
            var args = new List<string>();

            if (_registerValues.TryGetValue(A, out var funcValue))
            {
                functionExpr = funcValue;
            }
            else
            {
                functionExpr = $"R{A}";
            }

            if (B > 1)
            {
                for (int i = A + 1; i <= A + B - 1; i++)
                {
                    if (_registerValues.TryGetValue(i, out var argValue))
                    {
                        args.Add(argValue);
                    }
                    else
                    {
                        args.Add($"R{i}");
                    }
                }
            }

            return $"return {functionExpr}({string.Join(", ", args)})";
        }

        private string FormatReturn(Instruction instruction)
        {
            var A = instruction.A;
            var B = instruction.B;

            if (B == 1)
                return "return";
            
            var rets = new List<string>();
            for (int i = A; i <= A + B - 2; i++)
            {
                if (_registerValues.TryGetValue(i, out var retValue))
                {
                    rets.Add(retValue);
                }
                else
                {
                    rets.Add($"R{i}");
                }
            }
            return $"return {string.Join(", ", rets)}";
        }

        private string FormatForPrep(Instruction instruction)
        {
            var A = instruction.A;

            string init, limit, step;
            
            if (_registerValues.TryGetValue(A, out var initValue))
            {
                init = initValue;
            }
            else
            {
                init = $"R{A}";
            }
            
            if (_registerValues.TryGetValue(A + 1, out var limitValue))
            {
                limit = limitValue;
            }
            else
            {
                limit = $"R{A + 1}";
            }
            
            if (_registerValues.TryGetValue(A + 2, out var stepValue))
            {
                step = stepValue;
            }
            else
            {
                step = $"R{A + 2}";
            }

            var varName = $"i_{_tempCounter++}";
            _registerValues[A + 3] = varName;
            
            return $"for {varName} = {init}, {limit}, {step} do";
        }

        private string FormatTForLoop(Instruction instruction)
        {
            var A = instruction.A;
            var C = instruction.C;

            var vars = new List<string>();
            for (int i = A + 3; i <= A + 2 + C; i++)
            {
                var varName = $"v{_tempCounter++}";
                vars.Add(varName);
                _registerValues[i] = varName;
            }

            string iterator;
            if (_registerValues.TryGetValue(A, out var iterValue))
            {
                iterator = iterValue;
            }
            else
            {
                iterator = $"R{A}";
            }

            return $"for {string.Join(", ", vars)} in {iterator} do";
        }

        private string FormatVarArg(Instruction instruction)
        {
            var A = instruction.A;
            var B = instruction.B;

            if (B == 0)
            {
                _registerValues[A] = "...";
                return null;
            }
            else
            {
                var vars = new List<string>();
                for (int i = A; i <= A + B - 2; i++)
                {
                    var varName = $"arg{_tempCounter++}";
                    vars.Add(varName);
                    _registerValues[i] = varName;
                }
                return $"local {string.Join(", ", vars)} = ...";
            }
        }

        private static bool IsIdentifier(string s)
        {
            if (string.IsNullOrEmpty(s)) return false;
            if (!(char.IsLetter(s[0]) || s[0] == '_')) return false;
            for (int i = 1; i < s.Length; i++)
            {
                if (!(char.IsLetterOrDigit(s[i]) || s[i] == '_'))
                    return false;
            }
            return true;
        }
    }
}
