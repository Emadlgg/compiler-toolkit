CREATE TABLE estudiantes (id INT PRIMARY KEY, nombre VARCHAR(50) NOT NULL, edad INT);
INSERT INTO estudiantes VALUES (1, 'Carlos', 20);
INSERT INTO estudiantes VALUES (2, 'Maria', 22);
INSERT INTO estudiantes VALUES (3, 'Ana', 17);
SELECT id, nombre, edad FROM estudiantes WHERE edad >= 18 ORDER BY edad DESC;
UPDATE estudiantes SET edad = 23 WHERE id = 1;
DELETE FROM estudiantes WHERE edad < 18;
SELECT * FROM estudiantes ORDER BY id;
