import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
# Configurar Entorno
DB_CONFIG = {
  "host":     "localhost",
  "user":     "root",
  "password": "12345678",
  "database": "mexico_migration",
  "port":     3306}

CARPETA_CLEAN = "data_clean"
# Conexión
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
# Helpers
def leer_clean(nombre):
  ruta = f"{CARPETA_CLEAN}/{nombre}"
  if not os.path.exists(ruta):
      print(f"  ⚠  No encontrado: {ruta}")
      return pd.DataFrame()
  df = pd.read_csv(ruta, encoding="utf-8")
  if df.empty:
      print(f"  ⚠  Archivo vacío: {ruta}")
  return df

def ejecutar(conn, sql, valores):
  """Ejecuta un INSERT y devuelve el lastrowid. None si falla."""
  try:
      cu = conn.cursor()
      cu.execute(sql, valores)
      conn.commit()
      return cu.lastrowid
  except Error as e:
      # Duplicados (1062) son normales con INSERT IGNORE → silenciar
      if e.errno != 1062:
          print(f"  ⚠  SQL Error {e.errno}: {e.msg}  | valores={valores}")
      conn.rollback()
      return None

def ejecutar_muchos(conn, sql, lista_valores):
  try:
      cu = conn.cursor()
      cu.executemany(sql, lista_valores)
      conn.commit()
      return cu.rowcount
  except Error as e:
      print(f"  ⚠  executemany Error: {e}")
      conn.rollback()
      return 0

def obtener_id(conn, tabla, campo_pk, campo_busqueda, valor):
  try:
      cu = conn.cursor()
      cu.execute(
          f"SELECT {campo_pk} FROM {campo_pk.split('_id')[0]}s"
          f" WHERE {campo_busqueda} = %s LIMIT 1",
          (valor,))
      res = cu.fetchone()
      return res[0] if res else None
  except Error:
      return None

def obtener_id_directo(conn, sql, valor):
  """SELECT directo con SQL personalizado."""
  try:
      cu = conn.cursor()
      cu.execute(sql, (valor,))
      res = cu.fetchone()
      return res[0] if res else None
  except Error:
      return None

def cache_tabla(conn, sql_all, col_nombre, col_id):
  cu = conn.cursor()
  cu.execute(sql_all)
  return {str(row[col_nombre]).strip(): row[col_id] for row in cu.fetchall()}

# Regions
def cargar_regions(conn):
  print("\n[1] Cargando regions...")
  df = leer_clean("clean_paises.csv")
  if df.empty:
      return
  regiones = df["region"].dropna().unique()
  insertados = 0
  for region in regiones:
      r = ejecutar(conn,
          "INSERT IGNORE INTO regions (name) VALUES (%s)",
          (str(region).strip(),))
      if r:
          insertados += 1
  print(f"  ✔️  regions: {insertados} nuevas / {len(regiones)} únicas")

# Countries
def cargar_countries(conn):
  print("\n[2] Cargando countries...")
  df = leer_clean("clean_paises.csv")
  if df.empty:
      return

  # Caché de regiones
  cache_reg = cache_tabla(conn,
      "SELECT name, region_id FROM regions",
      col_nombre=0, col_id=1)

  insertados = 0
  for _, fila in df.iterrows():
      nombre  = str(fila["nombre"]).strip()
      iso     = str(fila["iso"]).strip().upper()
      region  = str(fila["region"]).strip()
      id_reg  = cache_reg.get(region)

      r = ejecutar(conn,
          "INSERT IGNORE INTO countries (name, iso_code, region_id) VALUES (%s, %s, %s)",
          (nombre, iso, id_reg))
      if r:
          insertados += 1

  # Aseguramos que México esté (a veces no viene en la API si no se agregó)
  ejecutar(conn,
      "INSERT IGNORE INTO countries (name, iso_code, region_id) VALUES (%s, %s, %s)",
      ("Mexico", "MX", cache_reg.get("Americas")))

  print(f"  ✔️  countries: {insertados} nuevas")

