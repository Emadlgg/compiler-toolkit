SELECT nombre
FROM estudiantes
WHERE edad >= 18;

SELECT nombre
FROM estudiantes
WHERE id IN (SELECT estudiante_id
             FROM inscripciones
             WHERE curso_id = 3);
