-- db: universidad
INSERT INTO estudiantes VALUES (1, 'Ana');
INSERT INTO estudiantes (id, nombre) VALUES (1, 'Ana', 3);
INSERT INTO estudiantes (id, nombre) VALUES ('uno', 'x');
INSERT INTO estudiantes (id, nombre) VALUES (1, 5);
INSERT INTO estudiantes (nombre, edad) VALUES ('Ana', 20);
INSERT INTO estudiantes (id, nombre) VALUES (1, NULL);
INSERT INTO estudiantes (id, nombre, edad) VALUES (1, 'Ana', 2.5);
INSERT INTO estudiantes (id, nombre) VALUES (1, 'Un nombre larguísimo que pasa de los cincuenta caracteres permitidos');
INSERT INTO estudiantes (id, id, nombre) VALUES (1, 2, 'x');
INSERT INTO estudiantes (id, nombre, ingreso) VALUES (1, 'x', 'ayer');
INSERT INTO estudiantes (id, nombre, edad) VALUES (1, 'x', edad + 1);
