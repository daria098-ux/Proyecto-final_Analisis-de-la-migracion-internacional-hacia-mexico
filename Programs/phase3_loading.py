"""
Phase 3: MySQL Data Loading via Stored Procedures

This script reads the cleaned CSVs from data_clean/ (produced by Phase 2)
and inserts each row into the mexico_migration MySQL database using the
stored procedures defined in mexico_migration_final.sql.

Each table has its own loading function that:
  1. Reads the corresponding clean CSV
  2. Looks up foreign-key values from already-loaded tables (using read SPs)
  3. Calls the appropriate sp_create_* procedure for each row
  4. Prints a count of inserted records

Typical usage:
    Run as part of the pipeline (run_all.py) or standalone:
        python phase3_loading.py
"""

import os
import warnings
import mysql.connector
from mysql.connector import Error
import pandas as pd

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",
    "database": "mexico_migration",
    "port":     3306,
}

# Absolute paths based on the project root directory
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))   # Programs/
PROJECT_ROOT  = os.path.dirname(SCRIPT_DIR)                  # project root
CARPETA_CLEAN = os.path.join(PROJECT_ROOT, "data_clean")     # cleaned CSVs (input)


def conectar():
    """Connect to the mexico_migration MySQL database using DB_CONFIG.
    Returns the connection object or None on failure.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✔️  MySQL connection successful")
        return conn
    except Error as e:
        print(f"❌  Connection error: {e}")
        return None


def desconectar(conn):
    """Close the MySQL connection if it is still open."""
    if conn and conn.is_connected():
        conn.close()


def leer_clean(nombre):
    """Read a cleaned CSV from data_clean/. Returns an empty DataFrame if
    the file is missing or empty.
    """
    ruta = f"{CARPETA_CLEAN}/{nombre}"
    if not os.path.exists(ruta):
        print(f" Not found: {ruta}")
        return pd.DataFrame()
    df = pd.read_csv(ruta, encoding="utf-8")
    if df.empty:
        print(f"Empty file: {ruta}")
    return df


def llamar_sp(conn, sp, params=()):
    """Call a MySQL stored procedure with the given parameters and commit.

    Silently ignores duplicate-key errors (errno 1062). Returns the
    lastrowid on success, True if no lastrowid, or None on error.
    """
    try:
        cu = conn.cursor()
        cu.callproc(sp, params)
        conn.commit()
        lastrow = cu.lastrowid if cu.lastrowid else True
        cu.close()
        return lastrow
    except Error as e:
        if e.errno != 1062:
            print(f" {sp}{params} → {e.errno}: {e.msg}")
        conn.rollback()
        return None


def leer_sp(conn, sp, params=()):
    """Call a MySQL read-type stored procedure and return all rows.

    Used to query reference data (e.g., region IDs, country IDs) that
    is needed as foreign keys when inserting into other tables.
    """
    rows = []
    try:
        cu = conn.cursor()
        cu.callproc(sp, params)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for resultado in cu.stored_results():
                rows = resultado.fetchall()
        cu.close()
    except Error as e:
        print(f"{sp} lectura → {e}")
    return rows


def llamar_sp_migrant(conn, edad, sexo, id_origen, id_nivel):
    """Create a migrant record using sp_create_migrant_full and return the
    new migrant ID. This uses a MySQL session variable (@last_migrant_id)
    set by the stored procedure to retrieve the auto-increment ID.
    """
    try:
        cu = conn.cursor()
        cu.callproc("sp_create_migrant_full", (edad, sexo, id_origen, id_nivel))
        conn.commit()
        cu.close()
        cu2 = conn.cursor()
        cu2.execute("SELECT @last_migrant_id")
        row = cu2.fetchone()
        cu2.close()
        return int(row[0]) if row and row[0] else None
    except Error as e:
        if e.errno != 1062:
            print(f"  ⚠  sp_create_migrant_full → {e.errno}: {e.msg}")
        conn.rollback()
        return None


def cargar_regions(conn):
    """Load unique region names from clean_paises.csv into the regions table."""
    print("\nLoading regions")
    df = leer_clean("clean_paises.csv")
    if df.empty:
        return
    regiones = df["region"].dropna().unique()
    n = 0
    for region in regiones:
        r = llamar_sp(conn, "sp_create_region", (str(region).strip(),))
        if r:
            n += 1
    print(f"  ✔️  regions: {n} new / {len(regiones)} unique")


def cargar_countries(conn):
    """Load countries from clean_paises.csv into the countries table.

    Uses the regions table as a foreign-key lookup. Also adds 'Mexico'
    as a country since it's the destination but may not appear in the
    source data.
    """
    print("\nLoading countries")
    df = leer_clean("clean_paises.csv")
    if df.empty:
        return
    rows = leer_sp(conn, "sp_read_all_regions")
    cache_reg = {str(f[1]).strip(): f[0] for f in rows}
    n = 0
    for _, fila in df.iterrows():
        nombre = str(fila["nombre"]).strip()
        iso = str(fila["iso"]).strip().upper()
        id_reg = cache_reg.get(str(fila["region"]).strip())
        r = llamar_sp(conn, "sp_create_country", (nombre, iso, id_reg))
        if r:
            n += 1
    llamar_sp(conn, "sp_create_country", ("Mexico", "MX", cache_reg.get("Americas")))
    print(f"  ✔️  countries: {n} new")


def cargar_niveles(conn):
    """Load socioeconomic levels from clean_niveles.csv into the levels table."""
    print("\nLoading socioeconomic_levels")
    df = leer_clean("clean_niveles.csv")
    if df.empty:
        return
    n = 0
    for _, fila in df.iterrows():
        r = llamar_sp(
            conn, "sp_create_level", (str(fila["description"]).strip(),))
        if r:
            n += 1
    print(f"  ✔️  socioeconomic_levels: {n} new")


def cargar_categorias(conn):
    """Load motive categories from clean_categorias.csv into the motive_categories table."""
    print("\nLoading motive_categories")
    df = leer_clean("clean_categorias.csv")
    if df.empty:
        return
    n = 0
    for _, fila in df.iterrows():
        r = llamar_sp(
            conn,
            "sp_create_motive_category",
            (str(fila["name"]).strip(),),
        )
        if r:
            n += 1
    print(f"✔️motive_categories: {n} new")


def cargar_motivos(conn):
    """Load motives from clean_motivos.csv into the motives table.

    Looks up the category foreign key from the already-loaded
    motive_categories table.
    """
    print("\nLoading motives")
    df = leer_clean("clean_motivos.csv")
    if df.empty:
        return
    rows = leer_sp(conn, "sp_read_all_motive_categories")
    cache_cat = {str(f[1]).strip(): f[0] for f in rows}
    n = 0
    for _, fila in df.iterrows():
        id_cat = cache_cat.get(str(fila["category"]).strip())
        r = llamar_sp(
            conn, "sp_create_motive", (str(fila["name"]).strip(), id_cat))
        if r:
            n += 1
    print(f"✔️  motives: {n} new")


def cargar_periodos(conn):
    """Load year periods from clean_periodos.csv into the periods table."""
    print("\nLoading periods")
    df = leer_clean("clean_periodos.csv")
    if df.empty:
        return
    n = 0
    for _, fila in df.iterrows():
        r = llamar_sp(conn, "sp_create_period", (int(fila["year"]),))
        if r:
            n += 1
    print(f"✔️  periods: {n} new")


def cargar_risks(conn):
    """Load risks from both clean_riesgos.csv (base catalog) and
    clean_riesgos_missing.csv (real causes from the Missing Migrants dataset).

    Validates that each risk type is one of: Physical, Legal, Economic, Social.
    Defaults to 'Physical' for invalid types.
    """
    print("\nLoading risks")
    n = 0
    for archivo in ["clean_riesgos.csv", "clean_riesgos_missing.csv"]:
        df = leer_clean(archivo)
        for _, fila in df.iterrows():
            tipo = str(fila["type"]).strip()
            if tipo not in ["Physical", "Legal", "Economic", "Social"]:
                tipo = "Physical"
            desc = str(fila["description"]).strip()[:249]
            r = llamar_sp(conn, "sp_create_risk", (desc, tipo))
            if r:
                n += 1
    print(f"✔️  risks: {n} new")


def cargar_impacts(conn):
    """Load impacts from clean_impactos.csv into the impacts table.

    Validates that each impact type is one of: Social, Economic.
    Defaults to 'Social' for invalid types.
    """
    print("\nLoading impacts")
    df = leer_clean("clean_impactos.csv")
    if df.empty:
        return
    n = 0
    for _, fila in df.iterrows():
        tipo = str(fila["type"]).strip()
        if tipo not in ["Social", "Economic"]:
            tipo = "Social"
        r = llamar_sp(
            conn, "sp_create_impact", (tipo, str(fila["description"]).strip())
        )
        if r:
            n += 1
    print(f"✔️impacts: {n} new")


def cargar_global_statistics(conn):
    """Load global statistics from two sources:

    1. clean_estadisticas.csv (combined WB API, WB CSV, WorldPop, UNDESA)
    2. clean_unhcr.csv (UNHCR asylum-seeker demographics)

    Looks up the country foreign key by ISO code or name. Calls
    sp_create_global_stat with (year, country_id, total, percentage, source).
    """
    print("\nLoading global_statistics")
    rows = leer_sp(conn, "sp_read_all_countries")
    cache_nombre = {str(f[1]).strip().lower(): f[0] for f in rows}
    cache_iso = {str(f[2]).strip().upper(): f[0] for f in rows if f[2]}

    def buscar_pais(iso, nombre):
        id_p = cache_iso.get(str(iso).strip().upper()) if iso else None
        if not id_p:
            id_p = cache_nombre.get(str(nombre).strip().lower())
        return id_p

    n = 0
    fuentes = [
        ("clean_estadisticas.csv", "iso", "pais", "anio", "total_migrantes", "world_percentage",),
        ("clean_unhcr.csv", "iso_origen", "pais_origen", "anio", "total", None),
    ]
    for archivo, col_iso, col_pais, col_anio, col_total, col_pct in fuentes:
        df = leer_clean(archivo)
        if df.empty:
            continue
        n_archivo = 0
        for _, fila in df.iterrows():
            id_pais = buscar_pais(
                fila.get(col_iso, ""), fila.get(col_pais, "")
            )
            if not id_pais:
                continue
            pct = (
                float(fila.get(col_pct, 0))
                if col_pct and col_pct in fila
                else 0.0
            )

            # Determine a descriptive source label based on the file being processed
            fuente_origen = "UNHCR" if "unhcr" in archivo else "IOM / World Data"

            # Send exactly the 5 parameters expected by the stored procedure:
            # (p_year, p_country, p_total, p_pct, p_source)
            r = llamar_sp(
                conn,
                "sp_create_global_stat",
                (
                    int(fila[col_anio]),
                    id_pais,
                    int(fila.get(col_total, 0)),
                    pct,
                    fuente_origen
                ),
            )
            if r:
                n_archivo += 1
        print(f"  → {archivo}: {n_archivo} inserted")
        n += n_archivo

    print(f"☑️️global_statistics total: {n}")


def cargar_migrants_migrations(conn):
    """Load migrants and migrations from clean_inegi.csv.

    This is the most complex loading function:
    1. Looks up origin country, socioeconomic level, and motive IDs from
       already-loaded tables (using read SPs and building caches).
    2. Creates each migrant via sp_create_migrant_full (age, sex, origin, level).
    3. Creates the corresponding migration record (destination, motive, period).
    4. Updates the migration status for non-transit migrants.
    """
    print("\nLoading migrants and migrations (INEGI)")
    df = leer_clean("clean_inegi.csv")
    if df.empty:
        print(" ⚠ clean_inegi.csv empty")
        return
    # Build lookup caches from already-loaded tables (foreign key references)
    rows_paises = leer_sp(conn, "sp_read_all_countries")
    cache_paises = {str(f[1]).strip().lower(): f[0] for f in rows_paises}
    rows_niveles = leer_sp(conn, "sp_read_all_levels")
    cache_nivel = {str(f[1]).strip(): f[0] for f in rows_niveles}
    rows_motivos = leer_sp(conn, "sp_read_all_motives")
    cache_motivo = {str(f[1]).strip(): f[0] for f in rows_motivos}
    rows_periodos = leer_sp(conn, "sp_read_all_periods")
    cache_periodo = {int(f[1]): f[0] for f in rows_periodos}
    # Mexico is the default destination country — verify it exists
    id_mexico = cache_paises.get("mexico")
    if not id_mexico:
        print("❌México no encontrado en countries.")
        return
    print(f"Countries cache: {len(cache_paises)} | levels: {len(cache_nivel)} "
          f"| motives: {len(cache_motivo)} | periods: {len(cache_periodo)}")
    n_migrants = 0
    n_migs = 0
    n_errores = 0
    # Iterate over each INEGI survey record to create migrants + migrations
    for _, fila in df.iterrows():
        id_origen = cache_paises.get(
            str(fila.get("origin_country", "Mexico")).strip().lower(), id_mexico)

        id_nivel = cache_nivel.get(
            str(fila.get("socioeconomic_level", "Middle")).strip(),
            cache_nivel.get("Middle"), )

        sexo = str(fila.get("sex", "Other")).strip()
        if sexo not in ["Male", "Female", "Other"]:
            sexo = "Other"

        try:
            edad = int(fila.get("age", 28))
            if not 0 <= edad <= 120:
                edad = 28
        except (ValueError, TypeError):
            edad = 28

        id_migrante = llamar_sp_migrant(conn, edad, sexo, id_origen, id_nivel)
        if not id_migrante:
            n_errores += 1
            continue
        n_migrants += 1

        id_motivo = cache_motivo.get(
            str(fila.get("motive", "Other")).strip(), cache_motivo.get("Other"))

        try:
            anio = int(fila.get("year", 2020))
        except (ValueError, TypeError):
            anio = 2020

        id_periodo = cache_periodo.get(anio)
        if not id_periodo:
            llamar_sp(conn, "sp_create_period", (anio,))
            new = leer_sp(conn, "sp_read_period_by_year", (anio,))
            if new:
                id_periodo = new[0][0]
                cache_periodo[anio] = id_periodo

        if not id_motivo or not id_periodo:
            n_errores += 1
            continue

        status = str(fila.get("status", "Established")).strip()
        if status not in ["In transit", "Established", "Returned", "Deported"]:
            status = "Established"

        id_destino = cache_paises.get(
            str(fila.get("destination_country", "Mexico")).strip().lower(),
            id_mexico,
        )

        r = llamar_sp(
            conn,
            "sp_create_migration",
            (id_migrante, id_destino, id_motivo, id_periodo),
        )
        if r:
            n_migs += 1
            if status != "In transit":
                rows_mig = leer_sp(
                    conn, "sp_read_migrant_last", (id_migrante,))
                if rows_mig:
                    llamar_sp(
                        conn, "sp_update_migration", (rows_mig[0][0], status))
    print(f"✔️migrants:{n_migrants}")
    print(f" ️☑️migrations: {n_migs}")
    if n_errores:
        print(f"⚠ omitidos: {n_errores}")


def cargar_migration_risk(conn):
    """Link migration records to risks from the Missing Migrants dataset.

    Reads unique causes of death from clean_missing.csv, matches them to
    risk records already in the database, and creates migration_risk
    associations (up to 10 per cause).
    """
    print("\nLoading migration_risk...")
    df_missing = leer_clean("clean_missing.csv")
    if df_missing.empty:
        print("⚠ clean_missing.csv empty")
        return
    rows_risk = leer_sp(conn, "sp_read_all_risks")
    cache_risk = {str(f[1]).strip(): f[0] for f in rows_risk}
    ids_mig = [f[0] for f in leer_sp(conn, "sp_read_all_migrations")]
    if not ids_mig:
        print("⚠ No hay migrations en BD")
        return
    causas = df_missing["Cause of Death"].dropna().unique()
    n = 0
    idx = 0
    for causa in causas:
        id_risk = cache_risk.get(str(causa).strip())
        if not id_risk:
            continue
        cantidad = min(10, len(ids_mig))
        for i in range(cantidad):
            id_mig = ids_mig[(idx + i) % len(ids_mig)]
            r = llamar_sp(conn, "sp_create_migration_risk", (id_mig, id_risk))
            if r:
                n += 1
        idx = (idx + cantidad) % len(ids_mig)
    print(f"✔️migration_risk: {n} links")


def cargar_migration_impact(conn):
    """Link migration records to impacts.

    Distributes each impact across migration records evenly (round-robin),
    creating up to 50 migration_impact associations per impact.
    """
    print("\nLoading migration_impact...")
    rows_imp = leer_sp(conn, "sp_read_all_impacts")
    cache_imp = {str(f[1]).strip(): f[0] for f in rows_imp}
    ids_mig = [f[0] for f in leer_sp(conn, "sp_read_all_migrations")]
    if not ids_mig:
        print("⚠No hay migrations en BD")
        return
    impactos = list(cache_imp.items())
    n = 0
    for i, (desc, id_imp) in enumerate(impactos):
        subconjunto = ids_mig[i:: len(impactos)] if impactos else []
        for id_mig in subconjunto[:50]:
            r = llamar_sp(conn, "sp_create_migration_impact", (id_mig, id_imp))
            if r:
                n += 1
    print(f"✔️migration_impact: {n} links")


def verificar(conn):
    """Print a verification summary showing the row count for each table
    by calling the corresponding sp_read_all_* stored procedure.
    """
    print("\nVERIFICATION - TABLE COUNTS")
    tablas_sp = [("regions", "sp_read_all_regions"), ("countries", "sp_read_all_countries"),
                 ("socioeconomic_levels", "sp_read_all_levels"), ("motive_categories", "sp_read_all_motive_categories"),
                 ("motives", "sp_read_all_motives"), ("periods", "sp_read_all_periods"),
                 ("risks", "sp_read_all_risks"), ("impacts", "sp_read_all_impacts"),
                 ("global_statistics", "sp_read_all_global_stats"), ("migrations", "sp_read_all_migrations"), ]
    for nombre, sp in tablas_sp:
        rows = leer_sp(conn, sp)
        print(f"  {nombre:<30}: {len(rows):>7} records")
    print("\n✅Verification complete")


# =============================================================================
# Main execution: load all tables in the correct order (respecting FKs)
# =============================================================================
if __name__ == "__main__":
    conn = conectar()
    if not conn:
        print("Error in connection parameters")
        exit(1)
    cargar_regions(conn)
    cargar_countries(conn)
    cargar_niveles(conn)
    cargar_categorias(conn)
    cargar_motivos(conn)
    cargar_periodos(conn)
    cargar_risks(conn)
    cargar_impacts(conn)
    cargar_global_statistics(conn)
    cargar_migrants_migrations(conn)
    cargar_migration_risk(conn)
    cargar_migration_impact(conn)

    verificar(conn)
    desconectar(conn)