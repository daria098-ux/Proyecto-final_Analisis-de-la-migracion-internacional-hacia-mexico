CREATE DATABASE migracion_mexico;
USE migracion_mexico;
-- creo que poe el momento esto puede funcionar 
CREATE TABLE regiones (id_region INT PRIMARY KEY AUTO_INCREMENT,
nombre VARCHAR(100) NOT NULL UNIQUE);
CREATE TABLE paises (id_pais INT PRIMARY KEY AUTO_INCREMENT,
nombre VARCHAR(150) NOT NULL UNIQUE,
codigo_iso VARCHAR(10) UNIQUE,
id_region INT,
FOREIGN KEY (id_region) REFERENCES regiones (id_region));
CREATE TABLE categorias_motivo (id_categoria INT PRIMARY KEY AUTO_INCREMENT,
nombre VARCHAR(100) NOT NULL UNIQUE);
CREATE TABLE motivos (id_motivo INT PRIMARY KEY AUTO_INCREMENT,
nombre VARCHAR(150) NOT NULL,
id_categoria INT,
FOREIGN KEY (id_categoria) REFERENCES categorias_motivo (id_categoria));
CREATE TABLE periodos (id_periodo INT PRIMARY KEY AUTO_INCREMENT,
anio YEAR NOT NULL);
CREATE TABLE niveles_socioeconomicos (id_nivel INT PRIMARY KEY AUTO_INCREMENT,
descripcion VARCHAR(100) NOT NULL UNIQUE);
CREATE TABLE riesgos (id_riesgo INT PRIMARY KEY AUTO_INCREMENT,
descripcion VARCHAR(250) NOT NULL,
tipo ENUM('Fisico', 'Legal', 'Economico', 'Social') NOT NULL);
CREATE TABLE impactos (id_impacto INT PRIMARY KEY AUTO_INCREMENT,
tipo ENUM('Social','Economico') NOT NULL,
descripcion VARCHAR(250) NOT NULL);
CREATE TABLE migrantes (id_migrante INT PRIMARY KEY AUTO_INCREMENT,
edad INT CHECK (edad >= 0),
sexo ENUM('Masculino','Femenino','Otro') NOT NULL,
id_pais_origen INT,
id_nivel_socioeconomico INT,
FOREIGN KEY (id_pais_origen) REFERENCES paises (id_pais),
FOREIGN KEY (id_nivel_socioeconomico) REFERENCES niveles_socioeconomicos (id_nivel));
CREATE TABLE migraciones (id_migracion INT PRIMARY KEY AUTO_INCREMENT,id_migrante INT NOT NULL,
id_pais_destino INT NOT NULL,
id_motivo INT NOT NULL,
id_periodo INT NOT NULL,
status_ ENUM('En transito', 'Establecido', 'Retornado', 'Deportado') DEFAULT 'En transito',
FOREIGN KEY (id_migrante) REFERENCES migrantes(id_migrante),
FOREIGN KEY (id_pais_destino) REFERENCES paises(id_pais),
FOREIGN KEY (id_motivo) REFERENCES motivos(id_motivo),
FOREIGN KEY (id_periodo) REFERENCES periodos (id_periodo),
CONSTRAINT uc_migrante_evento UNIQUE (id_migrante, id_pais_destino, id_periodo));
CREATE TABLE migracion_riesgo (id INT PRIMARY KEY AUTO_INCREMENT,
id_migracion INT NOT NULL,
id_riesgo INT NOT NULL,
FOREIGN KEY (id_migracion) REFERENCES migraciones (id_migracion),
FOREIGN KEY (id_riesgo) REFERENCES riesgos (id_riesgo));
CREATE TABLE migracion_impacto (id INT PRIMARY KEY AUTO_INCREMENT,
id_migracion INT NOT NULL,
id_impacto INT NOT NULL,
FOREIGN KEY (id_migracion) REFERENCES migraciones (id_migracion),
FOREIGN KEY (id_impacto) REFERENCES impactos (id_impacto));
CREATE TABLE estadisticas_globales (id INT PRIMARY KEY AUTO_INCREMENT,
anio YEAR NOT NULL,
id_pais INT NOT NULL,
total_migrantes INT DEFAULT 0,
porcentaje_mundial DECIMAL(5,2),
FOREIGN KEY (id_pais) REFERENCES paises (id_pais));
CREATE TABLE audit (id_audit INT PRIMARY KEY AUTO_INCREMENT,
affected_table VARCHAR(100),
action_type ENUM('Insert', 'Update', 'Delete'),
action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
db_user VARCHAR(100));

