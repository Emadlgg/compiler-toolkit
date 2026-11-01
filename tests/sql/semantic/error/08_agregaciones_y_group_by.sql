-- db: universidad
SELECT * FROM estudiantes WHERE COUNT(*) > 1;
SELECT SUM(COUNT(*)) FROM estudiantes;
SELECT SUM(nombre) FROM estudiantes;
SELECT MAX(activo) FROM estudiantes;
SELECT nombre, COUNT(*) FROM estudiantes;
SELECT activo, nombre FROM estudiantes GROUP BY activo;
SELECT * FROM estudiantes GROUP BY activo;
SELECT activo, COUNT(*) FROM estudiantes GROUP BY activo HAVING edad > 3;
SELECT activo FROM estudiantes GROUP BY activo ORDER BY nombre;
