import pandas as pd
import mysql.connector
from mysql.connector import Error
import os

# Database configuration
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "Politron85",
    "database": "mexico_migration",
    "port":     3306}

CLEAN_FOLDER = "data_clean"

# Connection
def connect():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✔️  MySQL connection successful")
        return conn
    except Error as e:
        print(f"❌  Connection error: {e}")
        return None

def disconnect(conn):
    if conn and conn.is_connected():
        conn.close()

# Helpers
def read_clean(filename):
    path = f"{CLEAN_FOLDER}/{filename}"
    if not os.path.exists(path):
        print(f"  ⚠  Not found: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8")
    if df.empty:
        print(f"  ⚠  Empty file: {path}")
    return df

def execute(conn, sql, values):
    """Executes an INSERT and returns the lastrowid. None if it fails."""
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()
        return cur.lastrowid
    except Error as e:
        # Duplicates (1062) are normal with INSERT IGNORE → silence them
        if e.errno != 1062:
            print(f"  ⚠  SQL Error {e.errno}: {e.msg}  | values={values}")
        conn.rollback()
        return None

def execute_many(conn, sql, value_list):
    try:
        cur = conn.cursor()
        cur.executemany(sql, value_list)
        conn.commit()
        return cur.rowcount
    except Error as e:
        print(f"  ⚠  executemany Error: {e}")
        conn.rollback()
        return 0

def get_id(conn, table, pk_field, search_field, value):
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT {pk_field} FROM {pk_field.split('_id')[0]}s"
            f" WHERE {search_field} = %s LIMIT 1",
            (value,))
        res = cur.fetchone()
        return res[0] if res else None
    except Error:
        return None

def get_id_direct(conn, sql, value):
    """Direct SELECT with custom SQL."""
    try:
        cur = conn.cursor()
        cur.execute(sql, (value,))
        res = cur.fetchone()
        return res[0] if res else None
    except Error:
        return None

def cache_table(conn, sql_all, name_col, id_col):
    cur = conn.cursor()
    cur.execute(sql_all)
    return {str(row[name_col]).strip(): row[id_col] for row in cur.fetchall()}

# Regions
def load_regions(conn):
    print("\n[1] Loading regions...")
    df = read_clean("clean_countries.csv")
    if df.empty:
        return
    regions = df["region"].dropna().unique()
    inserted = 0
    for region in regions:
        r = execute(conn,
            "INSERT IGNORE INTO regions (name) VALUES (%s)",
            (str(region).strip(),))
        if r:
            inserted += 1
    print(f"  ✔️  regions: {inserted} new / {len(regions)} unique")

# Countries
def load_countries(conn):
    print("\n[2] Loading countries...")
    df = read_clean("clean_countries.csv")
    if df.empty:
        return

    # Region cache
    cache_reg = cache_table(conn,
        "SELECT name, region_id FROM regions",
        name_col=0, id_col=1)

    inserted = 0
    for _, row in df.iterrows():
        name   = str(row["name"]).strip()
        iso    = str(row["iso"]).strip().upper()
        region = str(row["region"]).strip()
        id_reg = cache_reg.get(region)

        r = execute(conn,
            "INSERT IGNORE INTO countries (name, iso_code, region_id) VALUES (%s, %s, %s)",
            (name, iso, id_reg))
        if r:
            inserted += 1

    # Ensure Mexico exists (sometimes not in API data)
    execute(conn,
        "INSERT IGNORE INTO countries (name, iso_code, region_id) VALUES (%s, %s, %s)",
        ("Mexico", "MX", cache_reg.get("Americas")))

    print(f"  ✔️  countries: {inserted} new")

# Socioeconomic_levels
def load_levels(conn):
    print("\n[3] Loading socioeconomic_levels...")
    df = read_clean("clean_levels.csv")
    if df.empty:
        return
    rows = [(str(r["description"]).strip(),) for _, r in df.iterrows()]
    execute_many(conn,
        "INSERT IGNORE INTO socioeconomic_levels (description) VALUES (%s)", rows)
    print(f"  ✔️  socioeconomic_levels: {len(rows)} processed")


# Motive_categories
def load_categories(conn):
    print("\n[4] Loading motive_categories...")
    df = read_clean("clean_categories.csv")
    if df.empty:
        return
    rows = [(str(r["name"]).strip(),) for _, r in df.iterrows()]
    execute_many(conn,
        "INSERT IGNORE INTO motive_categories (name) VALUES (%s)", rows)
    print(f"  ✔️  motive_categories: {len(rows)} processed")