CREATE TRIGGER tr_regiones_insert AFTER INSERT ON regiones FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('regiones', 'Insert', USER());
CREATE TRIGGER tr_regiones_update AFTER UPDATE ON regiones FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('regiones', 'Update', USER());
CREATE TRIGGER tr_regiones_delete AFTER DELETE ON regiones FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('regiones', 'Delete', USER());
CREATE TRIGGER tr_paises_insert AFTER INSERT ON paises FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('paises', 'Insert', USER());
CREATE TRIGGER tr_paises_update AFTER UPDATE ON paises FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('paises', 'Update', USER());
CREATE TRIGGER tr_paises_delete AFTER DELETE ON paises FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('paises', 'Delete', USER());
CREATE TRIGGER tr_catmotivo_insert AFTER INSERT ON categorias_motivo FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('categorias_motivo', 'Insert', USER());
CREATE TRIGGER tr_catmotivo_update AFTER UPDATE ON categorias_motivo FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('categorias_motivo', 'Update', USER());
CREATE TRIGGER tr_catmotivo_delete AFTER DELETE ON categorias_motivo FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('categorias_motivo', 'Delete', USER());
CREATE TRIGGER tr_motivos_insert AFTER INSERT ON motivos FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('motivos', 'Insert', USER());
CREATE TRIGGER tr_motivos_update AFTER UPDATE ON motivos FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('motivos', 'Update', USER());
CREATE TRIGGER tr_motivos_delete AFTER DELETE ON motivos FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('motivos', 'Delete', USER());
CREATE TRIGGER tr_migrantes_insert AFTER INSERT ON migrantes FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migrantes', 'Insert', USER());
CREATE TRIGGER tr_migrantes_update AFTER UPDATE ON migrantes FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migrantes', 'Update', USER());
CREATE TRIGGER tr_migrantes_delete AFTER DELETE ON migrantes FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migrantes', 'Delete', USER());
CREATE TRIGGER tr_migraciones_insert AFTER INSERT ON migraciones FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migraciones', 'Insert', USER());
CREATE TRIGGER tr_migraciones_update AFTER UPDATE ON migraciones FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migraciones', 'Update', USER());
CREATE TRIGGER tr_migraciones_delete AFTER DELETE ON migraciones FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migraciones', 'Delete', USER());
CREATE TRIGGER tr_riesgos_insert AFTER INSERT ON riesgos FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('riesgos', 'Insert', USER());
CREATE TRIGGER tr_riesgos_update AFTER UPDATE ON riesgos FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('riesgos', 'Update', USER());
CREATE TRIGGER tr_riesgos_delete AFTER DELETE ON riesgos FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('riesgos', 'Delete', USER());
CREATE TRIGGER tr_impactos_insert AFTER INSERT ON impactos FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('impactos', 'Insert', USER());
CREATE TRIGGER tr_impactos_update AFTER UPDATE ON impactos FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('impactos', 'Update', USER());
CREATE TRIGGER tr_impactos_delete AFTER DELETE ON impactos FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('impactos', 'Delete', USER());
DELIMITER //

