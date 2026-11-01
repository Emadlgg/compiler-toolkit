-- statements: 6
SELECT COUNT(*) FROM estudiantes;
SELECT COUNT(id), SUM(edad), AVG(promedio), MIN(edad), MAX(promedio) FROM estudiantes;
SELECT activo, COUNT(*) AS total, AVG(edad) FROM estudiantes GROUP BY activo;
SELECT edad, COUNT(*) FROM estudiantes GROUP BY edad HAVING COUNT(*) > 1 AND AVG(promedio) >= 70 ORDER BY edad DESC;
SELECT SUM(edad * 2) FROM estudiantes WHERE activo = TRUE;
SELECT MAX(edad) - MIN(edad) AS rango FROM estudiantes;