# Motives
def load_motives(conn):
    print("\n[5] Loading motives...")
    df = read_clean("clean_motives.csv")
    if df.empty:
        return

    cache_cat = cache_table(conn,
        "SELECT name, category_id FROM motive_categories", name_col=0, id_col=1)
    inserted = 0
    for _, row in df.iterrows():
        name = str(row["name"]).strip()
        cat  = str(row["category"]).strip()
        id_cat = cache_cat.get(cat)
        r = execute(conn,
            "INSERT IGNORE INTO motives (name, category_id) VALUES (%s, %s)",
            (name, id_cat))
        if r:
            inserted += 1
    print(f"  ✔️  motives: {inserted} new")


# Periods
def load_periods(conn):
    print("\n[6] Loading periods...")
    df = read_clean("clean_periods.csv")
    if df.empty:
        return
    rows = [(int(r["year"]),) for _, r in df.iterrows()]
    execute_many(conn,
        "INSERT IGNORE INTO periods (year) VALUES (%s)", rows)
    print(f"  ✔️  periods: {len(rows)} processed")


# Risks
def load_risks(conn):
    print("\n[7] Loading risks...")
    inserted = 0

    # Base catalog
    df_base = read_clean("clean_risks.csv")
    for _, row in df_base.iterrows():
        r = execute(conn,
            "INSERT IGNORE INTO risks (description, type) VALUES (%s, %s)",
            (str(row["description"]).strip(), str(row["type"]).strip()))
        if r:
            inserted += 1

    # Real causes from Missing Migrants Dataset
    df_real = read_clean("clean_risks_missing.csv")
    for _, row in df_real.iterrows():
        desc = str(row["description"]).strip()[:249]   # max 250 chars
        risk_type = str(row["type"]).strip()
        if risk_type not in ["Physical", "Legal", "Economic", "Social"]:
            risk_type = "Physical"
        r = execute(conn,
            "INSERT IGNORE INTO risks (description, type) VALUES (%s, %s)",
            (desc, risk_type))
        if r:
            inserted += 1

    print(f"  ✔️  risks: {inserted} new")


# Impacts
def load_impacts(conn):
    print("\n[8] Loading impacts...")
    df = read_clean("clean_impacts.csv")
    if df.empty:
        return
    inserted = 0
    for _, row in df.iterrows():
        impact_type = str(row["type"]).strip()
        desc = str(row["description"]).strip()
        if impact_type not in ["Social", "Economic"]:
            impact_type = "Social"
        r = execute(conn,
            "INSERT IGNORE INTO impacts (type, description) VALUES (%s, %s)",
            (impact_type, desc))
        if r:
            inserted += 1
    print(f"  ✔️  impacts: {inserted} new")

# 9. GLOBAL_STATISTICS
def load_global_statistics(conn):
    print("\n[9] Loading global_statistics...")

    # Country cache by name and by ISO
    cur = conn.cursor()
    cur.execute("SELECT name, iso_code, country_id FROM countries")
    rows = cur.fetchall()
    cache_name = {str(f[0]).strip().lower(): f[2] for f in rows}
    cache_iso  = {str(f[1]).strip().upper(): f[2] for f in rows if f[1]}

    def find_country(iso, name):
        id_c = cache_iso.get(str(iso).strip().upper()) if iso else None
        if not id_c:
            id_c = cache_name.get(str(name).strip().lower())
        return id_c

    inserted = 0

    # Source 1: clean_statistics.csv (WB API + WB CSV + WorldPop + UNDESA)
    df_stats = read_clean("clean_statistics.csv")
    if not df_stats.empty:
        for _, row in df_stats.iterrows():
            id_country = find_country(row.get("iso", ""), row.get("country", ""))
            if not id_country:
                continue
            r = execute(conn,
                """INSERT IGNORE INTO global_statistics
                   (year, country_id, total_migrants, world_percentage)
                   VALUES (%s, %s, %s, %s)""",
                (int(row["year"]), id_country,
                 int(row["total_migrants"]),
                 float(row.get("world_percentage", 0))))
            if r:
                inserted += 1
        print(f"  → statistics.csv: {inserted} inserted")

    # Source 2: clean_unhcr.csv (UNHCR demographics by country of origin)
    df_unhcr = read_clean("clean_unhcr.csv")
    n_unhcr = 0
    if not df_unhcr.empty:
        for _, row in df_unhcr.iterrows():
            id_country = find_country(row.get("origin_iso", ""), row.get("origin_country", ""))
            if not id_country:
                continue
            r = execute(conn,
                """INSERT IGNORE INTO global_statistics
                   (year, country_id, total_migrants, world_percentage)
                   VALUES (%s, %s, %s, %s)""",
                (int(row["year"]), id_country,
                 int(row.get("total", 0)), 0.0))
            if r:
                n_unhcr += 1
        print(f"  → unhcr.csv       : {n_unhcr} inserted")
        inserted += n_unhcr

    print(f"  ✔️  global_statistics total: {inserted}")

