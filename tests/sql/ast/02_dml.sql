INSERT INTO estudiantes (id, nombre) VALUES (1, 'Ana'), (2, 'O''Brien');
INSERT INTO cursos VALUES (1, 'Redes', -5, 2.5, TRUE, NULL, DATE '2024-01-15');
UPDATE estudiantes SET edad = edad + 1, nombre = 'X' WHERE id = 1 AND activo = TRUE;
DELETE FROM estudiantes WHERE edad < 18 OR nombre IS NULL;
