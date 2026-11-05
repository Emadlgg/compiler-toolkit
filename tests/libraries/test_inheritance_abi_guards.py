"""Guard inherited field offsets in precompiled package metadata."""
import unittest
from compiscript.modules.class_package_builder import _exported_labels, ClassPackageBuildError
from compiscript.modules.interface_metadata import ABI_VERSION


def cls(parent, size, fields, label):
    return {'kind': 'class', 'parent': parent, 'size': size, 'fields': fields,
            'methods': {'constructor': {'label': label, 'params': [],
                                        'return_type': 'void', 'frame_size': 20}}}


class TestInheritedLayoutGuards(unittest.TestCase):
    def test_inherited_field_cannot_be_overwritten(self):
        metadata = {'format': ABI_VERSION, 'exports': {
            'Animal': cls(None, 4, {'edad': {'type': 'integer', 'offset': 0}}, 'Animal_constructor'),
            'Perro': cls('Animal', 8, {'bono': {'type': 'integer', 'offset': 0}}, 'Perro_constructor')}}
        with self.assertRaisesRegex(ClassPackageBuildError, 'solapamiento'):
            _exported_labels(metadata)

    def test_child_field_after_parent_is_valid(self):
        metadata = {'format': ABI_VERSION, 'exports': {
            'Animal': cls(None, 4, {'edad': {'type': 'integer', 'offset': 0}}, 'Animal_constructor'),
            'Perro': cls('Animal', 8, {'bono': {'type': 'integer', 'offset': 4}}, 'Perro_constructor')}}
        self.assertEqual(len(_exported_labels(metadata)), 2)


if __name__ == '__main__':
    unittest.main()