# Socioeconomic_levels
def cargar_niveles(conn):
  print("\n[3] Cargando socioeconomic_levels...")
  df = leer_clean("clean_niveles.csv")
  if df.empty:
      return
  lista = [(str(r["description"]).strip(),) for _, r in df.iterrows()]
  n = ejecutar_muchos(conn,
      "INSERT IGNORE INTO socioeconomic_levels (description) VALUES (%s)", lista)
  print(f"  ✔️  socioeconomic_levels: {len(lista)} procesados")


# Motive_categories
def cargar_categorias(conn):
  print("\n[4] Cargando motive_categories...")
  df = leer_clean("clean_categorias.csv")
  if df.empty:
      return
  lista = [(str(r["name"]).strip(),) for _, r in df.iterrows()]
  ejecutar_muchos(conn,
      "INSERT IGNORE INTO motive_categories (name) VALUES (%s)", lista)
  print(f"  ✔️  motive_categories: {len(lista)} procesados")


# Motives
def cargar_motivos(conn):
  print("\n[5] Cargando motives...")
  df = leer_clean("clean_motivos.csv")
  if df.empty:
      return


  cache_cat = cache_tabla(conn,
      "SELECT name, category_id FROM motive_categories",col_nombre=0, col_id=1)
  insertados = 0
  for _, fila in df.iterrows():
      nombre = str(fila["name"]).strip()
      cat    = str(fila["category"]).strip()
      id_cat = cache_cat.get(cat)
      r = ejecutar(conn,
          "INSERT IGNORE INTO motives (name, category_id) VALUES (%s, %s)",
          (nombre, id_cat))
      if r:
          insertados += 1
  print(f"  ✔️  motives: {insertados} nuevos")


# Periods
def cargar_periodos(conn):
  print("\n[6] Cargando periods...")
  df = leer_clean("clean_periodos.csv")
  if df.empty:
      return
  lista = [(int(r["year"]),) for _, r in df.iterrows()]
  ejecutar_muchos(conn,
      "INSERT IGNORE INTO periods (year) VALUES (%s)", lista)
  print(f"  ✔️  periods: {len(lista)} procesados")


# Risks
def cargar_risks(conn):
  print("\n[7] Cargando risks...")
  insertados = 0


  # Catálogo base
  df_base = leer_clean("clean_riesgos.csv")
  for _, fila in df_base.iterrows():
      r = ejecutar(conn,
          "INSERT IGNORE INTO risks (description, type) VALUES (%s, %s)",
          (str(fila["description"]).strip(), str(fila["type"]).strip()))
      if r:
          insertados += 1


  # Causas reales del Missing Migrants Dataset
  df_real = leer_clean("clean_riesgos_missing.csv")
  for _, fila in df_real.iterrows():
      desc = str(fila["description"]).strip()[:249]   # max 250 chars
      tipo = str(fila["type"]).strip()
      if tipo not in ["Physical", "Legal", "Economic", "Social"]:
          tipo = "Physical"
      r = ejecutar(conn,
          "INSERT IGNORE INTO risks (description, type) VALUES (%s, %s)",
          (desc, tipo))
      if r:
          insertados += 1


  print(f"  ✔️  risks: {insertados} nuevos")


# Impacts
def cargar_impacts(conn):
  print("\n[8] Cargando impacts...")
  df = leer_clean("clean_impactos.csv")
  if df.empty:
      return
  insertados = 0
  for _, fila in df.iterrows():
      tipo = str(fila["type"]).strip()
      desc = str(fila["description"]).strip()
      if tipo not in ["Social", "Economic"]:
          tipo = "Social"
      r = ejecutar(conn,
          "INSERT IGNORE INTO impacts (type, description) VALUES (%s, %s)",
          (tipo, desc))
      if r:
          insertados += 1
  print(f"  ✔️  impacts: {insertados} nuevos")

