SELECT nombre, edad FROM usuarios WHERE edad >= 18;
INSERT INTO usuarios (nombre, edad) VALUES ('Juan', 20);
UPDATE usuarios SET edad = 21 WHERE nombre = 'Juan';
DELETE FROM usuarios WHERE edad < 18;