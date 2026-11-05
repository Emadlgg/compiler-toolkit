"""Regression checks for external frame descriptors and source resolver."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from compiscript.modules.compiled_runtime import external_records
from compiscript.modules.resolver import resolve_project


class TestCompiledPipeline(unittest.TestCase):
    def test_external_frame_sizes(self):
        dep = SimpleNamespace(metadata={'exports': {
            'Persona': {'kind': 'class', 'methods': {
                'constructor': {'label': 'Persona_constructor', 'frame_size': 28},
                'saludar': {'label': 'Persona_saludar', 'frame_size': 24}}},
            'suma': {'kind': 'function', 'label': 'suma', 'frame_size': 32}}})
        records = {r.label: r.size for r in external_records(SimpleNamespace(libraries=[dep]))}
        self.assertEqual(records, {'Persona_constructor': 28, 'Persona_saludar': 24, 'suma': 32})

    def test_compiled_import_not_sent_to_antlr(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'main.cps').write_text('import { Persona as Humano } from "./Persona.cplobj";\nlet x = new Humano();\n', encoding='utf-8')
            source = resolve_project(root / 'main.cps')
            self.assertNotIn('import {', source)
            self.assertIn('new Humano()', source)


if __name__ == '__main__':
    unittest.main()