CREATE PROCEDURE sp_create_region(IN p_nombre VARCHAR(100))
BEGIN INSERT INTO regiones (nombre) VALUES (p_nombre); END //
CREATE PROCEDURE sp_read_region(IN p_id INT)
BEGIN SELECT * FROM regiones WHERE id_region = p_id; END //
CREATE PROCEDURE sp_update_region(IN p_id INT, IN p_nombre VARCHAR(100))
BEGIN UPDATE regiones SET nombre = p_nombre WHERE id_region = p_id; END //
CREATE PROCEDURE sp_delete_region(IN p_id INT)
BEGIN DELETE FROM regiones WHERE id_region = p_id; END //
CREATE PROCEDURE sp_create_pais(IN p_nombre VARCHAR(150), IN p_iso VARCHAR(10), IN p_region INT)
BEGIN INSERT INTO paises (nombre, codigo_iso, id_region) VALUES (p_nombre, p_iso, p_region); END //
CREATE PROCEDURE sp_read_pais(IN p_id INT)
BEGIN SELECT * FROM paises WHERE id_pais = p_id; END //
CREATE PROCEDURE sp_update_pais(IN p_id INT, IN p_nombre VARCHAR(150))
BEGIN UPDATE paises SET nombre = p_nombre WHERE id_pais = p_id; END //
CREATE PROCEDURE sp_delete_pais(IN p_id INT)
BEGIN DELETE FROM paises WHERE id_pais = p_id; END //
CREATE PROCEDURE sp_create_categoria(IN p_nombre VARCHAR(100))
BEGIN INSERT INTO categorias_motivo (nombre) VALUES (p_nombre); END //
CREATE PROCEDURE sp_read_categoria(IN p_id INT)
BEGIN SELECT * FROM categorias_motivo WHERE id_categoria = p_id; END //
CREATE PROCEDURE sp_update_categoria(IN p_id INT, IN p_nombre VARCHAR(100))
BEGIN UPDATE categorias_motivo SET nombre = p_nombre WHERE id_categoria = p_id; END //
CREATE PROCEDURE sp_delete_categoria(IN p_id INT)
BEGIN DELETE FROM categorias_motivo WHERE id_categoria = p_id; END //
CREATE PROCEDURE sp_create_motivo(IN p_nombre VARCHAR(150), IN p_cat INT)
BEGIN INSERT INTO motivos (nombre, id_categoria) VALUES (p_nombre, p_cat); END //
CREATE PROCEDURE sp_read_motivo(IN p_id INT)
BEGIN SELECT * FROM motivos WHERE id_motivo = p_id; END //
CREATE PROCEDURE sp_update_motivo(IN p_id INT, IN p_nombre VARCHAR(150))
BEGIN UPDATE motivos SET nombre = p_nombre WHERE id_motivo = p_id; END //
CREATE PROCEDURE sp_delete_motivo(IN p_id INT)
BEGIN DELETE FROM motivos WHERE id_motivo = p_id; END //
CREATE PROCEDURE sp_create_migrante(IN p_edad INT, IN p_sexo VARCHAR(20), IN p_pais INT, IN p_nivel INT)
BEGIN INSERT INTO migrantes (edad, sexo, id_pais_origen, id_nivel_socioeconomico) VALUES (p_edad, p_sexo, p_pais, p_nivel); END //
CREATE PROCEDURE sp_read_migrante(IN p_id INT)
BEGIN SELECT * FROM migrantes WHERE id_migrante = p_id; END //
CREATE PROCEDURE sp_update_migrante(IN p_id INT, IN p_edad INT, IN p_nivel INT)
BEGIN UPDATE migrantes SET edad = p_edad, id_nivel_socioeconomico = p_nivel WHERE id_migrante = p_id; END //
CREATE PROCEDURE sp_delete_migrante(IN p_id INT)
BEGIN DELETE FROM migrantes WHERE id_migrante = p_id; END //
CREATE PROCEDURE sp_create_migracion(IN p_migrante INT, IN p_destino INT, IN p_motivo INT, IN p_periodo INT)
BEGIN INSERT INTO migraciones (id_migrante, id_pais_destino, id_motivo, id_periodo) VALUES (p_migrante, p_destino, p_motivo, p_periodo); END //
CREATE PROCEDURE sp_read_migracion(IN p_id INT)
BEGIN SELECT * FROM migraciones WHERE id_migracion = p_id; END //
CREATE PROCEDURE sp_update_migracion(IN p_id INT, IN p_status VARCHAR(20))
BEGIN UPDATE migraciones SET status_= p_status WHERE id_migracion = p_id; END //
CREATE PROCEDURE sp_delete_migracion(IN p_id INT)
BEGIN DELETE FROM migraciones WHERE id_migracion = p_id; END //
CREATE PROCEDURE sp_create_riesgo(IN p_desc VARCHAR(250), IN p_tipo VARCHAR(20))
BEGIN INSERT INTO riesgos (descripcion, tipo) VALUES (p_desc, p_tipo); END //
CREATE PROCEDURE sp_read_riesgo(IN p_id INT)
BEGIN SELECT * FROM riesgos WHERE id_riesgo = p_id; END //
CREATE PROCEDURE sp_update_riesgo(IN p_id INT, IN p_desc VARCHAR(250))
BEGIN UPDATE riesgos SET descripcion = p_desc WHERE id_riesgo = p_id; END //
CREATE PROCEDURE sp_delete_riesgo(IN p_id INT)
BEGIN DELETE FROM riesgos WHERE id_riesgo = p_id; END //
CREATE PROCEDURE sp_create_impacto(IN p_tipo VARCHAR(20), IN p_desc VARCHAR(250))
BEGIN INSERT INTO impactos (tipo, descripcion) VALUES (p_tipo, p_desc); END //
CREATE PROCEDURE sp_read_impacto(IN p_id INT)
BEGIN SELECT * FROM impactos WHERE id_impacto = p_id; END //
CREATE PROCEDURE sp_update_impacto(IN p_id INT, IN p_desc VARCHAR(250))
BEGIN UPDATE impactos SET descripcion = p_desc WHERE id_impacto = p_id; END //
CREATE PROCEDURE sp_delete_impacto(IN p_id INT)
BEGIN DELETE FROM impactos WHERE id_impacto = p_id; END //
CREATE PROCEDURE sp_create_estadistica(IN p_anio YEAR, IN p_pais INT, IN p_total INT, IN p_pct DECIMAL(5,2))
BEGIN INSERT INTO estadisticas_globales (anio, id_pais, total_migrantes, porcentaje_mundial) VALUES (p_anio, p_pais, p_total, p_pct); END //
CREATE PROCEDURE sp_read_estadistica(IN p_id INT)
BEGIN SELECT * FROM estadisticas_globales WHERE id = p_id; END //
CREATE PROCEDURE sp_read_all_estadisticas()
BEGIN SELECT * FROM estadisticas_globales ORDER BY anio DESC; END //
DELIMITER ;

