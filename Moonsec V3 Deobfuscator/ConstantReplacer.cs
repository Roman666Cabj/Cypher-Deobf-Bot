using MoonsecDeobfuscator.Ast;
using MoonsecDeobfuscator.Ast.Expressions;
using MoonsecDeobfuscator.Ast.Literals;

namespace MoonsecDeobfuscator.Deobfuscation.Rewriters
{
    public class ConstantReplacer(Dictionary<string, string[]> constants) : AstRewriter
    {
        public override Node Visit(MemberAccess node) =>
            constants.TryGetValue(node.Key.Value, out var values) ? CreateReplacement(values) : node;

        private static Expression CreateReplacement(string[] values)
        {
            if (int.TryParse(values[0], out var result))
                return new NumberLiteral(result);
            Expression name = new Name(values[0]);
            return values
                .Skip(1)
                .Aggregate(name, (acc, str) => new MemberAccess(acc, new Name(str)));
        }
    }
}

ConstantFolder.cs
using MoonsecDeobfuscator.Ast;
using MoonsecDeobfuscator.Ast.Expressions;
using MoonsecDeobfuscator.Ast.Literals;

namespace MoonsecDeobfuscator.Deobfuscation.Rewriters
{
    public class ConstantFolder : AstRewriter
    {
        private static Expression FoldUnaryExpression(UnaryExpression node)
        {
            if (CanFoldTableLen(node))
                return FoldTableLen(node);
            if (CanFoldNegation(node))
                return FoldNegation(node);
            return node;
        }

        private static NumberLiteral FoldTableLen(UnaryExpression node) => new(((Table)node.Operand).Entries.Count);

        private static bool CanFoldTableLen(UnaryExpression node)
        {
            return node is { Operator: UnaryOperator.Length, Operand: Table table }
                && table.Entries.All(entry => entry.Key == null && entry.Value is Literal and not Nil);
        }

        private static NumberLiteral FoldNegation(UnaryExpression node) => new(-((NumberLiteral)node.Operand).Value);

        private static bool CanFoldNegation(UnaryExpression node) =>
            node is { Operator: UnaryOperator.Negate, Operand: NumberLiteral };

        private static BinaryExpression NormalizeComparison(BinaryExpression node)
        {
            if (node is not { Left: NumberLiteral, Right: not NumberLiteral })
                return node;
            switch (node.Operator)
            {
                case BinaryOperator.Equals:
                case BinaryOperator.NotEquals:
                    (node.Left, node.Right) = (node.Right, node.Left);
                    break;
                case BinaryOperator.LessThan:
                    node.Operator = BinaryOperator.GreaterThan;
                    (node.Left, node.Right) = (node.Right, node.Left);
                    break;
                case BinaryOperator.GreaterThan:
                    node.Operator = BinaryOperator.LessThan;
                    (node.Left, node.Right) = (node.Right, node.Left);
                    break;
                case BinaryOperator.LessThanOrEquals:
                    node.Operator = BinaryOperator.GreaterThanOrEquals;
                    (node.Left, node.Right) = (node.Right, node.Left);
                    break;
                case BinaryOperator.GreaterThanOrEquals:
                    node.Operator = BinaryOperator.LessThanOrEquals;
                    (node.Left, node.Right) = (node.Right, node.Left);
                    break;
            }
            return node;
        }

        public override Node Visit(BinaryExpression node) => NormalizeComparison(node);
        public override Node Visit(UnaryExpression node) => FoldUnaryExpression(node);
    }
}
