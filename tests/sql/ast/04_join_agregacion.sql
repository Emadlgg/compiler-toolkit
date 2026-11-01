SELECT c.nombre, COUNT(*) AS inscritos, AVG(i.nota)
FROM cursos c
INNER JOIN inscripciones i ON c.id = i.curso_id
GROUP BY c.nombre
HAVING COUNT(*) >= 2
ORDER BY inscritos DESC, c.nombre;
