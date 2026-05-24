-- ============================================================================
-- patches.sql - Mejoras a las vistas del esquema mexico_migration
-- ============================================================================
-- Aplicar DESPUES de mexico_migration_final.sql y despues de haber cargado
-- los datos con el pipeline (run_all.py).
--
-- Estas vistas reemplazan las originales para que el dashboard tenga datos
-- mas ricos y para que los graficos (choropleth, sunburst, etc) reciban
-- las columnas que necesitan (ISO codes, etc).
--
-- Compatible con el esquema final que tiene la columna global_statistics.source
--
-- Como aplicar:
--   1. Abrir este archivo en MySQL Workbench
--   2. Verificar que estas conectado y la BD activa es mexico_migration
--   3. Ejecutar todo el script con el rayo amarillo
-- ============================================================================

USE mexico_migration;

-- ----------------------------------------------------------------------------
-- 1. vw_top_motives - REMOVER el filtro destino='Mexico'
--    La version original solo mostraba motivos de quienes migran HACIA Mexico.
--    Como INEGI tiene mexicanos que EMIGRAN, solo daba 3 motivos. Esta version
--    muestra todos los motivos de migracion en la base.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_top_motives;

CREATE VIEW vw_top_motives AS
SELECT
    cm.name                       AS category,
    m.name                        AS motive,
    COUNT(mg.migration_id)        AS total_migrations
FROM migrations mg
JOIN motives m              ON mg.motive_id   = m.motive_id
JOIN motive_categories cm   ON m.category_id  = cm.category_id
GROUP BY cm.name, m.name
ORDER BY total_migrations DESC;


-- ----------------------------------------------------------------------------
-- 2. vw_origin_countries - Usar global_statistics (UNHCR) + iso_code
--    La version original miraba migrants.origin_country_id, que con INEGI
--    siempre da 'Mexico'. Esta version usa global_statistics filtrando
--    source='UNHCR' (que es donde estan los paises de origen reales hacia Mexico).
--    Agregamos iso_code para poder hacer mapas choropleth.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_origin_countries;

CREATE VIEW vw_origin_countries AS
SELECT
    c.name                        AS origin_country,
    c.iso_code                    AS iso_code,
    COALESCE(r.name, 'Unknown')   AS region,
    SUM(gs.total_migrants)        AS total_migrants
FROM global_statistics gs
JOIN countries c            ON gs.country_id = c.country_id
LEFT JOIN regions r         ON c.region_id   = r.region_id
WHERE c.name != 'Mexico'
  AND gs.source = 'UNHCR'
GROUP BY c.name, c.iso_code, r.name
ORDER BY total_migrants DESC;


-- ----------------------------------------------------------------------------
-- 3. vw_international_comparison - Agregar iso_code para choropleth
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_international_comparison;

CREATE VIEW vw_international_comparison AS
SELECT
    c.name                       AS destination_country,
    c.iso_code                   AS iso_code,
    gs.year                      AS year,
    gs.total_migrants            AS total_migrants,
    gs.world_percentage          AS world_percentage,
    gs.source                    AS source
FROM global_statistics gs
JOIN countries c    ON gs.country_id = c.country_id
ORDER BY gs.year DESC, gs.total_migrants DESC;


-- ----------------------------------------------------------------------------
-- 4. vw_migrant_risks - Sin filtro de destino (mas datos disponibles)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_migrant_risks;

CREATE VIEW vw_migrant_risks AS
SELECT
    r.type                       AS risk_type,
    r.description                AS risk,
    COUNT(mr.id)                 AS cases
FROM migration_risk mr
JOIN risks r        ON mr.risk_id = r.risk_id
GROUP BY r.type, r.description
ORDER BY cases DESC;


-- ----------------------------------------------------------------------------
-- 5. vw_impacts_on_mexico - Sin cambios funcionales (ya estaba bien)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_impacts_on_mexico;

CREATE VIEW vw_impacts_on_mexico AS
SELECT
    i.type                       AS impact_type,
    i.description                AS impact,
    COUNT(mi.id)                 AS frequency
FROM migration_impact mi
JOIN impacts i      ON mi.impact_id = i.impact_id
GROUP BY i.type, i.description
ORDER BY impact_type, frequency DESC;


-- ----------------------------------------------------------------------------
-- 6. vw_demographic_profile - Quitar average_age (la edad no existe en INEGI)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_demographic_profile;

CREATE VIEW vw_demographic_profile AS
SELECT
    mi.sex                       AS sex,
    sl.description               AS socioeconomic_level,
    COUNT(mg.migration_id)       AS total
FROM migrations mg
JOIN migrants mi                 ON mg.migrant_id              = mi.migrant_id
JOIN socioeconomic_levels sl     ON mi.socioeconomic_level_id  = sl.level_id
GROUP BY mi.sex, sl.description
ORDER BY total DESC;


-- ----------------------------------------------------------------------------
-- VERIFICACION: contar filas en cada vista para confirmar el fix
-- ----------------------------------------------------------------------------
SELECT 'vw_top_motives'                 AS vista, COUNT(*) AS filas FROM vw_top_motives
UNION ALL
SELECT 'vw_origin_countries',           COUNT(*) FROM vw_origin_countries
UNION ALL
SELECT 'vw_international_comparison',   COUNT(*) FROM vw_international_comparison
UNION ALL
SELECT 'vw_migrant_risks',              COUNT(*) FROM vw_migrant_risks
UNION ALL
SELECT 'vw_impacts_on_mexico',          COUNT(*) FROM vw_impacts_on_mexico
UNION ALL
SELECT 'vw_demographic_profile',        COUNT(*) FROM vw_demographic_profile;
