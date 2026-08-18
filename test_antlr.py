import sys
sys.path.insert(0, "compiscript/generated")

from antlr4 import CommonTokenStream, InputStream
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser

code = '''
let x: integer = 10;
let y: string = "hola";
function suma(a: integer, b: integer): integer {
    return a + b;
}
'''

stream = InputStream(code)
lexer  = CompiscriptLexer(stream)
tokens = CommonTokenStream(lexer)
parser = CompiscriptParser(tokens)
tree   = parser.program()
print("Parser OK")
print(tree.toStringTree(recog=parser)[:300])