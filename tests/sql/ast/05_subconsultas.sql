SELECT nombre FROM estudiantes e WHERE NOT EXISTS (SELECT * FROM inscripciones i WHERE i.estudiante_id = e.id);
SELECT nombre FROM estudiantes WHERE promedio > (SELECT AVG(promedio) FROM estudiantes) AND id NOT IN (1, 2);
