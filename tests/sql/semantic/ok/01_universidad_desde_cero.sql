-- Base de datos de ejemplo del enunciado: estudiantes, cursos e inscripciones.
-- Sirve para probar todo el SQL requerido.

CREATE TABLE estudiantes (
    id       INT PRIMARY KEY,
    nombre   VARCHAR(50) NOT NULL,
    edad     INT,
    promedio FLOAT,
    activo   BOOLEAN,
    ingreso  DATE
);
CREATE TABLE cursos (
    id       INT PRIMARY KEY,
    nombre   VARCHAR(50) NOT NULL,
    creditos INT
);
CREATE TABLE inscripciones (
    estudiante_id INT,
    curso_id      INT,
    nota          FLOAT
);

INSERT INTO estudiantes VALUES
    (1, 'Ana Lopez',   20, 85.5,  TRUE,  '2023-01-16'),
    (2, 'Luis Perez',  17, 72.0,  TRUE,  '2024-01-15'),
    (3, 'Marta Diaz',  22, 91.25, TRUE,  '2021-07-20'),
    (4, 'Carlos Ruiz', 19, 60.0,  FALSE, '2023-07-17'),
    (5, 'Sofia Mena',  18, 78.75, TRUE,  '2024-01-15'),
    (6, 'Diego Soto',  21, 66.5,  TRUE,  '2022-01-17');
INSERT INTO cursos VALUES
    (1, 'Compiladores',   5),
    (2, 'Bases de Datos', 4),
    (3, 'Redes',          4),
    (4, 'Calculo',        5);
INSERT INTO inscripciones VALUES
    (1, 1, 90.0), (1, 3, 80.5), (2, 2, 70.0), (3, 1, 95.0),
    (3, 3, 88.0), (3, 4, 92.5), (4, 3, 55.0), (5, 3, 77.0);

CREATE INDEX idx_estudiantes_edad ON estudiantes (edad);
CREATE INDEX idx_inscripciones_curso ON inscripciones (curso_id);

-- Consultas
SELECT nombre FROM estudiantes WHERE edad >= 18;

SELECT nombre
FROM estudiantes
WHERE id IN (SELECT estudiante_id
             FROM inscripciones
             WHERE curso_id = 3);

SELECT e.nombre, c.nombre AS curso, i.nota
FROM estudiantes e
INNER JOIN inscripciones i ON e.id = i.estudiante_id
INNER JOIN cursos c ON c.id = i.curso_id
ORDER BY e.nombre, c.nombre;

SELECT c.nombre, COUNT(*) AS inscritos, AVG(i.nota) AS promedio
FROM cursos c
INNER JOIN inscripciones i ON c.id = i.curso_id
GROUP BY c.nombre
HAVING COUNT(*) >= 2
ORDER BY inscritos DESC;

SELECT nombre
FROM estudiantes e
WHERE NOT EXISTS (SELECT * FROM inscripciones i WHERE i.estudiante_id = e.id);

SELECT nombre FROM estudiantes WHERE promedio > (SELECT AVG(promedio) FROM estudiantes);

UPDATE estudiantes SET activo = TRUE WHERE id = 4;
DELETE FROM inscripciones WHERE nota < 60;
