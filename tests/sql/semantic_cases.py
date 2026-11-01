"""
semantic_cases.py — Pruebas del análisis semántico con el resultado esperado escrito a mano.

Los casos usan el esquema de tests/sql/fixtures/universidad:
  estudiantes(id INT PK, nombre VARCHAR(50) NN, edad INT, promedio FLOAT, activo BOOLEAN, ingreso DATE)
  cursos(id INT PK, nombre VARCHAR(50) NN, creditos INT)
  inscripciones(estudiante_id INT, curso_id INT, nota FLOAT)
  índices: idx_estudiantes_edad (estudiantes.edad), idx_inscripciones_curso (inscripciones.curso_id)
"""

import glob
import os
import tempfile

from sqlengine import ast as A
from sqlengine.catalog import Catalog, Column, Index
from sqlengine.frontend import parse
from sqlengine.ast_builder import build_ast
from sqlengine.metadata import MetadataError, format_metadata, load_catalog, parse_metadata, save_catalog
from sqlengine.semantic import analyze_script

HERE = os.path.dirname(os.path.abspath(__file__))
UNI = load_catalog(os.path.join(HERE, "fixtures", "universidad"))


def analyzed(sql, catalog=UNI):
    result = parse(sql)
    assert result.ok, f"el texto no analiza: {[str(e) for e in result.errors]}"
    script = build_ast(result)
    return script, analyze_script(script, catalog)


def first(sql, catalog=UNI):
    script, result = analyzed(sql, catalog)
    assert result.ok, f"no debía tener errores: {[str(e) for e in result.errors]}"
    return script.statements[0]


def errors_of(sql, catalog=UNI):
    return [(e.line, e.column, e.message) for e in analyzed(sql, catalog)[1].errors]


def bind(ref):
    b = ref.binding
    return (b.source, b.column, b.depth)


# ── tipos y nombres de salida ─────────────────────────────

def check_expression_types():
    s = first("SELECT edad + 1, edad / 2, promedio + 1, edad * 1.5, edad > 3, nombre IS NULL, -promedio, NOT activo, 1 + 2, 'x', TRUE, NULL FROM estudiantes;")
    assert [t for _, t in s.output] == ["INT", "INT", "FLOAT", "FLOAT", "BOOLEAN", "BOOLEAN", "FLOAT", "BOOLEAN", "INT", "VARCHAR", "BOOLEAN", "NULL"]


def check_aggregate_types():
    s = first("SELECT COUNT(*), COUNT(nombre), AVG(edad), SUM(edad), SUM(promedio), MIN(nombre), MAX(ingreso), MIN(edad) FROM estudiantes;")
    assert [t for _, t in s.output] == ["INT", "INT", "FLOAT", "INT", "FLOAT", "VARCHAR", "DATE", "INT"]


def check_output_names():
    s = first("SELECT nombre, e.edad, edad * 2 + 1, nombre AS alumno, 'x' FROM estudiantes e;")
    assert [n for n, _ in s.output] == ["nombre", "edad", "edad * 2 + 1", "alumno", "'x'"]
    s = first("SELECT COUNT(*), AVG(i.nota), MAX(e.edad) AS tope FROM estudiantes e INNER JOIN inscripciones i ON e.id = i.estudiante_id;")
    assert [n for n, _ in s.output] == ["COUNT(*)", "AVG(i.nota)", "tope"]


def check_star_expansion():
    s = first("SELECT * FROM estudiantes e INNER JOIN cursos c ON c.id = e.id;")
    assert [n for n, _ in s.output] == ["id", "nombre", "edad", "promedio", "activo", "ingreso", "id", "nombre", "creditos"]
    s = first("SELECT c.*, e.id FROM estudiantes e INNER JOIN cursos c ON c.id = e.id;")
    assert [n for n, _ in s.output] == ["id", "nombre", "creditos", "id"]
    assert errors_of("SELECT z.* FROM estudiantes e;")[0][2].startswith("La tabla 'z' no aparece en la cláusula FROM")


def check_sources_annotation():
    s = first("SELECT 1 FROM estudiantes e INNER JOIN cursos ON cursos.id = e.id;")
    assert [(name, table.name) for name, table in s.sources] == [("e", "estudiantes"), ("cursos", "cursos")]


# ── resolución de columnas ────────────────────────────────

