-- db: universidad
SELECT * FROM estudiantes;
SELECT e.*, c.nombre FROM estudiantes e INNER JOIN inscripciones i ON e.id = i.estudiante_id INNER JOIN cursos c ON c.id = i.curso_id;
SELECT nombre, edad * 2 + 1 AS doble FROM estudiantes WHERE edad >= 18 AND (activo OR promedio > 60.5) ORDER BY doble DESC, nombre;
SELECT nombre FROM estudiantes WHERE ingreso >= '2023-01-01' AND ingreso < DATE '2024-01-01';
SELECT activo, COUNT(*), AVG(edad), SUM(promedio), MIN(ingreso), MAX(nombre) FROM estudiantes GROUP BY activo HAVING COUNT(*) > 1 ORDER BY activo;
SELECT c.nombre, COUNT(*) AS inscritos FROM cursos c INNER JOIN inscripciones i ON c.id = i.curso_id GROUP BY c.nombre HAVING COUNT(*) >= 2 ORDER BY inscritos DESC;
SELECT nombre FROM estudiantes WHERE id IN (SELECT estudiante_id FROM inscripciones WHERE curso_id = 3);
SELECT nombre FROM estudiantes e WHERE NOT EXISTS (SELECT * FROM inscripciones i WHERE i.estudiante_id = e.id);
SELECT nombre FROM estudiantes e WHERE EXISTS (SELECT 1 FROM inscripciones i WHERE i.estudiante_id = e.id AND i.nota > e.promedio);
SELECT nombre FROM estudiantes WHERE promedio > (SELECT AVG(promedio) FROM estudiantes);
SELECT nombre FROM estudiantes WHERE id NOT IN (1, 2) AND nombre IS NOT NULL AND edad IN (SELECT creditos FROM cursos);
SELECT COUNT(*) FROM estudiantes;
SELECT 1 + 2 * 3, 'x', TRUE, NULL FROM cursos;
SELECT edad FROM estudiantes GROUP BY edad ORDER BY edad;
SELECT a.nombre FROM estudiantes a INNER JOIN estudiantes b ON a.edad = b.edad AND a.id <> b.id;
SELECT edad * 2, COUNT(*) FROM estudiantes GROUP BY edad * 2;
