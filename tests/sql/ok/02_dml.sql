-- statements: 9
INSERT INTO estudiantes VALUES (1, 'Ana', 20, 85.5, TRUE, '2004-03-15');
INSERT INTO estudiantes (id, nombre, edad) VALUES (2, 'Luis', 17);
INSERT INTO estudiantes VALUES (3, 'O''Brien', 19, 70.25, FALSE, DATE '2005-01-02'), (4, 'Marta', 22, 90, TRUE, '2002-11-30');
INSERT INTO cursos VALUES (1, 'Compiladores');
UPDATE estudiantes SET edad = 21;
UPDATE estudiantes SET edad = edad + 1, promedio = promedio * 1.1 WHERE id = 1;
UPDATE estudiantes SET activo = FALSE WHERE edad < 18 OR promedio IS NULL;
DELETE FROM estudiantes WHERE id = 2;
DELETE FROM inscripciones;
