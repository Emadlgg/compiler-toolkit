"""Pruebas de deteccion portable de MARS."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from compiscript.mars import find_mars


class TestMarsDiscovery(unittest.TestCase):
    def test_local_without_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / 'tools' / 'Mars.jar'
            jar.parent.mkdir()
            jar.write_bytes(b'fixture')
            with patch.dict('os.environ', {}, clear=True):
                self.assertEqual(find_mars(root=tmp), jar.resolve())

    def test_invalid_environment_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / 'tools' / 'Mars.jar'
            jar.parent.mkdir()
            jar.write_bytes(b'fixture')
            with patch.dict('os.environ', {'MARS_JAR': str(Path(tmp) / 'missing.jar')}):
                self.assertEqual(find_mars(root=tmp), jar.resolve())

    def test_explicit_invalid_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / 'tools' / 'Mars.jar'
            jar.parent.mkdir()
            jar.write_bytes(b'fixture')
            self.assertIsNone(find_mars(explicit=Path(tmp) / 'absent.jar', root=tmp))

    def test_environment_preferred(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / 'external.jar'
            jar.write_bytes(b'fixture')
            with patch.dict('os.environ', {'MARS_JAR': str(jar)}):
                self.assertEqual(find_mars(root=tmp), jar.resolve())


if __name__ == '__main__':
    unittest.main()