def check_bindings():
    s = first("SELECT e.id, edad, c.nombre FROM estudiantes e INNER JOIN cursos c ON c.id = e.id;")
    assert [bind(i.expr) for i in s.items] == [(0, 0, 0), (0, 2, 0), (1, 1, 0)]
    assert [i.expr.binding.type for i in s.items] == ["INT", "INT", "VARCHAR"]


def check_correlated_subqueries():
    s = first("SELECT nombre FROM estudiantes e WHERE EXISTS (SELECT 1 FROM inscripciones i WHERE i.estudiante_id = e.id);")
    inner = s.where.query.where
    assert bind(inner.left) == (0, 0, 0)        # i.estudiante_id: la primera columna de inscripciones, de esta consulta
    assert bind(inner.right) == (0, 0, 1)       # e.id: de la consulta de afuera (profundidad 1)

    s = first("SELECT nombre FROM estudiantes WHERE EXISTS (SELECT 1 FROM inscripciones WHERE estudiante_id = id);")
    inner = s.where.query.where
    assert bind(inner.left) == (0, 0, 0) and bind(inner.right) == (0, 0, 1)     # `id` no está en inscripciones: se busca afuera

    s = first("SELECT 1 FROM cursos c WHERE EXISTS (SELECT 1 FROM estudiantes e WHERE EXISTS (SELECT 1 FROM inscripciones i WHERE i.curso_id = c.id));")
    innermost = s.where.query.where.query.where
    assert bind(innermost.right) == (0, 0, 2)   # c.id está dos consultas más afuera


def check_inner_scope_wins():
    s = first("SELECT 1 FROM estudiantes WHERE EXISTS (SELECT 1 FROM cursos WHERE nombre = 'x');")
    assert bind(s.where.query.where.left) == (0, 1, 0)      # `nombre` existe en las dos: gana la consulta más cercana


def check_order_by_alias():
    s = first("SELECT edad AS nombre FROM estudiantes ORDER BY nombre;")
    assert bind(s.order_by[0].expr) == (-1, 0, 0)           # el alias gana a la columna del mismo nombre
    s = first("SELECT edad FROM estudiantes ORDER BY nombre;")
    assert bind(s.order_by[0].expr) == (0, 1, 0)            # sin alias, es la columna de la tabla
    msgs = [m for _, _, m in errors_of("SELECT edad AS x FROM estudiantes WHERE x > 1;")]
    assert len(msgs) == 1 and msgs[0].startswith("La columna 'x' no existe")      # fuera de ORDER BY no vale el alias


def check_join_condition_visibility():
    errs = errors_of("SELECT 1 FROM estudiantes e INNER JOIN cursos c ON c.id = i.curso_id INNER JOIN inscripciones i ON i.curso_id = c.id;")
    assert len(errs) == 1 and "La tabla o alias 'i' no existe" in errs[0][2]


def check_names_are_case_insensitive():
    s = first("SELECT NOMBRE FROM ESTUDIANTES E WHERE E.EDAD > 1;")
    assert bind(s.items[0].expr) == (0, 1, 0)
    assert s.output[0][0] == "NOMBRE"           # el nombre de salida es el que se escribió
    assert UNI.table("ESTUDIANTES").find_column("EDAD")[0] == 2
    assert UNI.find_index("IDX_ESTUDIANTES_EDAD").table == "estudiantes"


# ── anotaciones para el ejecutor ──────────────────────────

def check_date_coercion():
    s = first("SELECT 1 FROM estudiantes WHERE ingreso > '2023-01-01';")
    lit = s.where.right
    assert (lit.type, lit.sql_type, lit.value) == ("DATE", "DATE", "2023-01-01")
    assert first("SELECT 1 FROM estudiantes WHERE nombre = '2023-01-01';").where.right.type == "VARCHAR"      # texto con texto: no cambia
    i = first("INSERT INTO estudiantes (id, nombre, ingreso) VALUES (1, 'x', '2024-02-29');")
    assert i.rows[0].values[2].type == "DATE"                                                              # 2024 fue bisiesto
    assert errors_of("INSERT INTO estudiantes (id, nombre, ingreso) VALUES (1, 'x', '2023-02-29');")[0][2].startswith("Fecha no válida")
    assert errors_of("SELECT 1 FROM estudiantes WHERE ingreso = '2023-1-5';")[0][2].startswith("Fecha no válida")