# 9. GLOBAL_STATISTICS
# =============================================================================
def cargar_global_statistics(conn):
    print("\n[9] Cargando global_statistics...")

    # Caché de países por nombre y por ISO
    cu = conn.cursor()
    cu.execute("SELECT name, iso_code, country_id FROM countries")
    filas = cu.fetchall()
    cache_nombre = {str(f[0]).strip().lower(): f[2] for f in filas}
    cache_iso    = {str(f[1]).strip().upper(): f[2] for f in filas if f[1]}

    def buscar_pais(iso, nombre):
        id_p = cache_iso.get(str(iso).strip().upper()) if iso else None
        if not id_p:
            id_p = cache_nombre.get(str(nombre).strip().lower())
        return id_p

    insertados = 0

    # ── Fuente 1: clean_estadisticas.csv (WB API + WB CSV + WorldPop + UNDESA)
    df_est = leer_clean("clean_estadisticas.csv")
    if not df_est.empty:
        for _, fila in df_est.iterrows():
            id_pais = buscar_pais(fila.get("iso",""), fila.get("pais",""))
            if not id_pais:
                continue
            r = ejecutar(conn,
                """INSERT IGNORE INTO global_statistics
                   (year, country_id, total_migrants, world_percentage)
                   VALUES (%s, %s, %s, %s)""",
                (int(fila["anio"]), id_pais,
                 int(fila["total_migrantes"]),
                 float(fila.get("world_percentage", 0))))
            if r:
                insertados += 1
        print(f"  → estadisticas.csv: {insertados} insertados")

    # ── Fuente 2: clean_unhcr.csv (demografía UNHCR por país de origen)
    df_unhcr = leer_clean("clean_unhcr.csv")
    n_unhcr = 0
    if not df_unhcr.empty:
        for _, fila in df_unhcr.iterrows():
            id_pais = buscar_pais(fila.get("iso_origen",""), fila.get("pais_origen",""))
            if not id_pais:
                continue
            r = ejecutar(conn,
                """INSERT IGNORE INTO global_statistics
                   (year, country_id, total_migrants, world_percentage)
                   VALUES (%s, %s, %s, %s)""",
                (int(fila["anio"]), id_pais,
                 int(fila.get("total", 0)), 0.0))
            if r:
                n_unhcr += 1
        print(f"  → unhcr.csv       : {n_unhcr} insertados")
        insertados += n_unhcr

    print(f"  ✔️  global_statistics total: {insertados}")

