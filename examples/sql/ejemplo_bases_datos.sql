CREATE DATABASE universidad;
SHOW DATABASES;
USE universidad;
CREATE TABLE estudiantes (id INT PRIMARY KEY, nombre VARCHAR(50));
INSERT INTO estudiantes VALUES (1, 'Ana');
INSERT INTO estudiantes VALUES (2, 'Carlos');
SHOW TABLES;
SELECT * FROM estudiantes ORDER BY id;
