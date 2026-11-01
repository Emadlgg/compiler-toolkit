CREATE TABLE estudiantes (id INT PRIMARY KEY, nombre VARCHAR(50) NOT NULL, edad INT, activo BOOLEAN, ingreso DATE);
CREATE TABLE cursos (id INT, nombre VARCHAR(40) UNIQUE NOT NULL);
CREATE INDEX idx_edad ON estudiantes (edad);
DROP INDEX idx_edad;
DROP TABLE cursos;
