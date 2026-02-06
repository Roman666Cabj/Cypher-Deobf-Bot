using MoonsecDeobfuscator.Ast;
using MoonsecDeobfuscator.Ast.Expressions;
using MoonsecDeobfuscator.Ast.Statements;

namespace MoonsecDeobfuscator.Deobfuscation.Rewriters
{
    public class HandlerRewriter : AstRewriter
    {
        public override Node Visit(Call node)
        {
            var args = node.Arguments;
            if (node.Function is Name { Value: "stk" } && args is [Name name1, Name name2])
            {
                var newArg1 = ReplaceWithElementAccess(name1);
                var newArg2 = ReplaceWithElementAccess(name2);
                if (name1 != newArg1 || name2 != newArg2)
                    return new Call(node.Function, [newArg1, newArg2]);
            }
            return node;
        }

        public override Node Visit(ElementAccess node)
        {
            var newTable = ReplaceWithName(node.Table);
            var newKey = ReplaceWithName(node.Key);
            if (node.Table != newTable || node.Key != newKey)
                return new ElementAccess(newTable, newKey);
            newKey = ReplaceWithElementAccess(node.Key);
            if (node.Key != newKey)
                return new ElementAccess(newTable, newKey);
            return node;
        }

        public override Node Visit(Block node)
        {
            var unused = node.Statements
                .Where(stat => stat is LocalDeclare decl && ShouldRemoveDeclaration(decl))
                .ToHashSet();
            if (unused.Count > 0)
            {
                node.Statements.RemoveAll(stat => unused.Contains(stat));
                return new Block(node.Statements);
            }
            return node;
        }

        public override Node Visit(Assign node)
        {
            if (ShouldLocalizeAssignment(node))
            {
                var names = new NodeList<Name>(node.Variables.Select(name => (Name)name));
                return new LocalDeclare(names, node.Values);
            }
            if (node is { Variables: [ElementAccess], Values: [Name name] })
            {
                var replacement = ReplaceWithElementAccess(name);
                if (replacement != name)
                    return new Assign(node.Variables, [replacement]);
            }
            if (node is { Variables: [Name], Values: [Name name1] })
            {
                var newValue = ReplaceWithBinaryExpression(name1);
                if (name1 != newValue)
                    return new Assign(node.Variables, [newValue]);
            }
            return node;
        }

        public override Node Visit(BinaryExpression node)
        {
            var newLeft = ReplaceWithElementAccess(node.Left);
            var newRight = ReplaceWithElementAccess(node.Right);
            if (node.Left != newLeft || node.Right != newRight)
                return new BinaryExpression(node.Operator, newLeft, newRight);
            newLeft = ReplaceWithName(node.Left);
            newRight = ReplaceWithName(node.Right);
            if (node.Left != newLeft || node.Right != newRight)
                return new BinaryExpression(node.Operator, newLeft, newRight);
            return node;
        }

        private bool ShouldRemoveDeclaration(LocalDeclare node)
        {
            if (node.Values.Count == 0)
                return true;
            foreach (var name in node.Names)
            {
                var info = GetVariable(name.Value);
                if (info is { ReadCount: > 0 })
                    return false;
            }
            return true;
        }

        private bool ShouldLocalizeAssignment(Assign node)
        {
            foreach (var variable in node.Variables)
            {
                if (variable is not Name name)
                    return false;
                var value = name.Value;
                if (!value.StartsWith(''))
                    return false;
                if (GetVariable(value)!.DeclarationLocation != node)
                    return false;
            }
            return true;
        }

        private Expression ReplaceWithName(Expression node)
        {
            if (node is not Name name || !name.Value.StartsWith(''))
                return node;
            return GetVariable(name.Value) is { Value: Name } info
                ? info.Value.Clone()
                : node;
        }

        private Expression ReplaceWithElementAccess(Expression node)
        {
            if (node is not Name name || !name.Value.StartsWith(''))
                return node;
            return GetVariable(name.Value) is { Value: ElementAccess { Table: Name, Key: Name }, ReadCount: 1 } info
                ? info.Value.Clone()
                : node;
        }

        private Expression ReplaceWithBinaryExpression(Expression node)
        {
            if (node is not Name name || !name.Value.StartsWith(''))
                return node;
            return GetVariable(name.Value) is { Value: BinaryExpression, ReadCount: 1, AssignmentCount: 0 } info
                ? info.Value.Clone()
                : node;
        }
    }
}
