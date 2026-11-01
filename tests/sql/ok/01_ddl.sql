-- statements: 8
CREATE TABLE estudiantes (id INT PRIMARY KEY, nombre VARCHAR(50) NOT NULL, edad INT, promedio FLOAT, activo BOOLEAN, nacimiento DATE);
CREATE TABLE cursos (id INT PRIMARY KEY, nombre VARCHAR(40) UNIQUE NOT NULL);
CREATE TABLE inscripciones (estudiante_id INT, curso_id INT, fecha DATE);
DROP TABLE inscripciones;
CREATE INDEX idx_estudiantes_edad ON estudiantes (edad);
CREATE INDEX idx_cursos_nombre ON cursos(nombre);
DROP INDEX idx_estudiantes_edad;
DROP TABLE cursos;
