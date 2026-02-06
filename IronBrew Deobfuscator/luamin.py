class Token:
def init(self, type_, leading_white, source):
self.Type = type_
self.LeadingWhite = leading_white
self.Source = source

class ASTNode:
def init(self, type_):
self.Type = type_
self.Token = None
self.GetFirstToken = lambda: None
self.GetLastToken = lambda: None

def Parse(script):
return {
"Type": "Chunk",
"StatementList": []
}

def Beautify(script, options):
return script

def BeautifyAst(ast, options):
return ast

def Print(ast):
return ""

def SolveMath(ast):
pass
