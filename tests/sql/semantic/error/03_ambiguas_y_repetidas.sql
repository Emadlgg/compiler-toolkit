-- db: universidad
SELECT id FROM estudiantes e INNER JOIN cursos c ON e.id = c.id;
SELECT nombre FROM estudiantes e INNER JOIN cursos c ON e.id = c.id;
SELECT * FROM estudiantes e INNER JOIN cursos e ON e.id = e.id;
SELECT * FROM estudiantes INNER JOIN estudiantes ON 1 = 1;
SELECT * FROM estudiantes e INNER JOIN cursos c ON c.id = i.curso_id INNER JOIN inscripciones i ON i.curso_id = c.id;
