-- statements: 5
SELECT e.nombre, c.nombre FROM estudiantes e INNER JOIN inscripciones i ON e.id = i.estudiante_id INNER JOIN cursos c ON c.id = i.curso_id;
SELECT * FROM estudiantes INNER JOIN inscripciones ON estudiantes.id = inscripciones.estudiante_id WHERE inscripciones.curso_id = 3;
SELECT e.nombre FROM estudiantes AS e JOIN inscripciones AS i ON i.estudiante_id = e.id AND i.curso_id > 1 ORDER BY e.nombre;
SELECT c.nombre, COUNT(*) FROM cursos c INNER JOIN inscripciones i ON c.id = i.curso_id GROUP BY c.nombre HAVING COUNT(*) > 2 ORDER BY c.nombre;
SELECT e.nombre FROM estudiantes e INNER JOIN inscripciones i ON e.id = i.estudiante_id WHERE i.curso_id IN (SELECT id FROM cursos WHERE nombre = 'Compiladores');
