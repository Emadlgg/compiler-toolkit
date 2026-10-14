"""
codegen.py — Generador de código intermedio (TAC) para Compiscript.

Recorre el árbol sintáctico ya validado por el análisis semántico y produce
código de tres direcciones. Para decidir tipos, símbolos y offsets no vuelve a
analizar nada: consulta lo que el SemanticAnalyzer dejó anotado
(node_types, node_symbols, node_scopes) y los campos de generación de código
de la tabla de símbolos (storage, offset, size, label, depth).

Uso:
    generator = CodeGenerator(analyzer)
    instructions = generator.generate(tree)
    print(generator.format())            # TAC
    print(generator.memory_report())     # registros de activación y layouts
    generator.errors                     # construcciones no soportadas

Decisiones de traducción (detalle en docs/CI.md):
  * Una condición (if, while, for, do-while, ?:) se traduce con saltos y
    cortocircuito; &&, || y ! solo producen un valor 0/1 cuando se usan como dato.
  * Los argumentos se evalúan todos antes de emitir los `param`.
  * Un temporal se libera apenas se consume; el resultado de una instrucción
    puede reutilizar el temporal de uno de sus operandos.
  * Las funciones no se emiten en el punto de su declaración: cada una es un
    bloque aparte y el código global va en `main`.
"""

from antlr4 import *

from compiscript.generated.CompiscriptVisitor import CompiscriptVisitor
from compiscript.generated.CompiscriptParser import CompiscriptParser as P

from compiscript.symbol_table import Type, WORD, FRAME_HEADER
from compiscript.errors import CodegenError
from compiscript.semantic import for_parts
from compiscript.temps import TempPool
from compiscript.activation_record import ActivationRecord, full_report
from compiscript.tac import (
    Temp, Const, Var,
    Copy, Binary, Unary, Label, Goto, IfGoto, IfRel, Param, Call, Return,
    LoadIndex, StoreIndex, LoadField, StoreField, New, NewArray, Len,
    FuncBegin, Enter, Halt, RETARGETABLE,
    format_program, safe_name,
)

NEGATED = {"==": "!=", "!=": "==", "<": ">=", "<=": ">", ">": "<=", ">=": "<"}
COMPARISONS = {"==", "!=", "<", "<=", ">", ">="}


class FuncContext:
    """Estado de generación de una función (o del programa principal)."""

    def __init__(self, label, depth, scope=None, has_this=False):
        self.label = label
        self.depth = depth          # nivel léxico de su registro de activación
        self.scope = scope
        self.has_this = has_this
        self.parent = None
        self.temps = TempPool()
        self.loops = []             # pila de (etiqueta de continue | None, etiqueta de break)
        self.begin = FuncBegin(label, depth)
        self.enter = Enter(0)
        self.code = [self.begin, self.enter]
        self.record = None


