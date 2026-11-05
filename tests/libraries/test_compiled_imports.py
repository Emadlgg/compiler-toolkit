import tempfile
import unittest
from pathlib import Path
from compiscript.modules.compiled_imports import CompiledImportError, load_compiled_dependency, collect_compiled_dependencies
from compiscript.modules.mips_linker import build_object
from compiscript.modules.compiled_package import create_package
from compiscript.modules.interface_metadata import ABI_VERSION

class TestCompiledImports(unittest.TestCase):
    def test_metadata_and_dependency_discovery(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/'routine.asm').write_text('hello:\n  jr $ra\n', encoding='utf-8')
            build_object(p/'routine.asm', ['hello'], p/'routine.mobj')
            (p/'interface.cps').write_text('function hello(): void {}\n', encoding='utf-8')
            metadata = {'format': ABI_VERSION, 'exports': {'hello': {'kind':'function', 'label':'hello', 'params':[], 'return_type':'void', 'frame_size':16}}}
            create_package(p/'interface.cps', p/'routine.mobj', p/'routine.cplobj', metadata=metadata)
            (p/'main.cps').write_text('import { hello } from "./routine.cplobj";\nhello();\n', encoding='utf-8')
            dep = load_compiled_dependency(p/'routine.cplobj')
            self.assertIn('hello', dep.metadata['exports'])
            self.assertEqual(len(collect_compiled_dependencies(p/'main.cps')), 1)
            (p/'main.cps').write_text('import { absent } from "./routine.cplobj";\n', encoding='utf-8')
            with self.assertRaises(CompiledImportError):
                collect_compiled_dependencies(p/'main.cps')

if __name__ == '__main__':
    unittest.main()