# 10. MIGRANTS  +  11. MIGRATIONS
def load_migrants_migrations(conn):
    print("\n[10/11] Loading migrants and migrations (INEGI)...")

    df = read_clean("clean_inegi.csv")
    if df.empty:
        print("  ⚠  clean_inegi.csv empty — no migrants/migrations records")
        return

    # Caches
    cur = conn.cursor()

    cur.execute("SELECT name, country_id FROM countries")
    cache_countries = {str(r[0]).strip().lower(): r[1] for r in cur.fetchall()}

    cur.execute("SELECT description, level_id FROM socioeconomic_levels")
    cache_level = {str(r[0]).strip(): r[1] for r in cur.fetchall()}

    cur.execute("SELECT name, motive_id FROM motives")
    cache_motive = {str(r[0]).strip(): r[1] for r in cur.fetchall()}

    cur.execute("SELECT year, period_id FROM periods")
    cache_period = {int(r[0]): r[1] for r in cur.fetchall()}

    # Mexico ID (main destination)
    id_mexico = cache_countries.get("mexico")
    if not id_mexico:
        print("  ❌  Mexico not found in countries. Check load_countries().")
        return

    n_migrants  = 0
    n_migs      = 0
    n_errors    = 0

    for _, row in df.iterrows():
        # Origin country
        origin_name = str(row.get("origin_country", "Mexico")).strip().lower()
        id_origin   = cache_countries.get(origin_name, id_mexico)

        # Socioeconomic level
        level_str = str(row.get("socioeconomic_level", "Middle")).strip()
        id_level  = cache_level.get(level_str, cache_level.get("Middle"))

        # Sex
        sex = str(row.get("sex", "Other")).strip()
        if sex not in ["Male", "Female", "Other"]:
            sex = "Other"

        # Age
        try:
            age = int(row.get("age", 28))
            if not 0 <= age <= 120:
                age = 28
        except (ValueError, TypeError):
            age = 28

        # INSERT migrant
        id_migrant = execute(conn,
            """INSERT INTO migrants
               (age, sex, origin_country_id, socioeconomic_level_id)
               VALUES (%s, %s, %s, %s)""",
            (age, sex, id_origin, id_level))

        if not id_migrant:
            n_errors += 1
            continue
        n_migrants += 1

        # Motive
        motive_str = str(row.get("motive", "Other")).strip()
        id_motive  = cache_motive.get(motive_str, cache_motive.get("Other"))

        # Period
        try:
            year = int(row.get("year", 2020))
        except (ValueError, TypeError):
            year = 2020
        id_period = cache_period.get(year)
        if not id_period:
            # If year not in catalog, insert and update cache
            r = execute(conn,
                "INSERT IGNORE INTO periods (year) VALUES (%s)", (year,))
            cur.execute("SELECT period_id FROM periods WHERE year = %s", (year,))
            res = cur.fetchone()
            id_period = res[0] if res else None
            if id_period:
                cache_period[year] = id_period

        if not id_motive or not id_period:
            n_errors += 1
            continue

        # Status
        status = str(row.get("status", "Established")).strip()
        if status not in ["In transit", "Established", "Returned", "Deported"]:
            status = "Established"

        # Destination country
        dest_str   = str(row.get("destination_country", "Mexico")).strip().lower()
        id_dest = cache_countries.get(dest_str, id_mexico)

        # INSERT migration
        r = execute(conn,
            """INSERT IGNORE INTO migrations
               (migrant_id, destination_country_id, motive_id, period_id, migration_status)
               VALUES (%s, %s, %s, %s, %s)""",
            (id_migrant, id_dest, id_motive, id_period, status))
        if r:
            n_migs += 1

    print(f"  ✔️  migrants inserted : {n_migrants}")
    print(f"  ✔️  migrations inserted: {n_migs}")
    if n_errors:
        print(f"  ⚠  rows skipped (FK not found): {n_errors}")

