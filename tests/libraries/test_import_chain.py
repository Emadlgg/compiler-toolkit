"""Cadena de importaciones: main -> Perro (fuente) -> Animal.cplobj (compilada)."""
import os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARS = ROOT / 'tools' / 'Mars.jar'

ANIMAL = '''export class Animal {
    let edad: integer;
    function constructor() { this.edad = 5; }
    function obtener(): integer { return this.edad; }
}
'''
PERRO = '''import { Animal } from "./build/Animal.cplobj";
export class Perro : Animal {
    let bono: integer;
    function constructor() { this.edad = 5; this.bono = 2; }
    function total(): integer { return this.obtener() + this.bono; }
}
'''


def cli(*args, cwd):
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    r = subprocess.run([sys.executable, str(ROOT / 'compiscript.py'), *map(str, args)], cwd=cwd,
                       capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    return r.returncode, r.stdout + r.stderr


def mars(asm):
    r = subprocess.run(['java', '-jar', str(MARS), 'nc', str(asm)], capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=60)
    return [l for l in r.stdout.splitlines() if l.strip()]


class TestImportChain(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / 'Animal.cps').write_text(ANIMAL, encoding='utf-8')
        (self.dir / 'Perro.cps').write_text(PERRO, encoding='utf-8')
        code, out = cli('Animal.cps', '--build-library', '--output', 'build/Animal.cplobj', cwd=self.dir)
        self.assertEqual(code, 0, out)

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, main):
        (self.dir / 'main.cps').write_text(main, encoding='utf-8')
        code, out = cli('main.cps', '--mips', '--output', 'build/m.asm', cwd=self.dir)
        self.assertEqual(code, 0, out)
        if MARS.is_file():
            return mars(self.dir / 'build' / 'm.asm')

    def test_main_imports_source_module_that_imports_cplobj(self):
        out = self._run('import { Perro } from "./Perro";\nlet q = new Perro();\nprint(q.total());\n')
        if out is not None:
            self.assertEqual(out, ['7'])

    def test_main_and_module_import_same_cplobj(self):
        out = self._run('import { Animal } from "./build/Animal.cplobj";\n'
                        'import { Perro } from "./Perro";\n'
                        'let q = new Perro();\nlet a = new Animal();\nprint(q.total());\nprint(a.obtener());\n')
        if out is not None:
            self.assertEqual(out, ['7', '5'])

    def test_module_itself_runs_with_cplobj_parent(self):
        (self.dir / 'Perro.cps').write_text(PERRO + 'let p = new Perro();\nprint(p.total());\n', encoding='utf-8')
        code, out = cli('Perro.cps', '--mips', '--output', 'build/p.asm', cwd=self.dir)
        self.assertEqual(code, 0, out)
        if MARS.is_file():
            self.assertEqual(mars(self.dir / 'build' / 'p.asm'), ['7'])


if __name__ == '__main__':
    unittest.main()


