-- db: universidad
SELECT * FROM estudiantez;
INSERT INTO nada VALUES (1);
UPDATE nada SET a = 1;
DELETE FROM nada;
DROP TABLE nada;
CREATE INDEX i ON nada (a);
SELECT * FROM estudiantes e INNER JOIN cursoz c ON c.id = e.id;
