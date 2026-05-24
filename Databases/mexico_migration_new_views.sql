CREATE DATABASE mexico_migration;
USE mexico_migration;

CREATE TABLE regions (
    region_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE countries (
    country_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL UNIQUE,
    iso_code VARCHAR(10) UNIQUE,
    region_id INT,
    FOREIGN KEY (region_id) REFERENCES regions (region_id)
);

CREATE TABLE motive_categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE motives (
    motive_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    category_id INT,
    FOREIGN KEY (category_id) REFERENCES motive_categories (category_id)
);

CREATE TABLE periods (
    period_id INT PRIMARY KEY AUTO_INCREMENT,
    year YEAR NOT NULL
);

CREATE TABLE socioeconomic_levels (
    level_id INT PRIMARY KEY AUTO_INCREMENT,
    description VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE risks (
    risk_id INT PRIMARY KEY AUTO_INCREMENT,
    description VARCHAR(250) NOT NULL,
    type ENUM('Physical', 'Legal', 'Economic', 'Social') NOT NULL
);

CREATE TABLE impacts (
    impact_id INT PRIMARY KEY AUTO_INCREMENT,
    type ENUM('Social', 'Economic') NOT NULL,
    description VARCHAR(250) NOT NULL
);

CREATE TABLE migrants (
    migrant_id INT PRIMARY KEY AUTO_INCREMENT,
    age INT CHECK (age >= 0),
    sex ENUM('Male', 'Female', 'Other') NOT NULL,
    origin_country_id INT,
    socioeconomic_level_id INT,
    FOREIGN KEY (origin_country_id) REFERENCES countries (country_id),
    FOREIGN KEY (socioeconomic_level_id) REFERENCES socioeconomic_levels (level_id)
);

CREATE TABLE migrations (
    migration_id INT PRIMARY KEY AUTO_INCREMENT,
    migrant_id INT NOT NULL,
    destination_country_id INT NOT NULL,
    motive_id INT NOT NULL,
    period_id INT NOT NULL,
    status_ ENUM('In transit', 'Established', 'Returned', 'Deported') DEFAULT 'In transit',
    FOREIGN KEY (migrant_id) REFERENCES migrants (migrant_id),
    FOREIGN KEY (destination_country_id) REFERENCES countries (country_id),
    FOREIGN KEY (motive_id) REFERENCES motives (motive_id),
    FOREIGN KEY (period_id) REFERENCES periods (period_id),
    CONSTRAINT uc_migrant_event UNIQUE (migrant_id, destination_country_id, period_id)
);

CREATE TABLE migration_risk (
    id INT PRIMARY KEY AUTO_INCREMENT,
    migration_id INT NOT NULL,
    risk_id INT NOT NULL,
    FOREIGN KEY (migration_id) REFERENCES migrations (migration_id),
    FOREIGN KEY (risk_id) REFERENCES risks (risk_id)
);

CREATE TABLE migration_impact (
    id INT PRIMARY KEY AUTO_INCREMENT,
    migration_id INT NOT NULL,
    impact_id INT NOT NULL,
    FOREIGN KEY (migration_id) REFERENCES migrations (migration_id),
    FOREIGN KEY (impact_id) REFERENCES impacts (impact_id)
);

CREATE TABLE global_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    year YEAR NOT NULL,
    country_id INT NOT NULL,
    total_migrants INT DEFAULT 0,
    world_percentage DECIMAL(5,2),
    FOREIGN KEY (country_id) REFERENCES countries (country_id)
);

CREATE TABLE audit (
    audit_id INT PRIMARY KEY AUTO_INCREMENT,
    affected_table VARCHAR(100),
    action_type ENUM('Insert', 'Update', 'Delete'),
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    db_user VARCHAR(100)
);

-- TRIGGERS
CREATE TRIGGER tr_regions_insert AFTER INSERT ON regions FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('regions', 'Insert', USER());
CREATE TRIGGER tr_regions_update AFTER UPDATE ON regions FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('regions', 'Update', USER());
CREATE TRIGGER tr_regions_delete AFTER DELETE ON regions FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('regions', 'Delete', USER());
CREATE TRIGGER tr_countries_insert AFTER INSERT ON countries FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('countries', 'Insert', USER());
CREATE TRIGGER tr_countries_update AFTER UPDATE ON countries FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('countries', 'Update', USER());
CREATE TRIGGER tr_countries_delete AFTER DELETE ON countries FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('countries', 'Delete', USER());
CREATE TRIGGER tr_motive_categories_insert AFTER INSERT ON motive_categories FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('motive_categories', 'Insert', USER());
CREATE TRIGGER tr_motive_categories_update AFTER UPDATE ON motive_categories FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('motive_categories', 'Update', USER());
CREATE TRIGGER tr_motive_categories_delete AFTER DELETE ON motive_categories FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('motive_categories', 'Delete', USER());
CREATE TRIGGER tr_motives_insert AFTER INSERT ON motives FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('motives', 'Insert', USER());
CREATE TRIGGER tr_motives_update AFTER UPDATE ON motives FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('motives', 'Update', USER());
CREATE TRIGGER tr_motives_delete AFTER DELETE ON motives FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('motives', 'Delete', USER());
CREATE TRIGGER tr_migrants_insert AFTER INSERT ON migrants FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migrants', 'Insert', USER());
CREATE TRIGGER tr_migrants_update AFTER UPDATE ON migrants FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migrants', 'Update', USER());
CREATE TRIGGER tr_migrants_delete AFTER DELETE ON migrants FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migrants', 'Delete', USER());
CREATE TRIGGER tr_migrations_insert AFTER INSERT ON migrations FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migrations', 'Insert', USER());
CREATE TRIGGER tr_migrations_update AFTER UPDATE ON migrations FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migrations', 'Update', USER());
CREATE TRIGGER tr_migrations_delete AFTER DELETE ON migrations FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migrations', 'Delete', USER());
CREATE TRIGGER tr_risks_insert AFTER INSERT ON risks FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('risks', 'Insert', USER());
CREATE TRIGGER tr_risks_update AFTER UPDATE ON risks FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('risks', 'Update', USER());
CREATE TRIGGER tr_risks_delete AFTER DELETE ON risks FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('risks', 'Delete', USER());
CREATE TRIGGER tr_impacts_insert AFTER INSERT ON impacts FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('impacts', 'Insert', USER());
CREATE TRIGGER tr_impacts_update AFTER UPDATE ON impacts FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('impacts', 'Update', USER());
CREATE TRIGGER tr_impacts_delete AFTER DELETE ON impacts FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('impacts', 'Delete', USER());

-- TRIGGERS NUEVOS
CREATE TRIGGER tr_periods_insert AFTER INSERT ON periods FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('periods', 'Insert', USER());
CREATE TRIGGER tr_periods_update AFTER UPDATE ON periods FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('periods', 'Update', USER());
CREATE TRIGGER tr_periods_delete AFTER DELETE ON periods FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('periods', 'Delete', USER());
CREATE TRIGGER tr_socioeconomic_levels_insert AFTER INSERT ON socioeconomic_levels FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('socioeconomic_levels', 'Insert', USER());
CREATE TRIGGER tr_socioeconomic_levels_update AFTER UPDATE ON socioeconomic_levels FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('socioeconomic_levels', 'Update', USER());
CREATE TRIGGER tr_socioeconomic_levels_delete AFTER DELETE ON socioeconomic_levels FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('socioeconomic_levels', 'Delete', USER());
CREATE TRIGGER tr_global_statistics_insert AFTER INSERT ON global_statistics FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('global_statistics', 'Insert', USER());
CREATE TRIGGER tr_global_statistics_update AFTER UPDATE ON global_statistics FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('global_statistics', 'Update', USER());
CREATE TRIGGER tr_global_statistics_delete AFTER DELETE ON global_statistics FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('global_statistics', 'Delete', USER());
CREATE TRIGGER tr_migration_risk_insert AFTER INSERT ON migration_risk FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migration_risk', 'Insert', USER());
CREATE TRIGGER tr_migration_risk_update AFTER UPDATE ON migration_risk FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migration_risk', 'Update', USER());
CREATE TRIGGER tr_migration_risk_delete AFTER DELETE ON migration_risk FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migration_risk', 'Delete', USER());
CREATE TRIGGER tr_migration_impact_insert AFTER INSERT ON migration_impact FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migration_impact', 'Insert', USER());
CREATE TRIGGER tr_migration_impact_update AFTER UPDATE ON migration_impact FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migration_impact', 'Update', USER());
CREATE TRIGGER tr_migration_impact_delete AFTER DELETE ON migration_impact FOR EACH ROW
INSERT INTO audit (affected_table, action_type, db_user) VALUES ('migration_impact', 'Delete', USER());

DELIMITER //

-- CRUD REGIONS
CREATE PROCEDURE sp_create_region(IN p_name VARCHAR(100))
BEGIN INSERT INTO regions (name) VALUES (p_name); END //
CREATE PROCEDURE sp_read_region(IN p_id INT)
BEGIN SELECT * FROM regions WHERE region_id = p_id; END //
CREATE PROCEDURE sp_update_region(IN p_id INT, IN p_name VARCHAR(100))
BEGIN UPDATE regions SET name = p_name WHERE region_id = p_id; END //
CREATE PROCEDURE sp_delete_region(IN p_id INT)
BEGIN DELETE FROM regions WHERE region_id = p_id; END //

-- CRUD COUNTRIES
CREATE PROCEDURE sp_create_country(IN p_name VARCHAR(150), IN p_iso VARCHAR(10), IN p_region INT)
BEGIN INSERT INTO countries (name, iso_code, region_id) VALUES (p_name, p_iso, p_region); END //
CREATE PROCEDURE sp_read_country(IN p_id INT)
BEGIN SELECT * FROM countries WHERE country_id = p_id; END //
CREATE PROCEDURE sp_update_country(IN p_id INT, IN p_name VARCHAR(150))
BEGIN UPDATE countries SET name = p_name WHERE country_id = p_id; END //
CREATE PROCEDURE sp_delete_country(IN p_id INT)
BEGIN DELETE FROM countries WHERE country_id = p_id; END //

-- CRUD MOTIVE_CATEGORIES
CREATE PROCEDURE sp_create_motive_category(IN p_name VARCHAR(100))
BEGIN INSERT INTO motive_categories (name) VALUES (p_name); END //
CREATE PROCEDURE sp_read_motive_category(IN p_id INT)
BEGIN SELECT * FROM motive_categories WHERE category_id = p_id; END //
CREATE PROCEDURE sp_update_motive_category(IN p_id INT, IN p_name VARCHAR(100))
BEGIN UPDATE motive_categories SET name = p_name WHERE category_id = p_id; END //
CREATE PROCEDURE sp_delete_motive_category(IN p_id INT)
BEGIN DELETE FROM motive_categories WHERE category_id = p_id; END //

-- CRUD MOTIVES
CREATE PROCEDURE sp_create_motive(IN p_name VARCHAR(150), IN p_cat INT)
BEGIN INSERT INTO motives (name, category_id) VALUES (p_name, p_cat); END //
CREATE PROCEDURE sp_read_motive(IN p_id INT)
BEGIN SELECT * FROM motives WHERE motive_id = p_id; END //
CREATE PROCEDURE sp_update_motive(IN p_id INT, IN p_name VARCHAR(150))
BEGIN UPDATE motives SET name = p_name WHERE motive_id = p_id; END //
CREATE PROCEDURE sp_delete_motive(IN p_id INT)
BEGIN DELETE FROM motives WHERE motive_id = p_id; END //

-- CRUD MIGRANTS
CREATE PROCEDURE sp_create_migrant(IN p_age INT, IN p_sex VARCHAR(20), IN p_country INT, IN p_level INT)
BEGIN INSERT INTO migrants (age, sex, origin_country_id, socioeconomic_level_id) VALUES (p_age, p_sex, p_country, p_level); END //
CREATE PROCEDURE sp_read_migrant(IN p_id INT)
BEGIN SELECT * FROM migrants WHERE migrant_id = p_id; END //
CREATE PROCEDURE sp_update_migrant(IN p_id INT, IN p_age INT, IN p_level INT)
BEGIN UPDATE migrants SET age = p_age, socioeconomic_level_id = p_level WHERE migrant_id = p_id; END //
CREATE PROCEDURE sp_delete_migrant(IN p_id INT)
BEGIN DELETE FROM migrants WHERE migrant_id = p_id; END //

-- CRUD MIGRATIONS
CREATE PROCEDURE sp_create_migration(IN p_migrant INT, IN p_destination INT, IN p_motive INT, IN p_period INT)
BEGIN INSERT INTO migrations (migrant_id, destination_country_id, motive_id, period_id) VALUES (p_migrant, p_destination, p_motive, p_period); END //
CREATE PROCEDURE sp_read_migration(IN p_id INT)
BEGIN SELECT * FROM migrations WHERE migration_id = p_id; END //
CREATE PROCEDURE sp_update_migration(IN p_id INT, IN p_status VARCHAR(20))
BEGIN UPDATE migrations SET status_ = p_status WHERE migration_id = p_id; END //
CREATE PROCEDURE sp_delete_migration(IN p_id INT)
BEGIN DELETE FROM migrations WHERE migration_id = p_id; END //

-- CRUD RISKS
CREATE PROCEDURE sp_create_risk(IN p_desc VARCHAR(250), IN p_type VARCHAR(20))
BEGIN INSERT INTO risks (description, type) VALUES (p_desc, p_type); END //
CREATE PROCEDURE sp_read_risk(IN p_id INT)
BEGIN SELECT * FROM risks WHERE risk_id = p_id; END //
CREATE PROCEDURE sp_update_risk(IN p_id INT, IN p_desc VARCHAR(250))
BEGIN UPDATE risks SET description = p_desc WHERE risk_id = p_id; END //
CREATE PROCEDURE sp_delete_risk(IN p_id INT)
BEGIN DELETE FROM risks WHERE risk_id = p_id; END //

-- CRUD IMPACTS
CREATE PROCEDURE sp_create_impact(IN p_type VARCHAR(20), IN p_desc VARCHAR(250))
BEGIN INSERT INTO impacts (type, description) VALUES (p_type, p_desc); END //
CREATE PROCEDURE sp_read_impact(IN p_id INT)
BEGIN SELECT * FROM impacts WHERE impact_id = p_id; END //
CREATE PROCEDURE sp_update_impact(IN p_id INT, IN p_desc VARCHAR(250))
BEGIN UPDATE impacts SET description = p_desc WHERE impact_id = p_id; END //
CREATE PROCEDURE sp_delete_impact(IN p_id INT)
BEGIN DELETE FROM impacts WHERE impact_id = p_id; END //

-- CRUD GLOBAL_STATISTICS
CREATE PROCEDURE sp_create_global_stat(IN p_year YEAR, IN p_country INT, IN p_total INT, IN p_pct DECIMAL(5,2))
BEGIN INSERT INTO global_statistics (year, country_id, total_migrants, world_percentage) VALUES (p_year, p_country, p_total, p_pct); END //
CREATE PROCEDURE sp_read_global_stat(IN p_id INT)
BEGIN SELECT * FROM global_statistics WHERE id = p_id; END //
CREATE PROCEDURE sp_read_all_global_stats()
BEGIN SELECT * FROM global_statistics ORDER BY year DESC; END //

-- SOCIOECONOMIC_LEVELS
CREATE PROCEDURE sp_create_level(IN p_desc VARCHAR(100))
BEGIN INSERT IGNORE INTO socioeconomic_levels (description) VALUES (p_desc); END //
CREATE PROCEDURE sp_read_all_levels()
BEGIN SELECT level_id, description FROM socioeconomic_levels; END //

-- PERIODS
CREATE PROCEDURE sp_create_period(IN p_year YEAR)
BEGIN INSERT IGNORE INTO periods (year) VALUES (p_year); END //
CREATE PROCEDURE sp_read_all_periods()
BEGIN SELECT period_id, year FROM periods; END //
CREATE PROCEDURE sp_read_period_by_year(IN p_year YEAR)
BEGIN SELECT period_id FROM periods WHERE year = p_year LIMIT 1; END //

-- MIGRATION_RISK / MIGRATION_IMPACT
CREATE PROCEDURE sp_create_migration_risk(IN p_migration INT, IN p_risk INT)
BEGIN INSERT IGNORE INTO migration_risk (migration_id, risk_id) VALUES (p_migration, p_risk); END //
CREATE PROCEDURE sp_create_migration_impact(IN p_migration INT, IN p_impact INT)
BEGIN INSERT IGNORE INTO migration_impact (migration_id, impact_id) VALUES (p_migration, p_impact); END //

-- LECTURA
CREATE PROCEDURE sp_read_all_regions()
BEGIN SELECT * FROM regions; END //
CREATE PROCEDURE sp_read_all_countries()
BEGIN SELECT * FROM countries; END //
CREATE PROCEDURE sp_read_all_motive_categories()
BEGIN SELECT * FROM motive_categories; END //
CREATE PROCEDURE sp_read_all_motives()
BEGIN SELECT * FROM motives; END //
CREATE PROCEDURE sp_read_all_risks()
BEGIN SELECT * FROM risks; END //
CREATE PROCEDURE sp_read_all_impacts()
BEGIN SELECT * FROM impacts; END //
CREATE PROCEDURE sp_read_all_migrations()
BEGIN SELECT migration_id FROM migrations LIMIT 5000; END //
CREATE PROCEDURE sp_read_all_migrants()
BEGIN SELECT * FROM migrants; END //
CREATE PROCEDURE sp_read_all_migration_risk()
BEGIN SELECT * FROM migration_risk; END //
CREATE PROCEDURE sp_read_all_migration_impact()
BEGIN SELECT * FROM migration_impact; END //
CREATE PROCEDURE sp_read_all_audit()
BEGIN SELECT * FROM audit; END //

-- MIGRANT FULL + ÚLTIMO ID
CREATE PROCEDURE sp_create_migrant_full(IN p_age INT, IN p_sex VARCHAR(20), IN p_country INT, IN p_level INT)
BEGIN
    INSERT INTO migrants (age, sex, origin_country_id, socioeconomic_level_id)
    VALUES (p_age, p_sex, p_country, p_level);
    SET @last_migrant_id = LAST_INSERT_ID();
END //

CREATE PROCEDURE sp_read_migrant_last(IN p_migrant_id INT)
BEGIN
    SELECT migration_id FROM migrations
    WHERE migrant_id = p_migrant_id
    ORDER BY migration_id DESC LIMIT 1;
END //

DELIMITER ;

-- VIEWS
CREATE VIEW vw_top_motives AS
SELECT cm.name AS category, m.name AS motive, COUNT(mg.migration_id) AS total_migrations
FROM migrations mg
JOIN motives m ON mg.motive_id = m.motive_id
JOIN motive_categories cm ON m.category_id = cm.category_id
JOIN countries cd ON mg.destination_country_id = cd.country_id
WHERE cd.name = 'Mexico'
GROUP BY cm.name, m.name
ORDER BY total_migrations DESC;

CREATE VIEW vw_origin_countries AS
SELECT c.name AS origin_country, r.name AS region, COUNT(mg.migration_id) AS total_migrants
FROM migrations mg
JOIN migrants mi ON mg.migrant_id = mi.migrant_id
JOIN countries c ON mi.origin_country_id = c.country_id
JOIN regions r ON c.region_id = r.region_id
JOIN countries cd ON mg.destination_country_id = cd.country_id
WHERE cd.name = 'Mexico'
GROUP BY c.name, r.name
ORDER BY total_migrants DESC;

CREATE VIEW vw_international_comparison AS
SELECT c.name AS destination_country, gs.year, gs.total_migrants, gs.world_percentage
FROM global_statistics gs
JOIN countries c ON gs.country_id = c.country_id
ORDER BY gs.year DESC, gs.total_migrants DESC;

CREATE VIEW vw_migrant_risks AS
SELECT r.type AS risk_type, r.description AS risk, COUNT(mr.id) AS cases
FROM migration_risk mr
JOIN risks r ON mr.risk_id = r.risk_id
JOIN migrations mg ON mr.migration_id = mg.migration_id
JOIN countries cd ON mg.destination_country_id = cd.country_id
WHERE cd.name = 'Mexico'
GROUP BY r.type, r.description
ORDER BY cases DESC;

CREATE VIEW vw_impacts_on_mexico AS
SELECT i.type AS impact_type, i.description AS impact, COUNT(mi.id) AS frequency
FROM migration_impact mi
JOIN impacts i ON mi.impact_id = i.impact_id
JOIN migrations mg ON mi.migration_id = mg.migration_id
JOIN countries cd ON mg.destination_country_id = cd.country_id
WHERE cd.name = 'Mexico'
GROUP BY i.type, i.description
ORDER BY impact_type, frequency DESC;

CREATE VIEW vw_demographic_profile AS
SELECT mi.sex, sl.description AS socioeconomic_level,
ROUND(AVG(mi.age), 1) AS average_age, COUNT(mg.migration_id) AS total
FROM migrations mg
JOIN migrants mi ON mg.migrant_id = mi.migrant_id
JOIN socioeconomic_levels sl ON mi.socioeconomic_level_id = sl.level_id
JOIN countries cd ON mg.destination_country_id = cd.country_id
WHERE cd.name = 'Mexico'
GROUP BY mi.sex, sl.description;

-- VISTAS NUEVAS
CREATE VIEW vw_audit_summary AS
SELECT affected_table, action_type, COUNT(*) AS total_acciones, MAX(action_timestamp) AS ultima_vez
FROM audit
GROUP BY affected_table, action_type
ORDER BY affected_table, action_type;

CREATE VIEW vw_yearly_trends AS
SELECT p.year, cd.name AS destination_country, COUNT(mg.migration_id) AS total_migrations
FROM migrations mg
JOIN periods p ON mg.period_id = p.period_id
JOIN countries cd ON mg.destination_country_id = cd.country_id
GROUP BY p.year, cd.name
ORDER BY p.year DESC, total_migrations DESC;

CREATE VIEW vw_status_distribution AS
SELECT cd.name AS destination_country, p.year, mg.status_,
    COUNT(*) AS total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY cd.name, p.year), 2) AS percentage
FROM migrations mg
JOIN countries cd ON mg.destination_country_id = cd.country_id
JOIN periods p ON mg.period_id = p.period_id
GROUP BY cd.name, p.year, mg.status_
ORDER BY cd.name, p.year, mg.status_;