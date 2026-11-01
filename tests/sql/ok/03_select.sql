-- statements: 10
SELECT * FROM estudiantes;
SELECT nombre, edad FROM estudiantes;
SELECT nombre AS alumno, edad edad_actual FROM estudiantes e;
SELECT e.* FROM estudiantes AS e;
SELECT nombre FROM estudiantes WHERE edad >= 18;
SELECT nombre FROM estudiantes WHERE edad >= 18 AND (activo = TRUE OR promedio > 60.5) AND NOT edad = 30;
SELECT nombre FROM estudiantes WHERE edad <> 20 AND edad != 21 AND edad <= 40 AND edad < 50;
SELECT nombre, edad * 2 + 1 AS doble, -edad, (edad + 1) / 2 FROM estudiantes ORDER BY edad DESC, nombre ASC, id;
SELECT nombre FROM estudiantes WHERE nacimiento > DATE '2000-01-01' AND nombre IS NOT NULL AND promedio IS NULL;
SELECT 'texto con ''comilla''', 1, 2.5, TRUE, NULL FROM estudiantes;
