-- db: universidad
SELECT nombre FROM estudiantes WHERE id IN (SELECT estudiante_id, curso_id FROM inscripciones);
SELECT nombre FROM estudiantes WHERE edad > (SELECT edad, nombre FROM estudiantes);
SELECT nombre FROM estudiantes WHERE nombre IN (SELECT curso_id FROM inscripciones);
SELECT nombre, (SELECT MAX(edad) FROM estudiantes) FROM estudiantes;
UPDATE estudiantes SET edad = (SELECT MAX(edad) FROM estudiantes);
SELECT nombre FROM estudiantes WHERE id IN (SELECT id FROM fantasma);
