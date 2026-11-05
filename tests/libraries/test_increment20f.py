"""Bounded 20F checks: inheritance inside one compiled package."""
import unittest
from compiscript.modules.class_package_builder import _exported_labels, ClassPackageBuildError
from compiscript.modules.interface_metadata import ABI_VERSION


def cls(parent=None, size=4, label='Animal_constructor'):
    return {'kind':'class','parent':parent,'size':size,'fields':{},'methods':{
        'constructor':{'label':label,'params':[],'return_type':'void','frame_size':20}}}


class TestCompiledInheritanceValidation(unittest.TestCase):
    def test_parent_and_child_exported_together(self):
        meta = {'format':ABI_VERSION,'exports':{
            'Animal':cls(), 'Perro':cls('Animal',4,'Perro_constructor')}}
        self.assertEqual(set(_exported_labels(meta)), {'Animal_constructor','Perro_constructor'})

    def test_external_parent_still_rejected(self):
        meta = {'format':ABI_VERSION,'exports':{'Perro':cls('Animal',4,'Perro_constructor')}}
        with self.assertRaisesRegex(ClassPackageBuildError, 'Herencia externa'):
            _exported_labels(meta)

    def test_parent_layout_cannot_shrink(self):
        meta = {'format':ABI_VERSION,'exports':{
            'Animal':cls(size=12), 'Perro':cls('Animal',4,'Perro_constructor')}}
        with self.assertRaisesRegex(ClassPackageBuildError, 'Layout'):
            _exported_labels(meta)

    def test_cycle_rejected(self):
        meta = {'format':ABI_VERSION,'exports':{
            'Animal':cls('Perro'), 'Perro':cls('Animal',4,'Perro_constructor')}}
        with self.assertRaisesRegex(ClassPackageBuildError, 'circular'):
            _exported_labels(meta)


if __name__ == '__main__':
    unittest.main()