class TestLibraryWithDependency(unittest.TestCase):
    """BUILD LIB sobre una clase hija cuyo padre vive en otra biblioteca (.cplobj)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / 'Animal.cps').write_text(ANIMAL, encoding='utf-8')
        (self.dir / 'Perro.cps').write_text(PERRO, encoding='utf-8')
        code, out = cli('Animal.cps', '--build-library', '--output', 'build/Animal.cplobj', cwd=self.dir)
        self.assertEqual(code, 0, out)

    def tearDown(self):
        self._tmp.cleanup()

    def _build_perro(self, output='build/Perro.cplobj'):
        return cli('Perro.cps', '--build-library', '--output', output, cwd=self.dir)

    def _run(self, main):
        (self.dir / 'main.cps').write_text(main, encoding='utf-8')
        code, out = cli('main.cps', '--mips', '--output', 'build/m.asm', cwd=self.dir)
        return code, out

    def test_child_library_depends_on_parent_library(self):
        code, out = self._build_perro()
        self.assertEqual(code, 0, out)
        code, out = self._run('import { Perro } from "./build/Perro.cplobj";\n'
                              'let q = new Perro();\nprint(q.total());\nprint(q.obtener());\n')
        self.assertEqual(code, 0, out)
        if MARS.is_file():
            self.assertEqual(mars(self.dir / 'build' / 'm.asm'), ['7', '5'])

    def test_importing_both_libraries_still_works(self):
        self.assertEqual(self._build_perro()[0], 0)
        code, out = self._run('import { Animal } from "./build/Animal.cplobj";\n'
                              'import { Perro } from "./build/Perro.cplobj";\n'
                              'let q = new Perro();\nlet a = new Animal();\nprint(q.total());\nprint(a.obtener());\n')
        self.assertEqual(code, 0, out)
        if MARS.is_file():
            self.assertEqual(mars(self.dir / 'build' / 'm.asm'), ['7', '5'])

    def test_changed_dependency_is_rejected(self):
        self.assertEqual(self._build_perro()[0], 0)
        (self.dir / 'Animal.cps').write_text(ANIMAL.replace('= 5;', '= 9;'), encoding='utf-8')
        code, out = cli('Animal.cps', '--build-library', '--output', 'build/Animal.cplobj', cwd=self.dir)
        self.assertEqual(code, 0, out)
        code, out = self._run('import { Perro } from "./build/Perro.cplobj";\nlet q = new Perro();\nprint(q.total());\n')
        self.assertNotEqual(code, 0)
        self.assertIn('Integridad de dependencia incorrecta', out)

    def test_missing_dependency_is_reported(self):
        self.assertEqual(self._build_perro()[0], 0)
        (self.dir / 'build' / 'Animal.cplobj').unlink()
        code, out = self._run('import { Perro } from "./build/Perro.cplobj";\nlet q = new Perro();\nprint(q.total());\n')
        self.assertNotEqual(code, 0)
        self.assertIn('Dependencia inexistente', out)

    def test_library_must_live_next_to_its_dependencies(self):
        code, out = self._build_perro('otra/Perro.cplobj')
        self.assertNotEqual(code, 0)
        self.assertIn('misma carpeta', out)

    def test_missing_parent_library_is_reported_when_building(self):
        (self.dir / 'build' / 'Animal.cplobj').unlink()
        code, out = self._build_perro()
        self.assertNotEqual(code, 0)
        self.assertIn('No se encontro la biblioteca compilada', out)


CACHORRO = '''import { Perro } from "./build/Perro.cplobj";
export class Cachorro : Perro {
    let juguetes: integer;
    function constructor() { this.edad = 1; this.bono = 3; this.juguetes = 4; }
    function resumen(): integer { return this.total() + this.juguetes + this.obtener(); }
}
'''


class TestThreeLevelChainAndFrames(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        for name, src in (('Animal', ANIMAL), ('Perro', PERRO), ('Cachorro', CACHORRO)):
            (self.dir / f'{name}.cps').write_text(src, encoding='utf-8')
            code, out = cli(f'{name}.cps', '--build-library', '--output', f'build/{name}.cplobj', cwd=self.dir)
            self.assertEqual(code, 0, out)

    def tearDown(self):
        self._tmp.cleanup()

    def test_abi_frame_size_matches_real_frame(self):
        """El llamador reserva frame_size bytes: debe incluir los temporales del TAC."""
        import json, re, zipfile
        for lib in ('Animal', 'Perro', 'Cachorro'):
            with zipfile.ZipFile(self.dir / 'build' / f'{lib}.cplobj') as z:
                meta = json.loads(z.read('interface.json'))
                text = json.loads(z.read('object.mobj'))['text']
            for item in meta['exports'].values():
                for method in item['methods'].values():
                    label = method['label']
                    block = text[text.index(label + ':'):]
                    block = re.split(r'\n[A-Za-z_]\w*:', block, maxsplit=1)[0]
                    real = max(int(n) for n in re.findall(r'addiu \$sp, \$fp, (\d+)', block))
                    self.assertGreaterEqual(method['frame_size'], real, label)

    def test_three_library_chain_runs(self):
        (self.dir / 'main.cps').write_text('import { Cachorro } from "./build/Cachorro.cplobj";\n'
                                           'let c = new Cachorro();\nprint(c.resumen());\nprint(c.edad);\nprint(c.obtener());\n',
                                           encoding='utf-8')
        code, out = cli('main.cps', '--mips', '--output', 'build/m.asm', cwd=self.dir)
        self.assertEqual(code, 0, out)
        if MARS.is_file():
            self.assertEqual(mars(self.dir / 'build' / 'm.asm'), ['9', '1', '1'])