# =============================================================================
# 10. MIGRANTS  +  11. MIGRATIONS
# =============================================================================
def cargar_migrants_migrations(conn):
    print("\n[10/11] Cargando migrants y migrations (INEGI)...")

    df = leer_clean("clean_inegi.csv")
    if df.empty:
        print("  ⚠  clean_inegi.csv vacío — sin registros de migrants/migrations")
        return

    # Cachés
    cu = conn.cursor()

    cu.execute("SELECT name, country_id FROM countries")
    cache_paises = {str(r[0]).strip().lower(): r[1] for r in cu.fetchall()}

    cu.execute("SELECT description, level_id FROM socioeconomic_levels")
    cache_nivel = {str(r[0]).strip(): r[1] for r in cu.fetchall()}

    cu.execute("SELECT name, motive_id FROM motives")
    cache_motivo = {str(r[0]).strip(): r[1] for r in cu.fetchall()}

    cu.execute("SELECT year, period_id FROM periods")
    cache_periodo = {int(r[0]): r[1] for r in cu.fetchall()}

    # ID de México (destino principal)
    id_mexico = cache_paises.get("mexico")
    if not id_mexico:
        print("  ❌  México no encontrado en countries. Revisa cargar_countries().")
        return

    n_migrants  = 0
    n_migs      = 0
    n_errores   = 0

    for _, fila in df.iterrows():
        # ── País de origen ──────────────────────────────────────────────
        nombre_orig = str(fila.get("origin_country", "Mexico")).strip().lower()
        id_origen   = cache_paises.get(nombre_orig, id_mexico)

        # ── Nivel socioeconómico ────────────────────────────────────────
        nivel_str = str(fila.get("socioeconomic_level", "Middle")).strip()
        id_nivel  = cache_nivel.get(nivel_str, cache_nivel.get("Middle"))

        # ── Sexo ────────────────────────────────────────────────────────
        sexo = str(fila.get("sex", "Other")).strip()
        if sexo not in ["Male", "Female", "Other"]:
            sexo = "Other"

        # ── Edad ────────────────────────────────────────────────────────
        try:
            edad = int(fila.get("age", 28))
            if not 0 <= edad <= 120:
                edad = 28
        except (ValueError, TypeError):
            edad = 28

        # ── INSERT migrant ──────────────────────────────────────────────
        id_migrante = ejecutar(conn,
            """INSERT INTO migrants
               (age, sex, origin_country_id, socioeconomic_level_id)
               VALUES (%s, %s, %s, %s)""",
            (edad, sexo, id_origen, id_nivel))

        if not id_migrante:
            n_errores += 1
            continue
        n_migrants += 1

        # ── Motivo ──────────────────────────────────────────────────────
        motivo_str = str(fila.get("motive", "Other")).strip()
        id_motivo  = cache_motivo.get(motivo_str, cache_motivo.get("Other"))

        # ── Periodo ─────────────────────────────────────────────────────
        try:
            anio = int(fila.get("year", 2020))
        except (ValueError, TypeError):
            anio = 2020
        id_periodo = cache_periodo.get(anio)
        if not id_periodo:
            # Si el año no está en catálogo, insertar y actualizar caché
            r = ejecutar(conn,
                "INSERT IGNORE INTO periods (year) VALUES (%s)", (anio,))
            cu.execute("SELECT period_id FROM periods WHERE year = %s", (anio,))
            res = cu.fetchone()
            id_periodo = res[0] if res else None
            if id_periodo:
                cache_periodo[anio] = id_periodo

        if not id_motivo or not id_periodo:
            n_errores += 1
            continue

        # ── Status ──────────────────────────────────────────────────────
        status = str(fila.get("status", "Established")).strip()
        if status not in ["In transit", "Established", "Returned", "Deported"]:
            status = "Established"

        # ── País destino ────────────────────────────────────────────────
        dest_str   = str(fila.get("destination_country", "Mexico")).strip().lower()
        id_destino = cache_paises.get(dest_str, id_mexico)

        # ── INSERT migration ────────────────────────────────────────────
        r = ejecutar(conn,
            """INSERT IGNORE INTO migrations
               (migrant_id, destination_country_id, motive_id, period_id, status_)
               VALUES (%s, %s, %s, %s, %s)""",
            (id_migrante, id_destino, id_motivo, id_periodo, status))
        if r:
            n_migs += 1

    print(f"  ✔️  migrants insertados : {n_migrants}")
    print(f"  ✔️  migrations insertados: {n_migs}")
    if n_errores:
        print(f"  ⚠  filas omitidas (FK no encontrada): {n_errores}")

# =============================================================================
# 12. MIGRATION_RISK  (vincula migraciones con riesgos del Missing Dataset)
# =============================================================================
def cargar_migration_risk(conn):
    print("\n[12] Cargando migration_risk...")

    df_missing = leer_clean("clean_missing.csv")
    if df_missing.empty:
        print("  ⚠  clean_missing.csv vacío")
        return

    # Caché de riesgos por descripción
    cu = conn.cursor()
    cu.execute("SELECT description, risk_id FROM risks")
    cache_risk = {str(r[0]).strip(): r[1] for r in cu.fetchall()}

    # Caché de países
    cu.execute("SELECT name, country_id FROM countries")
    cache_paises = {str(r[0]).strip().lower(): r[1] for r in cu.fetchall()}
    id_mexico = cache_paises.get("mexico")

    # Tomamos todas las migraciones insertadas (las del INEGI)
    cu.execute("SELECT migration_id FROM migrations LIMIT 5000")
    ids_mig = [r[0] for r in cu.fetchall()]
    if not ids_mig:
        print("  ⚠  No hay migrations en BD aún")
        return

    # Estrategia: vinculamos cada causa de muerte única con las
    # migraciones cuyo país de destino sea México, distribuyendo
    # los riesgos de forma proporcional por región del incidente
    causas_unicas = (
        df_missing["Cause of Death"]
        .dropna()
        .unique()
    )

    n = 0
    idx_mig = 0   # índice rotatorio sobre ids_mig
    for causa in causas_unicas:
        id_risk = cache_risk.get(str(causa).strip())
        if not id_risk:
            continue
        # Asignamos este riesgo a las primeras N migraciones (rotatorio)
        cantidad = min(10, len(ids_mig))
        for i in range(cantidad):
            id_mig = ids_mig[(idx_mig + i) % len(ids_mig)]
            r = ejecutar(conn,
                "INSERT IGNORE INTO migration_risk (migration_id, risk_id) VALUES (%s, %s)",
                (id_mig, id_risk))
            if r:
                n += 1
        idx_mig = (idx_mig + cantidad) % len(ids_mig)

    print(f"  ✔️  migration_risk: {n} vínculos insertados")

