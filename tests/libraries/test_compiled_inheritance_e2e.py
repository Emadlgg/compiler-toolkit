"""End-to-end inheritance within one precompiled .cplobj.

Requires a compatible ANTLR runtime; MARS is discovered from tools/Mars.jar.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'compiscript.py'

SOURCE = '''export class Animal {
    let edad: integer;
    function constructor() {
        this.edad = 5;
    }
    function obtener(): integer {
        return this.edad;
    }
    function tipo(): integer {
        return 10;
    }
}
export class Perro : Animal {
    let bono: integer;
    function constructor() {
        this.edad = 5;
        this.bono = 2;
    }
    function tipo(): integer {
        return 20;
    }
    function total(): integer {
        return this.obtener() + this.bono;
    }
}
'''


def run(*args):
    env = os.environ.copy()
    env.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    return subprocess.run([str(a) for a in args], cwd=ROOT, env=env,
                          capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=45)


class TestCompiledInheritanceE2E(unittest.TestCase):
    def test_parent_child_one_package_without_source(self):
        with tempfile.TemporaryDirectory(prefix='cps-inheritance-') as tmp:
            root = Path(tmp)
            producer = root / 'Familia.cps'
            package = root / 'Familia.cplobj'
            consumer = root / 'main.cps'
            output = root / 'main.asm'
            producer.write_text(SOURCE, encoding='utf-8')
            result = run(sys.executable, CLI, producer, '--build-library', '--output', package)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(package.is_file())
            producer.unlink()
            consumer.write_text('''import { Perro } from "./Familia.cplobj";
let p = new Perro();
print(p.total());
print(p.tipo());
''', encoding='utf-8')
            result = run(sys.executable, CLI, consumer, '--mips', '--output', output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(output.is_file())
            jar = Path(os.environ.get('MARS_JAR', str(ROOT / 'tools' / 'Mars.jar')))
            if not jar.is_file():
                self.skipTest('MARS no disponible')
            result = run('java', '-jar', jar, 'nc', output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.replace("\n", ""), '720')


if __name__ == '__main__':
    unittest.main()