CREATE VIEW vw_motivos_principales AS
SELECT cm.nombre AS categoria,m.nombre AS motivo,COUNT(mg.id_migracion) AS total_migraciones
FROM migraciones mg
JOIN motivos m ON mg.id_motivo = m.id_motivo
JOIN categorias_motivo cm ON m.id_categoria = cm.id_categoria
JOIN paises pd ON mg.id_pais_destino = pd.id_pais
WHERE pd.nombre = 'Mexico'
GROUP BY cm.nombre,m.nombre
ORDER BY total_migraciones DESC;

CREATE VIEW vw_paises_origen AS
SELECT p.nombre AS pais_origen,r.nombre AS region,COUNT(mg.id_migracion) AS total_migrantes
FROM migraciones mg
JOIN migrantes mi ON mg.id_migrante = mi.id_migrante
JOIN paises p ON mi.id_pais_origen = p.id_pais
JOIN regiones r ON p.id_region = r.id_region
JOIN paises pd ON mg.id_pais_destino = pd.id_pais
WHERE pd.nombre = 'Mexico'
GROUP BY p.nombre, r.nombre
ORDER BY total_migrantes DESC;

CREATE VIEW vw_comparacion_internacional AS
SELECT p.nombre AS pais_destino,eg.anio,eg.total_migrantes,eg.porcentaje_mundial
FROM estadisticas_globales eg
JOIN paises p ON eg.id_pais = p.id_pais
ORDER BY eg.anio DESC, eg.total_migrantes DESC;

CREATE VIEW vw_riesgos_migrantes AS
SELECT ri.tipo AS tipo_riesgo, ri.descripcion AS riesgo,COUNT(mr.id) AS casos
FROM migracion_riesgo mr
JOIN riesgos ri ON mr.id_riesgo = ri.id_riesgo
JOIN migraciones mg ON mr.id_migracion = mg.id_migracion
JOIN paises pd ON mg.id_pais_destino = pd.id_pais
WHERE pd.nombre = 'Mexico'
GROUP BY ri.tipo, ri.descripcion
ORDER BY casos DESC;

CREATE VIEW vw_impacto_mexico AS
SELECT im.tipo AS tipo_impacto,im.descripcion AS impacto,COUNT(mi2.id) AS frecuencia
FROM migracion_impacto mi2
JOIN impactos im ON mi2.id_impacto = im.id_impacto
JOIN migraciones mg ON mi2.id_migracion = mg.id_migracion
JOIN paises pd ON mg.id_pais_destino = pd.id_pais
WHERE pd.nombre = 'Mexico'
GROUP BY im.tipo, im.descripcion
ORDER BY tipo_impacto, frecuencia DESC;

CREATE VIEW vw_perfil_demografico AS
SELECT mi.sexo, ns.descripcion AS nivel_socioeconomico,
ROUND(AVG(mi.edad), 1) AS edad_promedio,COUNT(mg.id_migracion) AS total
FROM migraciones mg
JOIN migrantes mi ON mg.id_migrante = mi.id_migrante
JOIN niveles_socioeconomicos ns ON mi.id_nivel_socioeconomico = ns.id_nivel
JOIN paises pd ON mg.id_pais_destino = pd.id_pais
WHERE pd.nombre = 'Mexico'
GROUP BY mi.sexo, ns.descripcion;