def check_dml_annotations():
    i = first("INSERT INTO estudiantes (nombre, id) VALUES ('x', 1);")
    assert i.schema.name == "estudiantes" and i.target_indexes == [1, 0]
    assert first("INSERT INTO estudiantes VALUES (1, 'x', 2, 3.5, TRUE, '2024-01-01');").target_indexes == [0, 1, 2, 3, 4, 5]
    assert first("UPDATE estudiantes SET edad = 1;").schema.name == "estudiantes"
    assert first("DELETE FROM cursos;").schema.name == "cursos"


# ── errores sin cascadas ──────────────────────────────────

def check_no_cascading_errors():
    assert len(errors_of("SELECT 1 FROM estudiantes WHERE nmbre = 1 AND edad = 'x';")) == 2      # uno por cada problema real
    assert len(errors_of("SELECT a, b FROM nada WHERE a > 1 ORDER BY b;")) == 1                  # solo la tabla que no existe
    assert len(errors_of("SELECT x FROM nada INNER JOIN estudiantes ON 1 = 1;")) == 1
    assert len(errors_of("SELECT nombre FROM estudiantes WHERE id IN (SELECT id FROM fantasma);")) == 1
    assert len(errors_of("SELECT nmbre + 1 FROM estudiantes WHERE nmbre > 2;")) == 2            # la columna mala, en sus dos usos
    # una columna mal escrita en un INSERT no debe hacer que parezcan «faltar» las columnas NOT NULL
    errs = errors_of("INSERT INTO estudiantes (id, nmbre) VALUES (1, 'x');")
    assert len(errs) == 1 and "'nmbre' no existe" in errs[0][2]
    assert len(errors_of("INSERT INTO estudiantes (nombre, edad) VALUES ('x', 1);")) == 1       # y aquí sí falta `id`


def check_errors_are_sorted_by_position():
    errs = errors_of("SELECT id FROM estudiantes e INNER JOIN cursos c ON c.id = e.nada;")
    assert len(errs) == 2 and [(l, c) for l, c, _ in errs] == sorted((l, c) for l, c, _ in errs)


# ── efectos de los CREATE y DROP ──────────────────────────

def check_ddl_effects_use_a_copy():
    original = Catalog()
    script, result = analyzed("CREATE TABLE t (a INT);", original)
    assert result.catalog.has_table("t") and not original.has_table("t")
    _, result = analyzed("DROP TABLE estudiantes;")
    assert not result.catalog.has_table("estudiantes") and UNI.has_table("estudiantes")
    assert result.catalog.find_index("idx_estudiantes_edad") is None and UNI.find_index("idx_estudiantes_edad") is not None


def check_failed_ddl_is_not_applied():
    _, result = analyzed("CREATE TABLE t (a INT, a INT);", Catalog())
    assert not result.ok and not result.catalog.has_table("t")
    _, result = analyzed("CREATE INDEX i ON estudiantes (nada);")
    assert result.catalog.find_index("i") is None


def check_create_table_effect_details():
    _, result = analyzed("CREATE TABLE t (id INT PRIMARY KEY, n VARCHAR(5) NOT NULL UNIQUE, d DATE);", Catalog())
    t = result.catalog.table("t")
    assert t.columns == [Column("id", "INT", None, True, False, False), Column("n", "VARCHAR", 5, False, True, True), Column("d", "DATE")]
    assert not t.columns[0].nullable and not t.columns[1].nullable and t.columns[2].nullable
    assert t.columns[0].must_be_unique and t.columns[1].must_be_unique and not t.columns[2].must_be_unique


# ── metadata.txt ──────────────────────────────────────────

def check_metadata_roundtrip():
    assert parse_metadata(format_metadata(UNI)) == UNI
    with open(os.path.join(HERE, "fixtures", "universidad", "metadata.txt"), encoding="utf-8") as f:
        assert f.read().replace("\r\n", "\n") == format_metadata(UNI)
    with tempfile.TemporaryDirectory() as folder:
        save_catalog(UNI, folder)
        assert load_catalog(folder) == UNI
        assert load_catalog(os.path.join(folder, "no_existe")) == Catalog()      # una base nueva todavía no tiene metadata.txt


