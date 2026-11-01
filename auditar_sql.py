"""Pruebas de regresion del interprete SQL. No modifica las bases existentes.
Uso: python auditar_sql.py
"""
import tempfile
import unittest
from pathlib import Path
from sqlengine.executor import execute
from sqlengine.storage import FileStorage
from sqlengine.indexes import IndexManager


class AuditoriaSQL(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='auditoria_sql_')
        self.db = str(Path(self.tmp.name) / 'database')

    def tearDown(self):
        self.tmp.cleanup()

    def sql(self, statement):
        return execute(statement, self.db)

    def seed(self):
        self.sql("CREATE TABLE personas (id INT PRIMARY KEY, nombre VARCHAR(30) NOT NULL, edad INT);")
        self.sql("INSERT INTO personas VALUES (1, 'Ana', 20), (2, 'Luis', 30);")

    def test_01_crear_insertar_consultar(self):
        self.seed()
        cols, rows = self.sql('SELECT nombre FROM personas WHERE edad >= 21 ORDER BY nombre;')[-1]
        self.assertEqual(cols, ['nombre'])
        self.assertEqual(rows, [['Luis']])

    def test_02_persistencia(self):
        self.seed()
        self.assertEqual(len(FileStorage(self.db).rows('personas')), 2)

    def test_03_update_delete(self):
        self.seed()
        self.sql('UPDATE personas SET edad = 31 WHERE id = 2;')
        self.sql('DELETE FROM personas WHERE id = 1;')
        _, rows = self.sql('SELECT edad FROM personas;')[-1]
        self.assertEqual(rows, [[31]])

    def test_04_clave_duplicada(self):
        self.seed()
        with self.assertRaises(ValueError):
            self.sql("INSERT INTO personas VALUES (1, 'Otra', 19);")

    def test_05_tabla_inexistente(self):
        with self.assertRaises(ValueError):
            self.sql('SELECT id FROM inexistente;')

    def test_06_tipo_incompatible(self):
        self.seed()
        with self.assertRaises(ValueError):
            self.sql("INSERT INTO personas VALUES (3, 'Eva', 'texto');")

    def test_07_indices_actualizados(self):
        self.seed()
        self.sql('CREATE INDEX idx_edad ON personas (edad);')
        manager = IndexManager(FileStorage(self.db))
        self.assertEqual(manager.lookup('personas', 'edad', 20), [0])
        self.sql('UPDATE personas SET edad = 25 WHERE id = 1;')
        manager = IndexManager(FileStorage(self.db))
        self.assertEqual(manager.lookup('personas', 'edad', 20), [])
        self.assertEqual(manager.lookup('personas', 'edad', 25), [0])
        self.sql('DELETE FROM personas WHERE id = 1;')
        manager = IndexManager(FileStorage(self.db))
        self.assertEqual(manager.lookup('personas', 'edad', 25), [])
        self.sql('DROP INDEX idx_edad;')
        self.assertFalse((Path(self.db) / 'indexes' / 'idx_edad.json').exists())

    def test_08_subconsulta_correlacionada(self):
        self.seed()
        self.sql('CREATE TABLE notas (id INT PRIMARY KEY, persona_id INT);')
        self.sql('INSERT INTO notas VALUES (10, 1);')
        _, rows = self.sql('SELECT nombre FROM personas p WHERE EXISTS (SELECT id FROM notas n WHERE n.persona_id = p.id);')[-1]
        self.assertEqual(rows, [['Ana']])

    def test_09_escalar_multiples_filas(self):
        self.seed()
        with self.assertRaises(ValueError):
            self.sql('SELECT nombre FROM personas WHERE edad = (SELECT edad FROM personas);')

    def test_10_cadena_vacia_no_es_null(self):
        self.sql('CREATE TABLE textos (id INT PRIMARY KEY, valor VARCHAR(20));')
        self.sql("INSERT INTO textos VALUES (1, ''), (2, NULL);")
        _, empty = self.sql("SELECT id FROM textos WHERE valor = '';")[-1]
        _, nulls = self.sql('SELECT id FROM textos WHERE valor IS NULL;')[-1]
        self.assertEqual(empty, [[1]])
        self.assertEqual(nulls, [[2]])


if __name__ == '__main__':
    unittest.main(verbosity=2)
