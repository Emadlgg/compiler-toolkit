"""
frontend.py — Análisis léxico y sintáctico de SQL.

    result = parse("SELECT nombre FROM estudiantes WHERE edad >= 18;")
    result.ok                 # True si no hubo errores léxicos ni sintácticos
    result.errors             # lista de SqlError (léxicos primero, luego sintácticos)
    format_tokens(result)     # tabla de tokens
    format_tree(result)       # árbol sintáctico con sangría
"""

import re

from antlr4 import InputStream, CommonTokenStream, Token
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.Errors import NoViableAltException
from antlr4.tree.Tree import TerminalNode, ErrorNode

from sqlengine.generated.SqlLexer import SqlLexer
from sqlengine.generated.SqlParser import SqlParser
from sqlengine.errors import SqlError, LEXICAL, SYNTAX
from sqlengine.treeview import TreeItem, render_text

# Cómo se muestran en los mensajes los tokens que no son una palabra fija
_FRIENDLY = {
    "IDENTIFIER": "un nombre",
    "INTEGER_LITERAL": "un número entero",
    "FLOAT_LITERAL": "un número decimal",
    "STRING_LITERAL": "un texto entre comillas",
    "'<EOF>'": "el final del texto",
    "<EOF>": "el final del texto",
}
_FRIENDLY_RE = re.compile("|".join(re.escape(k) for k in sorted(_FRIENDLY, key=len, reverse=True)))

# Lo que puede empezar una expresión: si el parser lo espera todo junto, se resume en "una expresión"
_EXPRESSION_START = {
    "'NOT'", "'EXISTS'", "'NULL'", "'TRUE'", "'FALSE'", "'COUNT'", "'SUM'", "'AVG'", "'MIN'", "'MAX'",
    "'DATE'", "'+'", "'-'", "'('", "IDENTIFIER", "INTEGER_LITERAL", "FLOAT_LITERAL", "STRING_LITERAL",
}
# Palabras reservadas que es fácil querer usar como nombre de columna o de tabla
_EASY_TO_MISUSE = {"DATE", "INT", "FLOAT", "BOOLEAN", "VARCHAR", "COUNT", "SUM", "AVG", "MIN", "MAX", "KEY"}
_MAX_EXPECTED = 6


def _friendly(text):
    return _FRIENDLY_RE.sub(lambda m: _FRIENDLY[m.group(0)], text)


def _expected(text):
    """Convierte lo que esperaba el parser ({'A', B, ...}) en una lista legible: «A, B o C»."""
    inner = text[1:-1] if text.startswith("{") and text.endswith("}") else text
    items = inner.split(", ")
    if {"IDENTIFIER", "INTEGER_LITERAL", "'('"} <= set(items):
        items = ["una expresión"] + [i for i in items if i not in _EXPRESSION_START]
    shown = [_friendly(i) for i in items[:_MAX_EXPECTED]]
    if len(items) > _MAX_EXPECTED:
        shown.append("otras opciones")
    return shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + " o " + shown[-1]


_AGGREGATES = {"COUNT", "SUM", "AVG", "MIN", "MAX"}


def _misused_reserved_word(fragment):
    """
    Una palabra reservada que parece estar usándose como nombre. No cuenta si es
    legítima: una función seguida de '(' o `DATE 'texto'`.
    """
    for i, token in enumerate(fragment):
        if token.text.upper() not in _EASY_TO_MISUSE:
            continue
        following = fragment[i + 1] if i + 1 < len(fragment) else None
        if following is None:
            if token.text.upper() not in _AGGREGATES:
                return token.text
        elif following.text != "(" and following.type != SqlLexer.STRING_LITERAL:
            return token.text
    return None


def _lexical_message(msg, offending, e, recognizer):
    # ANTLR: token recognition error at: '<texto>'
    m = re.match(r"token recognition error at: '(.*)'$", msg, re.S)
    text = m.group(1) if m else msg
    if text.startswith("'"):
        return "Cadena de texto sin cerrar: falta la comilla de cierre (')", None, None
    return f"Carácter o símbolo no reconocido: '{text}'", None, None