# =============================================================================
# 13. MIGRATION_IMPACT  (vincula migraciones con impactos)
# =============================================================================
def cargar_migration_impact(conn):
    print("\n[13] Cargando migration_impact...")

    # Caché de impactos
    cu = conn.cursor()
    cu.execute("SELECT description, impact_id FROM impacts")
    cache_impact = {str(r[0]).strip(): r[1] for r in cu.fetchall()}

    cu.execute("SELECT migration_id FROM migrations LIMIT 5000")
    ids_mig = [r[0] for r in cu.fetchall()]
    if not ids_mig:
        print("  ⚠  No hay migrations en BD aún")
        return

    # Cada impacto se vincula con un subconjunto de migraciones
    impactos = list(cache_impact.items())  # [(descripcion, id), ...]
    n = 0
    for i, (desc, id_imp) in enumerate(impactos):
        # Tomamos cada 7mo elemento de ids_mig para distribuir
        subconjunto = ids_mig[i::len(impactos)] if len(impactos) > 0 else []
        for id_mig in subconjunto[:50]:   # máximo 50 vínculos por impacto
            r = ejecutar(conn,
                "INSERT IGNORE INTO migration_impact (migration_id, impact_id) VALUES (%s, %s)",
                (id_mig, id_imp))
            if r:
                n += 1

    print(f"  ✔️  migration_impact: {n} vínculos insertados")

# =============================================================================
# VERIFICACIÓN FINAL
# =============================================================================
def verificar(conn):
    print("\n" + "=" * 55)
    print("VERIFICACIÓN — CONTEO POR TABLA")
    print("=" * 55)

    tablas = [
        "regions", "countries", "socioeconomic_levels",
        "motive_categories", "motives", "periods",
        "risks", "impacts", "global_statistics",
        "migrants", "migrations",
        "migration_risk", "migration_impact", "audit",
    ]
    cu = conn.cursor()
    for tabla in tablas:
        try:
            cu.execute(f"SELECT COUNT(*) FROM {tabla}")
            n = cu.fetchone()[0]
            print(f"  {tabla:<30}: {n:>7} registros")
        except Error as e:
            print(f"  {tabla:<30}: ❌ {e}")

    print("\n--- Top 5 países de origen ---")
    cu.execute("""
        SELECT c.name, COUNT(*) AS total
        FROM migrants m
        JOIN countries c ON m.origin_country_id = c.country_id
        GROUP BY c.name ORDER BY total DESC LIMIT 5
    """)
    for row in cu.fetchall():
        print(f"  {row[0]:<25}: {row[1]}")

    print("\n--- Top 5 motivos ---")
    cu.execute("""
        SELECT mo.name, COUNT(*) AS total
        FROM migrations mg
        JOIN motives mo ON mg.motive_id = mo.motive_id
        GROUP BY mo.name ORDER BY total DESC LIMIT 5
    """)
    for row in cu.fetchall():
        print(f"  {row[0]:<35}: {row[1]}")

    print("\n--- Distribución por sexo ---")
    cu.execute("""
        SELECT sex, COUNT(*) FROM migrants GROUP BY sex
    """)
    for row in cu.fetchall():
        print(f"  {row[0]:<10}: {row[1]}")

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("\n💾 FASE 3 — CARGA A MYSQL\n")

    conn = conectar()
    if not conn:
        print("No se pudo conectar. Revisa DB_CONFIG.")
        exit(1)

    # Orden estricto respetando FK
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

    print("\n✅  Fase 3 completada — BD lista para la Fase 4 (dashboards)")