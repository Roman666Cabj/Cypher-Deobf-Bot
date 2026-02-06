using MoonsecDeobfuscator.Bytecode.Models;

namespace MoonsecDeobfuscator.Deobfuscation
{
    public static class OpCodes
    {
        public static readonly Dictionary<string, (OpCode, Action<Instruction>?)> StaticOpcodes = new()
        {
            ["91909190"] = (OpCode.Move, null),
            ["1419090"] = (OpCode.LoadK, instruction => instruction.B--),
            ["91902690"] = (OpCode.LoadBool, null),
            ["91902690291529"] = (OpCode.LoadBool, instruction => instruction.C = 1),
            ["13909091"] = (OpCode.LoadNil, null),
            ["91909290"] = (OpCode.GetUpval, null),
            ["91909390"] = (OpCode.GetGlobal, instruction => instruction.B--),
            ["9190991909190"] = (OpCode.GetTable, null),
            ["91909919090"] = (OpCode.GetTable, instruction => instruction.C += 255),
            ["93909190"] = (OpCode.SetGlobal, instruction => instruction.B--),
            ["92909190"] = (OpCode.SetUpval, null),
            ["9919091909190"] = (OpCode.SetTable, null),
            ["99190919090"] = (OpCode.SetTable, instruction => instruction.C += 255),
            ["99190909190"] = (OpCode.SetTable, instruction => instruction.B += 255),
            ["991909090"] = (OpCode.SetTable, instruction =>
            {
                instruction.B += 255;
                instruction.C += 255;
            }),
            ["919033"] = (OpCode.NewTable, null),
            ["909190911591990"] = (OpCode.Self, instruction => instruction.C += 255),
            ["90919091159199190"] = (OpCode.Self, null),
            ["91901591909190"] = (OpCode.Add, null),
            ["919015919090"] = (OpCode.Add, instruction => instruction.C += 255),
            ["919015909190"] = (OpCode.Add, instruction => instruction.B += 255),
            ["9190159090"] = (OpCode.Add, instruction =>
            {
                instruction.B += 255;
                instruction.C += 255;
            }),
            ["91901691909190"] = (OpCode.Sub, null),
            ["919016919090"] = (OpCode.Sub, instruction => instruction.C += 255),
            ["919016909190"] = (OpCode.Sub, instruction => instruction.B += 255),
            ["9190169090"] = (OpCode.Sub, instruction =>
            {
                instruction.B += 255;
                instruction.C += 255;
            }),
            ["91901791909190"] = (OpCode.Mul, null),
            ["919017919090"] = (OpCode.Mul, instruction => instruction.C += 255),
            ["919017909190"] = (OpCode.Mul, instruction => instruction.B += 255),
            ["9190179090"] = (OpCode.Mul, instruction =>
            {
                instruction.B += 255;
                instruction.C += 255;
            }),
            ["91901891909190"] = (OpCode.Div, null),
            ["919018919090"] = (OpCode.Div, instruction => instruction.C += 255),
            ["919018909190"] = (OpCode.Div, instruction => instruction.B += 255),
            ["9190189090"] = (OpCode.Div, instruction =>
            {
                instruction.B += 255;
                instruction.C += 255;
            }),
            ["91901991909190"] = (OpCode.Mod, null),
            ["919019919090"] = (OpCode.Mod, instruction => instruction.C += 255),
            ["919019909190"] = (OpCode.Mod, instruction => instruction.B += 255),
            ["9190199090"] = (OpCode.Mod, instruction =>
            {
                instruction.B += 255;
                instruction.C += 255;
            }),
            ["91902091909190"] = (OpCode.Pow, null),
            ["919020919090"] = (OpCode.Pow, instruction => instruction.C += 255),
            ["919020909190"] = (OpCode.Pow, instruction => instruction.B += 255),
            ["9190209090"] = (OpCode.Pow, instruction =>
            {
                instruction.B += 255;
                instruction.C += 255;
            }),
            ["9190319190"] = (OpCode.Unm, null),
            ["9190349190"] = (OpCode.Not, null),
            ["9190289190"] = (OpCode.Len, null),
            ["909113159032919190"] = (OpCode.Concat, null),
            ["2990"] = (OpCode.Jmp, instruction => instruction.B -= instruction.PC + 1),
            ["101225919091902915292990"] = (OpCode.Eq, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 0;
            }),
            ["1012259190902915292990"] = (OpCode.Eq, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 0;
                instruction.C += 255;
            }),
            ["1012259091902915292990"] = (OpCode.Eq, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 0;
            }),
            ["10122590902915292990"] = (OpCode.Eq, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 0;
                instruction.C += 255;
            }),
            ["101226919091902915292990"] = (OpCode.Eq, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 1;
            }),
            ["1012269190902915292990"] = (OpCode.Eq, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 1;
                instruction.C += 255;
            }),
            ["1012269091902915292990"] = (OpCode.Eq, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 1;
            }),
            ["10122690902915292990"] = (OpCode.Eq, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 1;
                instruction.C += 255;
            }),
            ["2936352591909190901529"] = (OpCode.Eq, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 1;
            }),
            ["101221919091902915292990"] = (OpCode.Lt, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 0;
            }),
            ["1012219091902915292990"] = (OpCode.Lt, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 0;
            }),
            ["1012219190902915292990"] = (OpCode.Lt, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 0;
                instruction.C += 255;
            }),
            ["10122190902915292990"] = (OpCode.Lt, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 0;
                instruction.C += 255;
            }),
            ["101221919091902990291529"] = (OpCode.Lt, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 1;
            }),
            ["1012219091902990291529"] = (OpCode.Lt, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 1;
            }),
            ["1012219190902990291529"] = (OpCode.Lt, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 1;
                instruction.C += 255;
            }),
            ["10122190902990291529"] = (OpCode.Lt, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 1;
                instruction.C += 255;
            }),
            ["101223919091902915292990"] = (OpCode.Le, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 0;
            }),
            ["1012239091902915292990"] = (OpCode.Le, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 0;
            }),
            ["1012239190902915292990"] = (OpCode.Le, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 0;
                instruction.C += 255;
            }),
            ["10122390902915292990"] = (OpCode.Le, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 0;
                instruction.C += 255;
            }),
            ["101223919091902990291529"] = (OpCode.Le, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 1;
            }),
            ["1012239190902990291529"] = (OpCode.Le, instruction =>
            {
                instruction.B = instruction.A;
                instruction.A = 1;
                instruction.C += 255;
            }),
            ["1012239091902990291529"] = (OpCode.Le, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 1;
            }),
            ["10122390902990291529"] = (OpCode.Le, instruction =>
            {
                instruction.B = instruction.A + 255;
                instruction.A = 1;
                instruction.C += 255;
            }),
            ["101291902915292990"] = (OpCode.Test, instruction =>
            {
                instruction.B = 0;
                instruction.C = 0;
            }),
            ["10123491902915292990"] = (OpCode.Test, instruction =>
            {
                instruction.B = 0;
                instruction.C = 1;
            }),
            ["9190101229152991902990"] = (OpCode.TestSet, instruction =>
            {
                instruction.B = instruction.C;
                instruction.C = 0;
            }),
            ["919010123429152991902990"] = (OpCode.TestSet, instruction =>
            {
                instruction.B = instruction.C;
                instruction.C = 1;
            }),
            ["149190"] = (OpCode.Call, null),
            ["909114919115"] = (OpCode.Call, null),
            ["9091149114511590"] = (OpCode.Call, instruction => instruction.B -= instruction.A - 1),
            ["9014919115"] = (OpCode.Call, null),
            ["90149114511590"] = (OpCode.Call, instruction => instruction.B -= instruction.A - 1),
            ["9091149114511530"] = (OpCode.Call, null),
            ["903314919115139015919"] = (OpCode.Call, instruction => instruction.C -= instruction.A - 2),
            ["90911491"] = (OpCode.Call, null),
            ["90141491301615133015919"] = (OpCode.Call, null),
            ["901414919115301615133015919"] = (OpCode.Call, instruction => instruction.B -= instruction.A - 1),
            ["9014149114511590301615133015919"] = (OpCode.Call, instruction => instruction.B -= instruction.A - 1),
            ["90149114511530"] = (OpCode.Call, null),
            ["9033149114511590139015919"] = (OpCode.Call, instruction =>
            {
                instruction.B -= instruction.A - 1;
                instruction.C -= instruction.A - 2;
            }),
            ["9033149114511530139015919"] = (OpCode.Call, instruction => instruction.C -= instruction.A - 2),
            ["90331491901315919"] = (OpCode.Call, instruction => instruction.C -= instruction.A - 2),
            ["9014149114511530301615133015919"] = (OpCode.Call, null),
            ["9027149114511590"] = (OpCode.TailCall, instruction => instruction.B -= instruction.A - 1),
            ["9027149114511530"] = (OpCode.TailCall, null),
            ["27149190"] = (OpCode.TailCall, null),
            ["27"] = (OpCode.Return, null),
            ["279190"] = (OpCode.Return, null),
            ["9027145130"] = (OpCode.Return, null),
            ["902714511590"] = (OpCode.Return, instruction => instruction.B += 2),
            ["9027919115"] = (OpCode.Return, null),
            ["909115159191101122102391152990911524911529909115"] = (OpCode.ForLoop, instruction =>
                instruction.B -= instruction.PC + 1),
            ["909191151011122210122291152990911521911529909115"] = (OpCode.ForPrep, instruction =>
                instruction.B -= instruction.PC + 2),
            ["909015331491911591139115991012912990291529"] = (OpCode.TForLoop, instruction => instruction.B = 0),
            ["909113153014691"] = (OpCode.SetList, null),
            ["909113159014691"] = (OpCode.SetList, instruction => instruction.B -= instruction.A),
            ["3313289132899910352512490999"] = (OpCode.Close, null),
            ["990331473333927999999913902915299291012259916331991633299152891901483"] = (OpCode.Closure, null),
            ["91901489903"] = (OpCode.Closure, null),
            ["903016151330941691"] = (OpCode.VarArg, null),
            ["909013919416"] = (OpCode.VarArg, instruction => instruction.B -= instruction.A - 1)
        };
    }
}
