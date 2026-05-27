-- ============================================================================
-- patches.sql - Improvements to the mexico_migration schema views
-- ============================================================================
-- Apply AFTER mexico_migration_final.sql and after loading the data
-- with the pipeline (run_all.py).
--
-- These views replace the original ones so the dashboard has richer data
-- and so the charts (choropleth, sunburst, etc.) receive the columns they need
-- (ISO codes, etc.).
--
-- Compatible with the final schema that includes the global_statistics.source column.
--
-- How to apply:
--   1. Open this file in MySQL Workbench
--   2. Verify that you are connected and that the active database is mexico_migration
--   3. Run the entire script using the yellow lightning bolt
-- ============================================================================

USE mexico_migration;

-- ----------------------------------------------------------------------------
-- 1. vw_top_motives - REMOVE the destination = 'Mexico' filter
-- The original version only showed reasons for people migrating TO Mexico.
-- Since INEGI includes Mexicans who EMIGRATE, it only returned 3 reasons. This version
-- shows all migration reasons in the database.
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
-- 2. vw_origin_countries - Use global_statistics (UNHCR) + iso_code
--    The original version looked at migrants.origin_country_id, which with INEGI
--    always returns 'Mexico'. This version uses global_statistics filtered by
--    source = 'UNHCR' (which is where the real countries of origin toward Mexico are stored).
--    We add iso_code to be able to create choropleth maps.
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
-- 3. vw_international_comparison - Add iso_code for choropleth maps
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
-- 4. vw_migrant_risks - No destination filter (more available data)
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
-- 5. vw_impacts_on_mexico - No functional changes
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
-- 6. vw_demographic_profile - Remove "average_age" (age is not a field in INEGI)
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
-- VERIFICATION: Count the rows in each view to confirm the fix
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
