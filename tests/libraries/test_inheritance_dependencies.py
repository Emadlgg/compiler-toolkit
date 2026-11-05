import unittest
from compiscript.modules.inheritance_dependencies import validate_external_inheritance
from compiscript.modules.compiled_imports import CompiledImportError
from compiscript.modules.interface_metadata import ABI_VERSION


def cls(parent=None, size=4, fields=None):
    return {'kind': 'class', 'parent': parent, 'size': size,
            'fields': fields or {}, 'methods': {}}


def abi(**exports):
    return {'format': ABI_VERSION, 'exports': exports}


class TestExternalInheritanceGuards(unittest.TestCase):
    def test_reject_missing_parent(self):
        with self.assertRaisesRegex(CompiledImportError, 'no disponible'):
            validate_external_inheritance(abi(Perro=cls('Animal', 8)), [])

    def test_local_inheritance_accepted(self):
        validate_external_inheritance(abi(Animal=cls(size=4), Perro=cls('Animal', 8)), [])

    def test_local_cycle_rejected(self):
        with self.assertRaisesRegex(CompiledImportError, 'circular'):
            validate_external_inheritance(abi(A=cls('B'), B=cls('A')), [])

    def test_layout_too_small_rejected(self):
        with self.assertRaisesRegex(CompiledImportError, 'Layout'):
            validate_external_inheritance(abi(A=cls(size=8), B=cls('A', 4)), [])


if __name__ == '__main__':
    unittest.main()
