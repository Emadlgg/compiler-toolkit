-- db: universidad
SELECT nmbre FROM estudiantes;
SELECT nombre FROM estudiantes WHERE edd > 3;
SELECT e.nombr FROM estudiantes e;
UPDATE estudiantes SET edda = 1;
INSERT INTO estudiantes (id, nmbre) VALUES (1, 'x');
CREATE INDEX i1 ON estudiantes (edda);
SELECT nombre FROM estudiantes ORDER BY promedioo;
SELECT x.nombre FROM estudiantes e;
