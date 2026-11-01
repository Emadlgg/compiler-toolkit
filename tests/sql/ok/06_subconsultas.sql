-- statements: 8
SELECT nombre FROM estudiantes WHERE id IN (SELECT estudiante_id FROM inscripciones WHERE curso_id = 3);
SELECT nombre FROM estudiantes WHERE id NOT IN (SELECT estudiante_id FROM inscripciones);
SELECT nombre FROM estudiantes WHERE id IN (1, 2, 3) AND edad NOT IN (17, 18);
SELECT nombre FROM estudiantes e WHERE EXISTS (SELECT 1 FROM inscripciones i WHERE i.estudiante_id = e.id);
SELECT nombre FROM estudiantes e WHERE NOT EXISTS (SELECT * FROM inscripciones i WHERE i.estudiante_id = e.id);
SELECT nombre FROM estudiantes WHERE edad > (SELECT AVG(edad) FROM estudiantes);
SELECT nombre FROM estudiantes WHERE promedio = (SELECT MAX(promedio) FROM estudiantes) OR edad < (SELECT MIN(edad) FROM estudiantes WHERE activo = TRUE);
SELECT nombre FROM estudiantes WHERE id IN (SELECT estudiante_id FROM inscripciones WHERE curso_id IN (SELECT id FROM cursos WHERE nombre = 'Compiladores'));
