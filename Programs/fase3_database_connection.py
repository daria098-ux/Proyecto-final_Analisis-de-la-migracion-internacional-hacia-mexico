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
