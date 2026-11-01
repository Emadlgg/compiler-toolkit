-- db: universidad
UPDATE estudiantes SET edad = 'x';
UPDATE estudiantes SET nombre = NULL;
UPDATE estudiantes SET edad = 1, edad = 2;
UPDATE estudiantes SET edad = 1 WHERE edad;
UPDATE estudiantes SET promedio = nota + 1;
DELETE FROM estudiantes WHERE nombre;
DELETE FROM estudiantes WHERE id IN (SELECT estudiante_id FROM inscripciones WHERE nota);
