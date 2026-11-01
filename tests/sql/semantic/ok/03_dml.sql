-- db: universidad
INSERT INTO estudiantes VALUES (10, 'Ana', 20, 85.5, TRUE, '2004-03-15');
INSERT INTO estudiantes (id, nombre) VALUES (11, 'Luis'), (12, 'Marta');
INSERT INTO estudiantes (id, nombre, edad, promedio) VALUES (13, 'O''Brien', 19, 90);
INSERT INTO estudiantes (id, nombre, activo, ingreso) VALUES (14, 'Z', NULL, NULL);
INSERT INTO estudiantes (id, nombre, edad) VALUES (15, 'x', -3 + 10);
INSERT INTO estudiantes (nombre, id) VALUES ('orden distinto', 16);
UPDATE estudiantes SET edad = edad + 1, promedio = promedio * 1.1 WHERE id = 1;
UPDATE estudiantes SET activo = FALSE, ingreso = '2020-02-29' WHERE edad < 18 OR promedio IS NULL;
UPDATE estudiantes SET nombre = 'sin nombre' WHERE id IN (SELECT estudiante_id FROM inscripciones WHERE nota < 60);
DELETE FROM inscripciones WHERE nota < 60 AND curso_id <> 3;
DELETE FROM estudiantes;
