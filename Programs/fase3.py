import os
import warnings
import mysql.connector
from mysql.connector import Error
import pandas as pd

DB_CONFIG = {"host": "localhost", "user": "root", "password": "Yaquelin09/",
             "database": "mexico_migration", "port": 3307, }
CARPETA_CLEAN = "data_clean"


def conectar():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✔️  Conexión a MySQL exitosa")
        return conn
    except Error as e:
        print(f"❌  Error de conexión: {e}")
        return None


def desconectar(conn):
    if conn and conn.is_connected():
        conn.close()


def leer_clean(nombre):
    ruta = f"{CARPETA_CLEAN}/{nombre}"
    if not os.path.exists(ruta):
        print(f" No encontrado: {ruta}")
        return pd.DataFrame()
    df = pd.read_csv(ruta, encoding="utf-8")
    if df.empty:
        print(f"Archivo vacío: {ruta}")
    return df


def llamar_sp(conn, sp, params=()):
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
    filas = []
    try:
        cu = conn.cursor()
        cu.callproc(sp, params)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for resultado in cu.stored_results():
                filas = resultado.fetchall()
        cu.close()
    except Error as e:
        print(f"{sp} lectura → {e}")
    return filas


def llamar_sp_migrant(conn, edad, sexo, id_origen, id_nivel):
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
    print("\nCargando regions")
    df = leer_clean("clean_paises.csv")
    if df.empty:
        return
    regiones = df["region"].dropna().unique()
    n = 0
    for region in regiones:
        r = llamar_sp(conn, "sp_create_region", (str(region).strip(),))
        if r:
            n += 1
    print(f"  ✔️  regions: {n} nuevas / {len(regiones)} únicas")


def cargar_countries(conn):
    print("\nCargando countries")
    df = leer_clean("clean_paises.csv")
    if df.empty:
        return
    filas = leer_sp(conn, "sp_read_all_regions")
    cache_reg = {str(f[1]).strip(): f[0] for f in filas}
    n = 0
    for _, fila in df.iterrows():
        nombre = str(fila["nombre"]).strip()
        iso = str(fila["iso"]).strip().upper()
        id_reg = cache_reg.get(str(fila["region"]).strip())
        r = llamar_sp(conn, "sp_create_country", (nombre, iso, id_reg))
        if r:
            n += 1
    llamar_sp(conn, "sp_create_country", ("Mexico", "MX", cache_reg.get("Americas")))
    print(f"  ✔️  countries: {n} nuevas")


def cargar_niveles(conn):
    print("\nCargando socioeconomic_levels")
    df = leer_clean("clean_niveles.csv")
    if df.empty:
        return
    n = 0
    for _, fila in df.iterrows():
        r = llamar_sp(
            conn, "sp_create_level", (str(fila["description"]).strip(),))
        if r:
            n += 1
    print(f"  ✔️  socioeconomic_levels: {n} nuevas")


def cargar_categorias(conn):
    print("\nCargando motive_categories")
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
    print(f"✔️motive_categories: {n} nuevas")


def cargar_motivos(conn):
    print("\nCargando motives")
    df = leer_clean("clean_motivos.csv")
    if df.empty:
        return
    filas = leer_sp(conn, "sp_read_all_motive_categories")
    cache_cat = {str(f[1]).strip(): f[0] for f in filas}
    n = 0
    for _, fila in df.iterrows():
        id_cat = cache_cat.get(str(fila["category"]).strip())
        r = llamar_sp(
            conn, "sp_create_motive", (str(fila["name"]).strip(), id_cat))
        if r:
            n += 1
    print(f"✔️  motives: {n} nuevos")


def cargar_periodos(conn):
    print("\nCargando periods")
    df = leer_clean("clean_periodos.csv")
    if df.empty:
        return
    n = 0
    for _, fila in df.iterrows():
        r = llamar_sp(conn, "sp_create_period", (int(fila["year"]),))
        if r:
            n += 1
    print(f"✔️  periods: {n} nuevos")


def cargar_risks(conn):
    print("\nCargando risks")
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
    print(f"✔️  risks: {n} nuevos")


def cargar_impacts(conn):
    print("\nCargando impacts")
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
    print(f"✔️impacts: {n} nuevos")


