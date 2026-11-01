-- db: universidad
SELECT * FROM estudiantes WHERE edad = 'abc';
SELECT * FROM estudiantes WHERE nombre + 1 > 2;
SELECT * FROM estudiantes WHERE edad AND activo;
SELECT * FROM estudiantes WHERE activo < TRUE;
SELECT * FROM estudiantes WHERE edad;
SELECT * FROM estudiantes WHERE ingreso = 5;
SELECT * FROM estudiantes WHERE ingreso = 'no es fecha';
SELECT -nombre FROM estudiantes;
SELECT * FROM estudiantes WHERE NOT edad;
SELECT * FROM estudiantes WHERE ingreso = DATE '2023-02-30';