def _syntax_message(msg, offending, e, recognizer):
    """Devuelve (mensaje, línea, columna); línea y columna en None significan «donde ANTLR lo detectó»."""
    if isinstance(e, NoViableAltException) and e.startToken is not None:
        # ANTLR no sabe qué esperaba: se muestra el fragmento problemático, empezando donde empieza
        stream = recognizer.getTokenStream()
        start, end = e.startToken, e.offendingToken
        fragment = [stream.get(i) for i in range(start.tokenIndex, end.tokenIndex + 1) if stream.get(i).type != Token.EOF]
        text = " ".join(t.text for t in fragment)
        first = fragment[0]
        # una función de agregación mal usada: SUM(*), COUNT(a, b)...
        if first.text.upper() in _AGGREGATES and len(fragment) > 1 and fragment[1].text == "(":
            func = first.text.upper()
            message = f"Llamada no válida a {func}: {func} recibe una sola expresión entre paréntesis"
            if func != "COUNT" and len(fragment) > 2 and fragment[2].text == "*":
                message += " (solo COUNT acepta *)"
            return message, start.line, start.column

        message = f"No se pudo interpretar la sentencia cerca de '{text}'"
        if start.type in (SqlLexer.DROP, SqlLexer.CREATE):
            message += f". Después de {start.text.upper()} se esperaba TABLE o INDEX"
        misused = _misused_reserved_word(fragment)
        if misused:
            message += (f". ¿Usaste la palabra reservada '{misused}' como nombre? "
                        "Las palabras reservadas no se pueden usar como nombres de tablas, columnas o alias")
        return message, start.line, start.column

    found = _friendly(offending.text if offending is not None and offending.type != Token.EOF else "<EOF>")
    if found != "el final del texto":
        found = f"'{found}'"
    rules = [
        (r"^mismatched input .+? expecting (.+)$", lambda m: f"Se encontró {found} pero se esperaba {_expected(m.group(1))}"),
        (r"^extraneous input .+? expecting (.+)$", lambda m: f"Sobra {found}; se esperaba {_expected(m.group(1))}"),
        (r"^missing (.+?) at .+$", lambda m: f"Falta {_friendly(m.group(1))} antes de {found}"),
    ]
    for pattern, build in rules:
        m = re.match(pattern, msg, re.S)
        if m:
            return build(m), None, None
    return _friendly(msg), None, None


class _Collector(ErrorListener):
    def __init__(self, kind, translate):
        super().__init__()
        self.kind = kind
        self.translate = translate
        self.errors = []

    def syntaxError(self, recognizer, offending, line, column, msg, e):
        message, at_line, at_column = self.translate(msg, offending, e, recognizer)
        self.errors.append(SqlError(self.kind, message, at_line or line, column if at_column is None else at_column))


class ParseResult:
    def __init__(self, text, tokens, tree, parser, lexical_errors, syntax_errors):
        self.text = text
        self.tokens = tokens                  # [(tipo, texto, línea, columna)]
        self.tree = tree
        self.parser = parser
        self.lexical_errors = lexical_errors
        self.syntax_errors = syntax_errors

    @property
    def errors(self):
        return self.lexical_errors + self.syntax_errors

    @property
    def ok(self):
        return not self.errors

    def statements(self):
        """Sentencias del script (cada una es un contexto del árbol)."""
        return self.tree.statement() if self.tree is not None else []


def _token_info(token):
    name = "EOF" if token.type == Token.EOF else SqlLexer.symbolicNames[token.type]
    return (name, token.text, token.line, token.column)


def parse(text):
    """Analiza un script SQL. Siempre devuelve un resultado; los problemas van en `errors`."""
    lexer = SqlLexer(InputStream(text))
    lexical = _Collector(LEXICAL, _lexical_message)
    lexer.removeErrorListeners()
    lexer.addErrorListener(lexical)

    stream = CommonTokenStream(lexer)
    stream.fill()
    tokens = [_token_info(t) for t in stream.tokens]

    parser = SqlParser(stream)
    syntax = _Collector(SYNTAX, _syntax_message)
    parser.removeErrorListeners()
    parser.addErrorListener(syntax)
    tree = parser.script()
    return ParseResult(text, tokens, tree, parser, lexical.errors, syntax.errors)


def format_tokens(result):
    """Tabla de tokens: ubicación, tipo y texto."""
    lines = [f"{'UBICACIÓN':<11}{'TIPO':<18}TEXTO", "-" * 48]
    for name, text, line, column in result.tokens:
        if name == "EOF":
            continue
        lines.append(f"{line}:{column:<9}{name:<18}{text}")
    return "\n".join(lines)


# Reglas que solo existen para fijar la precedencia de los operadores: cuando tienen un único
# hijo no aportan nada al leer el árbol, así que la vista compacta las salta.
_PASS_THROUGH = {
    "expr", "orExpr", "andExpr", "notExpr", "additive", "multiplicative", "unary",
    "predicate", "primary",
}


def parse_tree_item(result, compact=True):
    """
    El árbol sintáctico como TreeItem: reglas del parser y tokens en las hojas.
    Con compact=True se omiten las capas de precedencia de las expresiones.
    """
    parser = result.parser

    def label(ctx):
        rule = parser.ruleNames[ctx.getRuleIndex()]
        name = type(ctx).__name__[:-len("Context")]
        return rule if name == rule[0].upper() + rule[1:] else f"{rule} #{name[0].lower() + name[1:]}"

    def build(node):
        if isinstance(node, ErrorNode):
            return TreeItem(f"<error> '{node.getText()}'", "leaf")
        if isinstance(node, TerminalNode):
            token = node.symbol
            name = "EOF" if token.type == Token.EOF else SqlLexer.symbolicNames[token.type]
            return TreeItem(f"{name} '{token.text}'", "leaf")
        children = [build(c) for c in node.getChildren()]
        skip = (compact and parser.ruleNames[node.getRuleIndex()] in _PASS_THROUGH
                and node.getChildCount() == 1 and not isinstance(node.getChild(0), TerminalNode))
        if skip:
            return children[0]
        return TreeItem(label(node), "node", children)

    return build(result.tree)


def format_tree(result, compact=True):
    """Árbol sintáctico con sangría (ver parse_tree_item)."""
    return render_text(parse_tree_item(result, compact))