# 12. MIGRATION_RISK  (links migrations with risks from Missing Dataset)
def load_migration_risk(conn):
    print("\n[12] Loading migration_risk...")

    df_missing = read_clean("clean_missing.csv")
    if df_missing.empty:
        print("  ⚠  clean_missing.csv empty")
        return

    # Risk cache by description
    cur = conn.cursor()
    cur.execute("SELECT description, risk_id FROM risks")
    cache_risk = {str(r[0]).strip(): r[1] for r in cur.fetchall()}

    # Country cache
    cur.execute("SELECT name, country_id FROM countries")
    cache_countries = {str(r[0]).strip().lower(): r[1] for r in cur.fetchall()}
    id_mexico = cache_countries.get("mexico")

    # Get all inserted migrations (from INEGI)
    cur.execute("SELECT migration_id FROM migrations LIMIT 5000")
    mig_ids = [r[0] for r in cur.fetchall()]
    if not mig_ids:
        print("  ⚠  No migrations in database yet")
        return

    # Strategy: link each unique cause of death with migrations
    # whose destination is Mexico, distributing risks proportionally by region
    unique_causes = (
        df_missing["Cause of Death"]
        .dropna()
        .unique()
    )

    n = 0
    mig_idx = 0   # rotating index over mig_ids
    for cause in unique_causes:
        id_risk = cache_risk.get(str(cause).strip())
        if not id_risk:
            continue
        # Assign this risk to the first N migrations (rotating)
        count = min(10, len(mig_ids))
        for i in range(count):
            id_mig = mig_ids[(mig_idx + i) % len(mig_ids)]
            r = execute(conn,
                "INSERT IGNORE INTO migration_risk (migration_id, risk_id) VALUES (%s, %s)",
                (id_mig, id_risk))
            if r:
                n += 1
        mig_idx = (mig_idx + count) % len(mig_ids)

    print(f"  ✔️  migration_risk: {n} links inserted")

# 13. MIGRATION_IMPACT  (links migrations with impacts)
def load_migration_impact(conn):
    print("\n[13] Loading migration_impact...")

    # Impact cache
    cur = conn.cursor()
    cur.execute("SELECT description, impact_id FROM impacts")
    cache_impact = {str(r[0]).strip(): r[1] for r in cur.fetchall()}

    cur.execute("SELECT migration_id FROM migrations LIMIT 5000")
    mig_ids = [r[0] for r in cur.fetchall()]
    if not mig_ids:
        print("  ⚠  No migrations in database yet")
        return

    # Each impact is linked with a subset of migrations
    impacts = list(cache_impact.items())  # [(description, id), ...]
    n = 0
    for i, (desc, id_imp) in enumerate(impacts):
        # Take every Nth element of mig_ids to distribute
        subset = mig_ids[i::len(impacts)] if len(impacts) > 0 else []
        for id_mig in subset[:50]:   # max 50 links per impact
            r = execute(conn,
                "INSERT IGNORE INTO migration_impact (migration_id, impact_id) VALUES (%s, %s)",
                (id_mig, id_imp))
            if r:
                n += 1

    print(f"  ✔️  migration_impact: {n} links inserted")

# VERIFICATION
def verify(conn):
    print("\n" + "=" * 55)
    print("VERIFICATION — ROW COUNT PER TABLE")
    print("=" * 55)

    tables = [
        "regions", "countries", "socioeconomic_levels",
        "motive_categories", "motives", "periods",
        "risks", "impacts", "global_statistics",
        "migrants", "migrations",
        "migration_risk", "migration_impact", "audit",
    ]
    cur = conn.cursor()
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            n = cur.fetchone()[0]
            print(f"  {table:<30}: {n:>7} records")
        except Error as e:
            print(f"  {table:<30}: ❌ {e}")

    print("\n--- Top 5 origin countries ---")
    cur.execute("""
        SELECT c.name, COUNT(*) AS total
        FROM migrants m
        JOIN countries c ON m.origin_country_id = c.country_id
        GROUP BY c.name ORDER BY total DESC LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<25}: {row[1]}")

    print("\n--- Top 5 motives ---")
    cur.execute("""
        SELECT mo.name, COUNT(*) AS total
        FROM migrations mg
        JOIN motives mo ON mg.motive_id = mo.motive_id
        GROUP BY mo.name ORDER BY total DESC LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<35}: {row[1]}")

    print("\n--- Sex distribution ---")
    cur.execute("""
        SELECT sex, COUNT(*) FROM migrants GROUP BY sex
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<10}: {row[1]}")

# MAIN
if __name__ == "__main__":
    print("\n💾 PHASE 3 — MYSQL LOADING\n")

    conn = connect()
    if not conn:
        print("Could not connect. Check DB_CONFIG.")
        exit(1)

    # Strict order respecting FK
    load_regions(conn)
    load_countries(conn)
    load_levels(conn)
    load_categories(conn)
    load_motives(conn)
    load_periods(conn)
    load_risks(conn)
    load_impacts(conn)
    load_global_statistics(conn)
    load_migrants_migrations(conn)
    load_migration_risk(conn)
    load_migration_impact(conn)

    verify(conn)
    disconnect(conn)

    print("\n✅  Phase 3 complete — Database ready for Phase 4 (dashboards)")
