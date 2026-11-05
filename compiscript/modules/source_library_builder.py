"""Compile a self-contained Compiscript module to a verified .cplobj.

This intentionally supports only standalone classes/functions whose generated
MIPS can be extracted safely; globals, dependencies and relocations fail closed.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

from .class_package_builder import build_class_package
from .interface_metadata import from_symbol_table
from .resolver import _load


class SourceLibraryError(ValueError):
    pass


def build_source_library(source_path, output_path):
    source_path = Path(source_path).resolve()
    if source_path.suffix.lower() != '.cps':
        raise SourceLibraryError('La biblioteca debe partir de un archivo .cps')
    module = _load(source_path)
    if module.imports:
        raise SourceLibraryError('Bibliotecas con imports requieren enlace de dependencias (pendiente)')
    if not module.exports:
        raise SourceLibraryError('No hay declaraciones exportadas')

    # Import lazily so the packaging utilities remain usable without ANTLR.
    from compiscript import codegen
    from compiscript.mips import MIPSGenerator
    from compiscript.modules.class_package_builder import ClassPackageBuildError
    from compiscript.modules.interface_metadata import InterfaceError
    from compiscript.modules.library_object_builder import LibraryBuildError
    from compiscript.modules.resolver import _global_declarations
    from compiscript.generated.CompiscriptLexer import CompiscriptLexer
    from compiscript.generated.CompiscriptParser import CompiscriptParser
    from compiscript.semantic import SemanticAnalyzer
    from antlr4 import CommonTokenStream, InputStream
    from antlr4.error.ErrorListener import ErrorListener

    class Collector(ErrorListener):
        def __init__(self):
            super().__init__()
            self.messages = []
        def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
            self.messages.append(f'{line}:{column}: {msg}')

    collector = Collector()
    lexer = CompiscriptLexer(InputStream(module.source))
    lexer.removeErrorListeners()
    lexer.addErrorListener(collector)
    parser = CompiscriptParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(collector)
    tree = parser.program()
    if collector.messages:
        raise SourceLibraryError('Errores sintacticos: ' + '; '.join(collector.messages))
    analyzer = SemanticAnalyzer()
    analyzer.visit(tree)
    if analyzer.errors:
        raise SourceLibraryError('Errores semanticos: ' + '; '.join(map(str, analyzer.errors)))
    # Non-exported global variables also require relocation; fail before writing.
    for name in _global_declarations(module.source):
        sym = analyzer.table.global_scope.lookup_local(name)
        if sym is not None and sym.kind in ('variable', 'const'):
            raise SourceLibraryError('Variables globales requieren reubicacion: ' + name)
    try:
        metadata = from_symbol_table(analyzer.table, module.exports)
        intermediate = codegen.CodeGenerator(analyzer)
        intermediate.generate(tree)
        if intermediate.errors:
            raise SourceLibraryError('Errores TAC: ' + '; '.join(map(str, intermediate.errors)))
        assembly = MIPSGenerator(intermediate.instructions, intermediate.records, analyzer.table).generate()
        with TemporaryDirectory(prefix='cps-build-lib-') as tmp:
            root = Path(tmp)
            (root / 'library.asm').write_text(assembly, encoding='utf-8')
            (root / 'interface.cps').write_text(module.source, encoding='utf-8')
            import json
            (root / 'abi.json').write_text(json.dumps(metadata, ensure_ascii=False), encoding='utf-8')
            return build_class_package(root / 'library.asm', root / 'interface.cps',
                                       root / 'abi.json', output_path)
    except (ClassPackageBuildError, InterfaceError, LibraryBuildError, ValueError) as exc:
        raise SourceLibraryError(str(exc)) from exc