class CodeGenerator(CompiscriptVisitor):

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.table = analyzer.table
        self.types = analyzer.node_types
        self.symbols = analyzer.node_symbols
        self.scopes = analyzer.node_scopes
        self.errors = []
        self.instructions = []
        self.records = []
        self.functions = []
        self.fctx = None
        self._label_count = 0
        self._names = {}
        self._name_count = {}
        self.own_init = {}          # clase -> etiqueta de la función que inicializa sus atributos
        self.classes = {}
        for scope in self.table.all_scopes:
            if scope.kind == "class" and scope.class_symbol is not None:
                self.classes[scope.class_symbol.name] = scope.class_symbol

    # ── API ───────────────────────────────────────────────

    def generate(self, tree):
        """Genera el TAC de todo el programa y lo retorna como lista de instrucciones."""
        entry = "main" if "main" not in self.table._labels else "_start"
        main = FuncContext(entry, 0, self.table.global_scope)
        self.functions = [main]
        self.fctx = main
        self.visit(tree)
        self.emit(Halt())
        self._finish(main, FRAME_HEADER)
        self.instructions = []
        for fctx in self.functions:
            self.instructions.extend(fctx.code)
        self.records = [f.record for f in self.functions if f.record is not None]
        return self.instructions

    def format(self):
        return format_program(self.instructions)

    def memory_report(self):
        return full_report(self.table, self.records)

    # ── Utilidades ────────────────────────────────────────

    def emit(self, instr):
        self.fctx.code.append(instr)
        return instr

    def emit_goto(self, label):
        """Salto incondicional, omitido si la instrucción anterior ya salta o retorna."""
        last = self.fctx.code[-1]
        if isinstance(last, (Goto, Return)):
            return
        self.emit(Goto(label))

    def new_label(self):
        self._label_count += 1
        return f"L{self._label_count}"

    def new_temp(self):
        return self.fctx.temps.new()

    def release(self, *operands):
        for operand in operands:
            self.fctx.temps.free(operand)

    def error(self, message, ctx):
        self.errors.append(CodegenError(message, ctx.start.line, ctx.start.column))

    def assign_to(self, target, value):
        """
        Copia `value` en `target`. Si `value` es un temporal que acaba de calcular
        la instrucción anterior, la redirige a `target` en vez de emitir una copia:
        `t0 = x + 1; x = t0` queda como `x = x + 1`.
        """
        last = self.fctx.code[-1]
        if (isinstance(value, Temp) and isinstance(last, RETARGETABLE)
                and last.dest == value and value != target):
            last.dest = target
            self.release(value)
            return
        if value == target:
            return
        self.emit(Copy(target, value))
        self.release(value)

    # ── Variables ─────────────────────────────────────────

    def _name_of(self, sym, owner):
        key = (owner, sym.name, sym.offset)
        if key not in self._names:
            count = self._name_count.get((owner, sym.name), 0) + 1
            self._name_count[(owner, sym.name)] = count
            base = safe_name(sym.name)
            self._names[key] = base if count == 1 else f"{base}_{count}"
        return self._names[key]

    def var_operand(self, sym):
        """Operando de una variable global, local o parámetro (x o x@k)."""
        if sym.storage == "global":
            return Var(self._name_of(sym, "global"), sym, 0)
        hops = self.fctx.depth - sym.depth
        owner = self.fctx
        for _ in range(hops):
            owner = owner.parent
        return Var(self._name_of(sym, owner.label), sym, hops)

    def this_operand(self):
        ctx = self.fctx
        while ctx is not None and not ctx.has_this:
            ctx = ctx.parent
        hops = self.fctx.depth - ctx.depth if ctx is not None else 0
        return Var("this", None, hops)

    # ── Funciones ─────────────────────────────────────────

    @staticmethod
    def _remove_unreachable(code):
        """Quita lo que queda después de un goto, return o halt hasta la siguiente etiqueta."""
        out = []
        dead = False
        for ins in code:
            if isinstance(ins, Label):
                dead = False
            if dead:
                continue
            out.append(ins)
            if isinstance(ins, (Goto, Return, Halt)):
                dead = True
        return out

    @staticmethod
    def _simplify_jumps(code):
        """
        Dos simplificaciones de saltos:
          if c goto La; goto Lb; La:   ->  if !c goto Lb; La:
          goto L; L:                   ->  L:
        """
        changed = True
        while changed:
            changed = False
            out = []
            i = 0
            while i < len(code):
                ins = code[i]
                nxt = code[i + 1] if i + 1 < len(code) else None
                after = code[i + 2] if i + 2 < len(code) else None
                if (isinstance(ins, (IfRel, IfGoto)) and isinstance(nxt, Goto)
                        and isinstance(after, Label) and after.name == ins.label):
                    if isinstance(ins, IfRel):
                        ins = IfRel(ins.left, NEGATED[ins.op], ins.right, nxt.label)
                    else:
                        ins = IfGoto(ins.cond, nxt.label, not ins.negate)
                    out.append(ins)
                    i += 2
                    changed = True
                    continue
                if isinstance(ins, Goto) and isinstance(nxt, Label) and nxt.name == ins.label:
                    i += 1
                    changed = True
                    continue
                out.append(ins)
                i += 1
            code = out
        return code

    def _finish(self, fctx, base_size):
        """Cierra una función: quita código inalcanzable, simplifica saltos, quita etiquetas sin uso y fija el tamaño del registro."""
        # cada limpieza puede dejar a la vista trabajo para las otras: se repite hasta que nada cambie
        code = fctx.code
        while True:
            before = len(code)
            code = self._simplify_jumps(self._remove_unreachable(code))
            used = {i.label for i in code if isinstance(i, (Goto, IfGoto, IfRel))}
            code = [i for i in code if not (isinstance(i, Label) and i.name not in used)]
            if len(code) == before:
                break
        fctx.code = code
        size = base_size + fctx.temps.count * WORD
        fctx.enter.size = size
        fctx.begin.size = size
        if fctx.scope is not None and fctx.scope.kind == "function":
            fctx.record = ActivationRecord.from_scope(fctx.label, fctx.scope, fctx.temps.count)
        elif fctx.has_this:
            fctx.record = ActivationRecord.synthetic(fctx.label, fctx.depth, ["this"], fctx.temps.count)
        else:
            fctx.record = ActivationRecord.synthetic(fctx.label, fctx.depth, [], fctx.temps.count)

    def _enter_function(self, label, depth, scope, has_this):
        fctx = FuncContext(label, depth, scope, has_this)
        fctx.parent = self.fctx
        self.functions.append(fctx)
        self.fctx = fctx
        return fctx

    def _gen_function(self, label, scope, block, has_this):
        fctx = self._enter_function(label, scope.depth, scope, has_this)
        self.visit(block)
        if not isinstance(fctx.code[-1], Return):
            self.emit(Return())
        self._finish(fctx, scope.frame_size)
        self.fctx = fctx.parent

    def visitFunctionDeclaration(self, ctx):
        sym = self.symbols.get(ctx)
        scope = self.scopes.get(ctx)
        if sym is None or scope is None:
            self.error("No se pudo resolver la función", ctx)
            return None
        self._gen_function(sym.label, scope, ctx.block(), sym.storage == "method")
        return None

    def _gen_init(self, label, class_scope, inits):
        """Función que asigna los valores iniciales de los atributos de una clase."""
        fctx = self._enter_function(label, class_scope.depth + 1, None, True)
        this = Var("this", None, 0)
        for field, expr in inits:
            value = self.visit(expr)
            self.emit(StoreField(this, field.name, field.offset, value))
            self.release(value)
        self.emit(Return())
        self._finish(fctx, FRAME_HEADER + WORD)
        self.fctx = fctx.parent

    def visitClassDeclaration(self, ctx):
        sym = self.symbols.get(ctx)
        scope = self.scopes.get(ctx)
        if sym is None or scope is None:
            self.error("No se pudo resolver la clase", ctx)
            return None
        inits = []
        for member in ctx.classMember():
            decl = member.variableDeclaration()
            expr = None
            if decl is not None:
                if decl.initializer() is not None:
                    expr = decl.initializer().expression()
            else:
                decl = member.constantDeclaration()
                if decl is not None:
                    expr = decl.expression()
            if decl is not None and expr is not None:
                inits.append((self.symbols.get(decl), expr))
        label = None
        if inits:
            label = f"{sym.name}__init"
            while label in self.table._labels:
                label += "_"
            self.table._labels.add(label)
            self.own_init[sym.name] = label
        for member in ctx.classMember():
            if member.functionDeclaration() is not None:
                self.visit(member.functionDeclaration())
        if inits:
            self._gen_init(label, scope, inits)
        return None

    # ── Programa y sentencias ─────────────────────────────

    def visitProgram(self, ctx):
        for stmt in ctx.statement():
            self.visit(stmt)

    def visitStatement(self, ctx):
        for child in ctx.getChildren():
            child.accept(self)

    def visitBlock(self, ctx):
        for stmt in ctx.statement():
            self.visit(stmt)

    def visitVariableDeclaration(self, ctx):
        sym = self.symbols.get(ctx)
        if sym is None or sym.storage == "field":
            return
        if ctx.initializer() is not None:
            value = self.visit(ctx.initializer().expression())
            self.assign_to(self.var_operand(sym), value)

    def visitConstantDeclaration(self, ctx):
        sym = self.symbols.get(ctx)
        if sym is None or sym.storage == "field":
            return
        value = self.visit(ctx.expression())
        self.assign_to(self.var_operand(sym), value)

    def visitAssignment(self, ctx):
        if ctx.getChildCount() == 4:
            sym = self.symbols.get(ctx)
            value = self.visit(ctx.expression(0))
            self._store_variable(sym, value)
            self.release(value)
            return
        expressions = ctx.expression()
        member = self.symbols.get(ctx)
        obj = self.visit(expressions[0])
        value = self.visit(expressions[1])
        if member is None:
            self.error("No se pudo resolver el atributo", ctx)
        else:
            self.emit(StoreField(obj, member.name, member.offset, value))
        self.release(obj, value)

    def _store_variable(self, sym, value):
        """Escribe `value` en la variable `sym` y retorna el operando destino."""
        if sym.storage == "field":
            this = self.this_operand()
            self.emit(StoreField(this, sym.name, sym.offset, value))
            return value
        target = self.var_operand(sym)
        self.assign_to(target, value)
        return target

    def visitExpressionStatement(self, ctx):
        self.release(self.visit(ctx.expression()))

    def visitPrintStatement(self, ctx):
        value = self.visit(ctx.expression())
        self.emit(Param(value))
        self.emit(Call(None, "print", 1))
        self.release(value)

    def visitReturnStatement(self, ctx):
        if ctx.expression() is None:
            self.emit(Return())
            return
        value = self.visit(ctx.expression())
        self.emit(Return(value))
        self.release(value)

    def visitBreakStatement(self, ctx):
        if not self.fctx.loops:
            self.error("break fuera de un bucle o switch", ctx)
            return
        self.emit_goto(self.fctx.loops[-1][1])

    def visitContinueStatement(self, ctx):
        for cont, _ in reversed(self.fctx.loops):
            if cont is not None:
                self.emit_goto(cont)
                return
        self.error("continue fuera de un bucle", ctx)

    def visitTryCatchStatement(self, ctx):
        self.error("try/catch no está soportado por el generador de código intermedio", ctx)

    # ── Control de flujo ──────────────────────────────────

    def visitIfStatement(self, ctx):
        blocks = ctx.block()
        l_end = self.new_label()
        if len(blocks) == 2:
            l_else = self.new_label()
            self.jump_false(ctx.expression(), l_else)
            self.visit(blocks[0])
            self.emit_goto(l_end)
            self.emit(Label(l_else))
            self.visit(blocks[1])
        else:
            self.jump_false(ctx.expression(), l_end)
            self.visit(blocks[0])
        self.emit(Label(l_end))

    def visitWhileStatement(self, ctx):
        l_start, l_end = self.new_label(), self.new_label()
        self.emit(Label(l_start))
        self.jump_false(ctx.expression(), l_end)
        self.fctx.loops.append((l_start, l_end))
        self.visit(ctx.block())
        self.fctx.loops.pop()
        self.emit_goto(l_start)
        self.emit(Label(l_end))

    def visitDoWhileStatement(self, ctx):
        l_body, l_cond, l_end = self.new_label(), self.new_label(), self.new_label()
        self.emit(Label(l_body))
        self.fctx.loops.append((l_cond, l_end))
        self.visit(ctx.block())
        self.fctx.loops.pop()
        self.emit(Label(l_cond))
        self.jump_true(ctx.expression(), l_body)
        self.emit(Label(l_end))

    def visitForStatement(self, ctx):
        if ctx.variableDeclaration() is not None:
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment() is not None:
            self.visit(ctx.assignment())
        cond, update = for_parts(ctx)
        l_cond, l_update, l_end = self.new_label(), self.new_label(), self.new_label()
        self.emit(Label(l_cond))
        if cond is not None:
            self.jump_false(cond, l_end)
        self.fctx.loops.append((l_update, l_end))
        self.visit(ctx.block())
        self.fctx.loops.pop()
        self.emit(Label(l_update))
        if update is not None:
            self.release(self.visit(update))
        self.emit_goto(l_cond)
        self.emit(Label(l_end))

    def visitForeachStatement(self, ctx):
        sym = self.symbols.get(ctx)
        if sym is None:
            self.error("No se pudo resolver la variable del foreach", ctx)
            return
        source = self.visit(ctx.expression())
        # la lista, su largo y el índice viven durante todo el bucle: no se reciclan
        if isinstance(source, Temp):
            array = source
        else:
            array = self.new_temp()
            self.emit(Copy(array, source))
        length = self.new_temp()
        self.emit(Len(length, array))
        index = self.new_temp()
        self.emit(Copy(index, Const(0)))
        l_cond, l_next, l_end = self.new_label(), self.new_label(), self.new_label()
        self.emit(Label(l_cond))
        self.emit(IfRel(index, ">=", length, l_end))
        self.emit(LoadIndex(self.var_operand(sym), array, index))
        self.fctx.loops.append((l_next, l_end))
        self.visit(ctx.block())
        self.fctx.loops.pop()
        self.emit(Label(l_next))
        self.emit(Binary(index, "+", index, Const(1)))
        self.emit_goto(l_cond)
        self.emit(Label(l_end))
        self.release(array, length, index)

    def visitSwitchStatement(self, ctx):
        value = self.visit(ctx.expression())
        cases = ctx.switchCase()
        default = ctx.defaultCase()
        l_end = self.new_label()
        case_labels = [self.new_label() for _ in cases]
        l_default = self.new_label() if default is not None else None
        for case, label in zip(cases, case_labels):
            candidate = self.visit(case.expression())
            self.emit(IfRel(value, "==", candidate, label))
            self.release(candidate)
        self.emit_goto(l_default if l_default else l_end)
        self.release(value)
        self.fctx.loops.append((None, l_end))
        for case, label in zip(cases, case_labels):
            self.emit(Label(label))
            for stmt in case.statement():
                self.visit(stmt)
        if default is not None:
            self.emit(Label(l_default))
            for stmt in default.statement():
                self.visit(stmt)
        self.fctx.loops.pop()
        self.emit(Label(l_end))

    # ── Condiciones con saltos ────────────────────────────

    def _strip(self, node):
        """Quita las capas de la gramática que no hacen nada (un solo operando, paréntesis)."""
        while True:
            if isinstance(node, P.ExpressionContext):
                node = node.assignmentExpr()
            elif isinstance(node, P.ExprNoAssignContext):
                node = node.conditionalExpr()
            elif isinstance(node, P.TernaryExprContext) and not node.expression():
                node = node.logicalOrExpr()
            elif isinstance(node, P.LogicalOrExprContext) and len(node.logicalAndExpr()) == 1:
                node = node.logicalAndExpr(0)
            elif isinstance(node, P.LogicalAndExprContext) and len(node.equalityExpr()) == 1:
                node = node.equalityExpr(0)
            elif isinstance(node, P.EqualityExprContext) and len(node.relationalExpr()) == 1:
                node = node.relationalExpr(0)
            elif isinstance(node, P.RelationalExprContext) and len(node.additiveExpr()) == 1:
                node = node.additiveExpr(0)
            elif isinstance(node, P.AdditiveExprContext) and len(node.multiplicativeExpr()) == 1:
                node = node.multiplicativeExpr(0)
            elif isinstance(node, P.MultiplicativeExprContext) and len(node.unaryExpr()) == 1:
                node = node.unaryExpr(0)
            elif isinstance(node, P.UnaryExprContext) and node.getChildCount() == 1:
                node = node.primaryExpr()
            elif isinstance(node, P.PrimaryExprContext) and node.expression() is not None:
                node = node.expression()
            else:
                return node

    @staticmethod
    def _comparison_parts(node):
        """(izquierda, operador, derecha) si `node` es una comparación simple, si no None."""
        if isinstance(node, P.EqualityExprContext) and len(node.relationalExpr()) == 2:
            return node.relationalExpr(0), node.getChild(1).getText(), node.relationalExpr(1)
        if isinstance(node, P.RelationalExprContext) and len(node.additiveExpr()) == 2:
            return node.additiveExpr(0), node.getChild(1).getText(), node.additiveExpr(1)
        return None

    @staticmethod
    def _is_not(node):
        return (isinstance(node, P.UnaryExprContext) and node.getChildCount() == 2
                and node.getChild(0).getText() == "!")

    def jump_false(self, expr, label):
        """Salta a `label` si la expresión es falsa; si es verdadera sigue de largo."""
        node = self._strip(expr)
        if isinstance(node, P.LogicalAndExprContext):
            for operand in node.equalityExpr():
                self.jump_false(operand, label)
            return
        if isinstance(node, P.LogicalOrExprContext):
            l_true = self.new_label()
            operands = node.logicalAndExpr()
            for operand in operands[:-1]:
                self.jump_true(operand, l_true)
            self.jump_false(operands[-1], label)
            self.emit(Label(l_true))
            return
        if self._is_not(node):
            self.jump_true(node.unaryExpr(), label)
            return
        parts = self._comparison_parts(node)
        if parts is not None:
            left_ctx, op, right_ctx = parts
            left = self.visit(left_ctx)
            right = self.visit(right_ctx)
            self.release(left, right)
            self.emit(IfRel(left, NEGATED[op], right, label))
            return
        value = self.visit(node)
        if isinstance(value, Const) and isinstance(value.value, bool):
            if not value.value:
                self.emit(Goto(label))
            return
        self.release(value)
        self.emit(IfGoto(value, label, negate=True))

    def jump_true(self, expr, label):
        """Salta a `label` si la expresión es verdadera; si es falsa sigue de largo."""
        node = self._strip(expr)
        if isinstance(node, P.LogicalOrExprContext):
            for operand in node.logicalAndExpr():
                self.jump_true(operand, label)
            return
        if isinstance(node, P.LogicalAndExprContext):
            l_false = self.new_label()
            operands = node.equalityExpr()
            for operand in operands[:-1]:
                self.jump_false(operand, l_false)
            self.jump_true(operands[-1], label)
            self.emit(Label(l_false))
            return
        if self._is_not(node):
            self.jump_false(node.unaryExpr(), label)
            return
        parts = self._comparison_parts(node)
        if parts is not None:
            left_ctx, op, right_ctx = parts
            left = self.visit(left_ctx)
            right = self.visit(right_ctx)
            self.release(left, right)
            self.emit(IfRel(left, op, right, label))
            return
        value = self.visit(node)
        if isinstance(value, Const) and isinstance(value.value, bool):
            if value.value:
                self.emit(Goto(label))
            return
        self.release(value)
        self.emit(IfGoto(value, label))

    def _materialize(self, ctx):
        """&& o || usado como valor: deja 1/0 (true/false) en un temporal."""
        result = self.new_temp()
        l_false, l_end = self.new_label(), self.new_label()
        self.jump_false(ctx, l_false)
        self.emit(Copy(result, Const(True)))
        self.emit(Goto(l_end))
        self.emit(Label(l_false))
        self.emit(Copy(result, Const(False)))
        self.emit(Label(l_end))
        return result

    # ── Expresiones ───────────────────────────────────────

    def visitExpression(self, ctx):
        return self.visit(ctx.assignmentExpr())

    def visitExprNoAssign(self, ctx):
        return self.visit(ctx.conditionalExpr())

    def visitTernaryExpr(self, ctx):
        if not ctx.expression():
            return self.visit(ctx.logicalOrExpr())
        result = self.new_temp()
        l_else, l_end = self.new_label(), self.new_label()
        self.jump_false(ctx.logicalOrExpr(), l_else)
        self.assign_to(result, self.visit(ctx.expression(0)))
        self.emit_goto(l_end)
        self.emit(Label(l_else))
        self.assign_to(result, self.visit(ctx.expression(1)))
        self.emit(Label(l_end))
        return result

    def visitLogicalOrExpr(self, ctx):
        operands = ctx.logicalAndExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        return self._materialize(ctx)

    def visitLogicalAndExpr(self, ctx):
        operands = ctx.equalityExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        return self._materialize(ctx)

    def _binary_chain(self, ctx, operands):
        left = self.visit(operands[0])
        left_type = self.types.get(operands[0])
        for i in range(1, len(operands)):
            op = ctx.getChild(2 * i - 1).getText()
            right = self.visit(operands[i])
            right_type = self.types.get(operands[i])
            if op == "+" and Type.STRING in (left_type, right_type):
                op, left_type = "concat", Type.STRING
            elif op in COMPARISONS:
                left_type = Type.BOOLEAN
            else:
                left_type = Type.INTEGER
            self.release(left, right)
            result = self.new_temp()
            self.emit(Binary(result, op, left, right))
            left = result
        return left

    def visitEqualityExpr(self, ctx):
        return self._binary_chain(ctx, ctx.relationalExpr())

    def visitRelationalExpr(self, ctx):
        return self._binary_chain(ctx, ctx.additiveExpr())

    def visitAdditiveExpr(self, ctx):
        return self._binary_chain(ctx, ctx.multiplicativeExpr())

    def visitMultiplicativeExpr(self, ctx):
        return self._binary_chain(ctx, ctx.unaryExpr())

    def visitUnaryExpr(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.primaryExpr())
        op = ctx.getChild(0).getText()
        value = self.visit(ctx.unaryExpr())
        if isinstance(value, Const):
            if op == "-" and isinstance(value.value, int) and not isinstance(value.value, bool):
                return Const(-value.value)
            if op == "!" and isinstance(value.value, bool):
                return Const(not value.value)
        self.release(value)
        result = self.new_temp()
        self.emit(Unary(result, op, value))
        return result

    def visitPrimaryExpr(self, ctx):
        if ctx.literalExpr() is not None:
            return self.visit(ctx.literalExpr())
        if ctx.leftHandSide() is not None:
            return self.visit(ctx.leftHandSide())
        return self.visit(ctx.expression())

    def visitLiteralExpr(self, ctx):
        if ctx.arrayLiteral() is not None:
            return self.visit(ctx.arrayLiteral())
        text = ctx.getText()
        if text == "true":
            return Const(True)
        if text == "false":
            return Const(False)
        if text == "null":
            return Const(None)
        if text.startswith('"'):
            return Const(text[1:-1])
        return Const(int(text))

    def visitArrayLiteral(self, ctx):
        elements = ctx.expression()
        array = self.new_temp()
        self.emit(NewArray(array, Const(len(elements))))
        for i, element in enumerate(elements):
            value = self.visit(element)
            self.emit(StoreIndex(array, Const(i), value))
            self.release(value)
        return array

    # ── Asignaciones como expresión ───────────────────────

    @staticmethod
    def _lvalue_kind(lhs):
        suffixes = lhs.suffixOp()
        if not suffixes:
            return "var" if isinstance(lhs.primaryAtom(), P.IdentifierExprContext) else None
        if isinstance(suffixes[-1], P.IndexExprContext):
            return "index"
        if isinstance(suffixes[-1], P.PropertyAccessExprContext):
            return "property"
        return None

    def visitAssignExpr(self, ctx):
        lhs = ctx.lhs
        kind = self._lvalue_kind(lhs)
        if kind == "var":
            sym = self.symbols.get(lhs.primaryAtom())
            value = self.visit(ctx.assignmentExpr())
            return self._store_variable(sym, value)
        if kind in ("index", "property"):
            last = lhs.suffixOp()[-1]
            base = self._chain(lhs, len(lhs.suffixOp()) - 1)
            if kind == "index":
                index = self.visit(last.expression())
                value = self.visit(ctx.assignmentExpr())
                self.emit(StoreIndex(base, index, value))
                self.release(base, index)
                return value
            member = self.symbols.get(last)
            value = self.visit(ctx.assignmentExpr())
            if member is None:
                self.error("No se pudo resolver el atributo", ctx)
            else:
                self.emit(StoreField(base, member.name, member.offset, value))
            self.release(base)
            return value
        self.error("El lado izquierdo de la asignación no es asignable", ctx)
        return Const(None)

    def visitPropertyAssignExpr(self, ctx):
        base = self.visit(ctx.lhs)
        member = self.symbols.get(ctx)
        value = self.visit(ctx.assignmentExpr())
        if member is None:
            self.error("No se pudo resolver el atributo", ctx)
        else:
            self.emit(StoreField(base, member.name, member.offset, value))
        self.release(base)
        return value

    # ── Accesos, llamadas y objetos ───────────────────────

    def visitLeftHandSide(self, ctx):
        return self._chain(ctx, len(ctx.suffixOp()))

    def _chain(self, ctx, count):
        """Evalúa primaryAtom y los primeros `count` sufijos (.campo, (args), [i])."""
        suffixes = list(ctx.suffixOp())[:count]
        primary = ctx.primaryAtom()
        i = 0
        if (suffixes and isinstance(suffixes[0], P.CallExprContext)
                and isinstance(primary, P.IdentifierExprContext)):
            func = self.symbols.get(suffixes[0])
            if func is None:
                self.error(f"No se pudo resolver la función '{primary.getText()}'", suffixes[0])
                return Const(None)
            operand = self._gen_call(func, None, suffixes[0])
            i = 1
        else:
            operand = self.visit(primary)

        while i < len(suffixes):
            suffix = suffixes[i]
            if isinstance(suffix, P.PropertyAccessExprContext):
                member = self.symbols.get(suffix)
                if member is None:
                    self.error(f"No se pudo resolver el miembro '{suffix.Identifier().getText()}'", suffix)
                    return Const(None)
                following = suffixes[i + 1] if i + 1 < len(suffixes) else None
                if member.kind == "function":
                    if isinstance(following, P.CallExprContext):
                        operand = self._gen_call(member, operand, following)
                        i += 2
                        continue
                    self.error("Un método no se puede usar como valor", suffix)
                    return Const(None)
                self.release(operand)
                result = self.new_temp()
                self.emit(LoadField(result, operand, member.name, member.offset))
                operand = result
            elif isinstance(suffix, P.IndexExprContext):
                index = self.visit(suffix.expression())
                self.release(operand, index)
                result = self.new_temp()
                self.emit(LoadIndex(result, operand, index))
                operand = result
            else:
                self.error("No se puede llamar al resultado de una expresión", suffix)
                return Const(None)
            i += 1
        return operand

    def _gen_call(self, func, receiver, call_ctx):
        """Llamada a una función o método: evalúa argumentos, emite param y call."""
        args = []
        if call_ctx.arguments() is not None:
            args = [self.visit(e) for e in call_ctx.arguments().expression()]
        count = len(args)
        if receiver is not None:
            self.emit(Param(receiver))
            count += 1
        for arg in args:
            self.emit(Param(arg))
        if receiver is not None:
            self.release(receiver)
        self.release(*args)
        link = None
        if func.storage == "function" and func.depth > 0:
            link = self.fctx.depth - func.depth
        if func.return_type in (None, Type.VOID):
            self.emit(Call(None, func.label, count, link))
            return Const(None)
        result = self.new_temp()
        self.emit(Call(result, func.label, count, link))
        return result

    def visitIdentifierExpr(self, ctx):
        sym = self.symbols.get(ctx)
        if sym is None:
            self.error(f"No se pudo resolver '{ctx.getText()}'", ctx)
            return Const(None)
        if sym.kind in ("function", "class"):
            self.error(f"'{sym.name}' no se puede usar como valor (no hay funciones de primera clase)", ctx)
            return Const(None)
        if sym.storage == "field":
            result = self.new_temp()
            self.emit(LoadField(result, self.this_operand(), sym.name, sym.offset))
            return result
        return self.var_operand(sym)

    def visitThisExpr(self, ctx):
        return self.this_operand()

    def _class_chain(self, name):
        chain = []
        while name is not None and name in self.classes:
            chain.append(self.classes[name])
            name = self.classes[name].parent_class
        return list(reversed(chain))

    def visitNewExpr(self, ctx):
        cls = self.symbols.get(ctx)
        if cls is None:
            self.error("No se pudo resolver la clase", ctx)
            return Const(None)
        args = []
        if ctx.arguments() is not None:
            args = [self.visit(e) for e in ctx.arguments().expression()]
        obj = self.new_temp()
        self.emit(New(obj, cls.name, cls.size))
        for c in self._class_chain(cls.name):          # atributos con valor inicial, de la base a la derivada
            label = self.own_init.get(c.name)
            if label:
                self.emit(Param(obj))
                self.emit(Call(None, label, 1))
        ctor = self.analyzer._lookup_class_member(cls.name, "constructor")
        if ctor is not None and ctor.kind == "function":
            self.emit(Param(obj))
            for arg in args:
                self.emit(Param(arg))
            self.emit(Call(None, ctor.label, len(args) + 1))
        self.release(*args)
        return obj