def check_metadata_hand_written():
    text = "# comentario\n\ntable Personas\n  column Id int primary key\n  column Nombre varchar(20) not null unique\n  index idx_p nombre\n"
    catalog = parse_metadata(text.replace("\n", "\r\n"))                   # también con saltos de línea de Windows
    table = catalog.table("personas")
    assert table.name == "Personas"
    assert table.columns == [Column("Id", "INT", None, primary_key=True), Column("Nombre", "VARCHAR", 20, not_null=True, unique=True)]
    assert table.indexes == [Index("idx_p", "Personas", "Nombre")]         # el índice guarda la columna como se definió


def check_metadata_errors():
    bad = [
        ("table t\n  column a TEXT\n", 2, "Tipo no válido"),
        ("column a INT\n", 1, "Se esperaba 'table NOMBRE'"),
        ("table t\n  column a INT\n  index i b\n", 3, "no existe en 't'"),
        ("table t\n", 1, "no tiene columnas"),
        ("table t\n  column a INT PRIMARY KEY\n  column b INT PRIMARY KEY\n", 3, "más de una columna PRIMARY KEY"),
        ("table t\n  column a INT\ntable T\n  column b INT\n", 3, "está repetida"),
        ("table t\n  column a VARCHAR(0)\n", 2, "largo mayor que cero"),
        ("table t\n  column a INT\n  column A INT\n", 3, "está repetida"),
        ("table t\n  column a INT\ntable u\n  column b INT\n  index i a\n", 5, "no existe en 'u'"),
        ("table t\n  column a INT\n  index i a\ntable u\n  column b INT\n  index i b\n", 6, "está repetido"),
        ("table t\n  foo bar\n", 2, "Se esperaba 'column' o 'index'"),
        ("table t\n  column a INT NOT NULLS\n", 2, "Restricción no reconocida"),
        ("  column a INT\n", 1, "antes de la primera 'table'"),
    ]
    for text, line, fragment in bad:
        try:
            parse_metadata(text)
        except MetadataError as e:
            assert e.line == line and fragment in e.message, f"{text!r}: línea {e.line}, {e.message!r}"
        else:
            raise AssertionError(f"debía fallar: {text!r}")


# ── robustez ──────────────────────────────────────────────

def check_never_crashes_on_valid_syntax():
    """Cualquier script que el parser acepta, el analizador lo recorre sin lanzar excepciones, con o sin esquema."""
    files = sorted(glob.glob(os.path.join(HERE, "ok", "*.sql")) + glob.glob(os.path.join(HERE, "ast", "*.sql")))
    assert len(files) >= 10
    for path in files:
        with open(path, encoding="utf-8") as f:
            sql = f.read()
        result = parse(sql)
        assert result.ok, path
        for catalog in (UNI, Catalog()):
            analyze_script(build_ast(result), catalog)


CASES = [
    ("tipos de las expresiones", check_expression_types),
    ("tipos de las funciones de agregación", check_aggregate_types),
    ("nombres de las columnas de salida", check_output_names),
    ("expansión de * y tabla.*", check_star_expansion),
    ("tablas resueltas de FROM y JOIN", check_sources_annotation),
    ("a qué columna se resuelve cada referencia", check_bindings),
    ("subconsultas correlacionadas (profundidad 1 y 2)", check_correlated_subqueries),
    ("una columna de la consulta interna tapa a la de afuera", check_inner_scope_wins),
    ("ORDER BY usa los alias del SELECT, solo ahí", check_order_by_alias),
    ("un ON solo ve las tablas de su izquierda", check_join_condition_visibility),
    ("los nombres no distinguen mayúsculas", check_names_are_case_insensitive),
    ("un texto se interpreta como fecha cuando corresponde", check_date_coercion),
    ("anotaciones de INSERT, UPDATE y DELETE", check_dml_annotations),
    ("un error no provoca errores en cascada", check_no_cascading_errors),
    ("los errores salen ordenados por posición", check_errors_are_sorted_by_position),
    ("CREATE y DROP se aplican a una copia del catálogo", check_ddl_effects_use_a_copy),
    ("un CREATE o DROP con errores no se aplica", check_failed_ddl_is_not_applied),
    ("el CREATE TABLE deja la tabla con sus restricciones", check_create_table_effect_details),
    ("metadata.txt: ida y vuelta", check_metadata_roundtrip),
    ("metadata.txt: escrito a mano, con comentarios y CRLF", check_metadata_hand_written),
    ("metadata.txt: errores con su línea", check_metadata_errors),
    ("el analizador no falla con ningún script válido", check_never_crashes_on_valid_syntax),
]