def cargar_global_statistics(conn):
    print("\nCargando global_statistics")
    filas = leer_sp(conn, "sp_read_all_countries")
    cache_nombre = {str(f[1]).strip().lower(): f[0] for f in filas}
    cache_iso = {str(f[2]).strip().upper(): f[0] for f in filas if f[2]}

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

            # Determinamos una fuente descriptiva según el archivo procesado
            fuente_origen = "UNHCR" if "unhcr" in archivo else "IOM / World Data"

            # Enviamos exactamente los 5 parámetros que tu procedimiento espera:
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
        print(f"  → {archivo}: {n_archivo} insertados")
        n += n_archivo

    print(f"☑️️global_statistics total: {n}")


def cargar_migrants_migrations(conn):
    print("\nCargando migrants y migrations (INEGI)")
    df = leer_clean("clean_inegi.csv")
    if df.empty:
        print(" ⚠ clean_inegi.csv vacío")
        return
    filas_paises = leer_sp(conn, "sp_read_all_countries")
    cache_paises = {str(f[1]).strip().lower(): f[0] for f in filas_paises}
    filas_niveles = leer_sp(conn, "sp_read_all_levels")
    cache_nivel = {str(f[1]).strip(): f[0] for f in filas_niveles}
    filas_motivos = leer_sp(conn, "sp_read_all_motives")
    cache_motivo = {str(f[1]).strip(): f[0] for f in filas_motivos}
    filas_periodos = leer_sp(conn, "sp_read_all_periods")
    cache_periodo = {int(f[1]): f[0] for f in filas_periodos}
    id_mexico = cache_paises.get("mexico")
    if not id_mexico:
        print("❌México no encontrado en countries.")
        return
    print(f"Cache países: {len(cache_paises)} | niveles: {len(cache_nivel)} "
          f"| motivos: {len(cache_motivo)} | periodos: {len(cache_periodo)}")
    n_migrants = 0
    n_migs = 0
    n_errores = 0
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
            nuevos = leer_sp(conn, "sp_read_period_by_year", (anio,))
            if nuevos:
                id_periodo = nuevos[0][0]
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
                filas_mig = leer_sp(
                    conn, "sp_read_migrant_last", (id_migrante,))
                if filas_mig:
                    llamar_sp(
                        conn, "sp_update_migration", (filas_mig[0][0], status))
    print(f"✔️migrants:{n_migrants}")
    print(f" ️☑️migrations: {n_migs}")
    if n_errores:
        print(f"⚠ omitidos: {n_errores}")


def cargar_migration_risk(conn):
    print("\nCargando migration_risk...")
    df_missing = leer_clean("clean_missing.csv")
    if df_missing.empty:
        print("⚠ clean_missing.csv vacío")
        return
    filas_risk = leer_sp(conn, "sp_read_all_risks")
    cache_risk = {str(f[1]).strip(): f[0] for f in filas_risk}
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
    print(f"✔️migration_risk: {n} vínculos")


def cargar_migration_impact(conn):
    print("\nCargando migration_impact...")
    filas_imp = leer_sp(conn, "sp_read_all_impacts")
    cache_imp = {str(f[1]).strip(): f[0] for f in filas_imp}
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
    print(f"✔️migration_impact: {n} vínculos")


def verificar(conn):
    print("\nVERIFICACIÓN — CONTEO POR TABLA")
    tablas_sp = [("regions", "sp_read_all_regions"), ("countries", "sp_read_all_countries"),
                 ("socioeconomic_levels", "sp_read_all_levels"), ("motive_categories", "sp_read_all_motive_categories"),
                 ("motives", "sp_read_all_motives"), ("periods", "sp_read_all_periods"),
                 ("risks", "sp_read_all_risks"), ("impacts", "sp_read_all_impacts"),
                 ("global_statistics", "sp_read_all_global_stats"), ("migrations", "sp_read_all_migrations"), ]
    for nombre, sp in tablas_sp:
        filas = leer_sp(conn, sp)
        print(f"  {nombre:<30}: {len(filas):>7} registros")
    print("\n✅Verificación completada")


if __name__ == "__main__":
    conn = conectar()
    if not conn:
        print("Error en los parámetros de conexión")
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