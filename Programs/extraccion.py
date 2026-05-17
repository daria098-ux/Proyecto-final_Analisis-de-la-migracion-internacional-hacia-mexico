import requests
import pandas as pd
import os


BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CARPETA_RAW = os.path.join(BASE_DIR, "data_raw")
os.makedirs(CARPETA_RAW, exist_ok=True)


ARCHIVO_UNDESA   = os.path.join(BASE_DIR, "cleaned_undesa_2024_ims_stock_by_sex_destination_and_origin_1990-2024.csv")
ARCHIVO_WORLDPOP = os.path.join(BASE_DIR, "world_pop_mig_186_countries.csv")
ARCHIVO_MISSING  = os.path.join(BASE_DIR, "Global_Missing_Migrants_Dataset.csv")
ARCHIVO_WB_DATA  = os.path.join(BASE_DIR, "data.csv")
ARCHIVO_INEGI    = os.path.join(BASE_DIR, "TMIGRANTE.csv")


MAX_PAGINAS_UNHCR = 50




def _detectar_encoding(ruta, candidatos=("utf-16", "utf-8-sig", "utf-8", "latin-1")):
   for enc in candidatos:
       try:
           with open(ruta, encoding=enc) as f:
               f.read(2048)
           return enc
       except (UnicodeDecodeError, UnicodeError):
           continue
   return "latin-1"




# SECCION de: APIs


def extraer_api_paises():
   print("=" * 55)
   print("[API 1] REST Countries informacion de paises")
   print("=" * 55)
   paises_iso = [
       "MX", "US", "GT", "HN", "SV", "VE", "CO",
       "CU", "HT", "NI", "EC", "PE", "BO", "BR",
       "AR", "DO", "JM", "PY", "UY", "PA",]
   registros = []
   for iso in paises_iso:
       url = f"https://restcountries.com/v3.1/alpha/{iso}"
       try:
           resp = requests.get(url, timeout=10)
           if resp.status_code == 200:
               info = resp.json()[0]
               registros.append({
                   "iso":    iso,
                   "nombre": info["name"]["common"],
                   "region": info.get("region", "Unknown"),})
               print(f"✔️{iso} — {info['name']['common']}")
           else:
               print(f"❌{iso} — HTTP {resp.status_code}")
       except Exception as e:
           print(f"❌{iso} — Error: {e}")
   df   = pd.DataFrame(registros)
   ruta = os.path.join(CARPETA_RAW, "raw_api_paises.csv")
   df.to_csv(ruta, index=False, encoding="utf-8")
   print(f"\nGuardado: {ruta} ({len(df)} registros)\n")
   return df




def extraer_api_worldbank():
   print("=" * 55)
   print("[API 2] World Bank migracion neta")
   print("=" * 55)
   paises_iso = ["MX", "US", "GT", "HN", "SV", "VE", "CO",
                 "CU", "HT", "NI", "EC", "PE", "BO", "BR",
                 "AR", "DO", "JM", "PY", "UY", "PA",]
   anio_inicio = 2015
   anio_fin    = 2023
   registros   = []
   for iso in paises_iso:
       url = (
           f"https://api.worldbank.org/v2/country/{iso}"
           f"/indicator/SM.POP.NETM"
           f"?format=json&per_page=50"
       )
       try:
           resp = requests.get(url, timeout=15)
           if resp.status_code == 200:
               data = resp.json()
               if data and len(data) > 1 and data[1]:
                   for item in data[1]:
                       anio  = int(item["date"])
                       valor = item.get("value")
                       if valor is not None and anio_inicio <= anio <= anio_fin:
                           registros.append({
                               "iso":            iso,
                               "pais":           item["country"]["value"],
                               "anio":           anio,
                               "migracion_neta": int(round(float(valor))),})
                   print(f"✔️{iso}")
               else:
                   print(f"❌{iso} sin datos")
           else:
               print(f"❌{iso} HTTP {resp.status_code}")
       except Exception as e:
           print(f"❌{iso} Error: {e}")
   df   = pd.DataFrame(registros)
   ruta = os.path.join(CARPETA_RAW, "raw_api_worldbank.csv")
   df.to_csv(ruta, index=False, encoding="utf-8")
   print(f"\nGuardado: {ruta} ({len(df)} registros)\n")
   return df




def extraer_api_unhcr():
   print("=" * 55)
   print("[API 3] UNHCR demografia migrantes en Mexico por pais")
   print("=" * 55)
   url = "https://api.unhcr.org/population/v1/demographics/"
   paises_coo = {
       "GTM": "Guatemala",        "HND": "Honduras",           "SLV": "El Salvador",
       "VEN": "Venezuela",        "CUB": "Cuba",               "HTI": "Haiti",
       "NIC": "Nicaragua",        "ECU": "Ecuador",            "COL": "Colombia",
       "PER": "Peru",             "BOL": "Bolivia",            "BRA": "Brazil",
       "ARG": "Argentina",        "DOM": "Dominican Republic", "JAM": "Jamaica",
       "PRY": "Paraguay",         "URY": "Uruguay",            "PAN": "Panama",
       "SYR": "Syria",            "AFG": "Afghanistan",        "CMR": "Cameroon",
       "SOM": "Somalia",          "YEM": "Yemen",              "COD": "Dem. Rep. Congo",
       "ETH": "Ethiopia"}
   registros = []
   for iso3, nombre in paises_coo.items():
       pagina     = 1
       total_pais = 0
       while pagina <= MAX_PAGINAS_UNHCR:
           params = {
               "coa":      "MEX",
               "coo":      iso3,
               "yearFrom": 2015,
               "yearTo":   2023,
               "limit":    300,
               "page":     pagina,}
           try:
               resp = requests.get(url, params=params, timeout=15)
               if resp.status_code != 200:
                   print(f"❌ {iso3} pag.{pagina} HTTP {resp.status_code}")
                   break
               data  = resp.json()
               items = data.get("items", [])
               if not items:
                   break
               for item in items:
                   registros.append({
                       "anio":         item.get("year"),
                       "pais_origen":  item.get("coo_name", nombre),
                       "iso_origen":   item.get("coo",      iso3),
                       "pais_destino": item.get("coa_name", "Mexico"),
                       "f_0_4":        item.get("f_0_4",   0),
                       "f_5_11":       item.get("f_5_11",  0),
                       "f_12_17":      item.get("f_12_17", 0),
                       "f_18_59":      item.get("f_18_59", 0),
                       "f_60":         item.get("f_60",    0),
                       "f_total":      item.get("f_total", 0),
                       "m_0_4":        item.get("m_0_4",   0),
                       "m_5_11":       item.get("m_5_11",  0),
                       "m_12_17":      item.get("m_12_17", 0),
                       "m_18_59":      item.get("m_18_59", 0),
                       "m_60":         item.get("m_60",    0),
                       "m_total":      item.get("m_total", 0),
                       "total":        item.get("total",   0),})
               total_pais += len(items)
               max_paginas = data.get("maxPages", 1)
               if pagina >= max_paginas:
                   break
               pagina += 1
           except Exception as e:
               print(f"❌ {iso3} pag.{pagina} error: {e}")
               break
       if total_pais > 0:
           print(f"✔️{nombre:<22} y {total_pais} registros")
       else:
           print(f"{nombre:<22} sin datos")
   df   = pd.DataFrame(registros)
   ruta = os.path.join(CARPETA_RAW, "raw_api_unhcr.csv")
   df.to_csv(ruta, index=False, encoding="utf-8")
   print(f"\nGuardado: {ruta} ({len(df)} registros)\n")
   return df

def extraer_csv_undesa():
   print("=" * 55)
   print("[CSV 1] UNDESA 2024 stock migrantes internacionales")
   print("=" * 55)
   if not os.path.exists(ARCHIVO_UNDESA):
       print(f"❌No encontrado: '{ARCHIVO_UNDESA}'")
       return pd.DataFrame()
   enc = _detectar_encoding(ARCHIVO_UNDESA)
   print(f"   Encoding detectado: {enc}")
   columnas_requeridas = ["Destination", "Origin", "Year", "Total", "Male", "Female"]
   try:
       df = pd.read_csv(ARCHIVO_UNDESA, encoding=enc, usecols=columnas_requeridas)
   except ValueError as e:
       print(f"❌ Error al leer columnas de UNDESA: {e}")
       return pd.DataFrame()
   for col in ["Total", "Male", "Female"]:
       df[col] = (df[col].astype(str)
                         .str.replace(" ", "", regex=False)
                         .str.replace(",", "", regex=False))
       df[col] = pd.to_numeric(df[col], errors="coerce")
   ruta = os.path.join(CARPETA_RAW, "raw_csv_undesa.csv")
   df.to_csv(ruta, index=False, encoding="utf-8")
   print(f"Guardado: {ruta} ({len(df)} registros)\n")
   return df




def extraer_csv_worldpop():
   print("=" * 55)
   print("[CSV 2] World Pop Migration 186 paises")
   print("=" * 55)
   if not os.path.exists(ARCHIVO_WORLDPOP):
       print(f"❌No encontrado: '{ARCHIVO_WORLDPOP}'")
       return pd.DataFrame()
   columnas_requeridas = ["country", "year", "population", "netMigration"]
   try:
       df = pd.read_csv(ARCHIVO_WORLDPOP, encoding="utf-8", usecols=columnas_requeridas)
   except ValueError as e:
       print(f"❌ Error al leer columnas de WorldPop: {e}")
       return pd.DataFrame()
   ruta = os.path.join(CARPETA_RAW, "raw_csv_worldpop.csv")
   df.to_csv(ruta, index=False, encoding="utf-8")
   print(f"Guardado: {ruta} ({len(df)} registros)\n")
   return df




def extraer_csv_missing():
   print("=" * 55)
   print("[CSV 3] Global Missing Migrants Dataset")
   print("=" * 55)
   if not os.path.exists(ARCHIVO_MISSING):
       print(f"❌No encontrado: '{ARCHIVO_MISSING}'")
       return pd.DataFrame()
   enc = _detectar_encoding(ARCHIVO_MISSING)
   print(f"   Encoding detectado: {enc}")
   columnas_utiles = [
       "Incident Type","Incident year","Reported Month","Region of Origin","Region of Incident",
       "Country of Origin","Number of Dead","Minimum Estimated Number of Missing",
       "Total Number of Dead and Missing","Number of Survivors","Number of Females",
       "Number of Males","Number of Children","Cause of Death","Migration route",
       "UNSD Geographical Grouping",]
   try:
       df_raw = pd.read_csv(ARCHIVO_MISSING, encoding=enc, on_bad_lines="skip")
   except Exception as e:
       print(f"❌ Error al leer Missing Migrants: {e}")
       return pd.DataFrame()
   df = df_raw[[c for c in columnas_utiles if c in df_raw.columns]].copy()
   ruta = os.path.join(CARPETA_RAW, "raw_csv_missing.csv")
   df.to_csv(ruta, index=False, encoding="utf-8")
   print(f"Guardado: {ruta} ({len(df)} registros)\n")
   return df




def extraer_csv_wb_data():
   print("=" * 55)
   print("[CSV 4] World Bank data.csv — indicador SM.POP.NETM")
   print("=" * 55)
   if not os.path.exists(ARCHIVO_WB_DATA):
       print(f"❌No encontrado: '{ARCHIVO_WB_DATA}'")
       return pd.DataFrame()
   df_raw = None
   for enc in ("utf-16", "utf-8-sig", "utf-8", "latin-1"):
       try:
           df_raw = pd.read_csv(ARCHIVO_WB_DATA, encoding=enc)
           print(f"   Encoding detectado: {enc}")
           break
       except (UnicodeDecodeError, UnicodeError):
           continue
   if df_raw is None:
       print("❌ No se pudo leer data.csv con ningun encoding conocido")
       return pd.DataFrame()
   print(f"  Filas totales en data.csv : {len(df_raw)}")
   # FIX: limpiar nombres de columnas por si tienen espacios/caracteres raros del encoding
   df_raw.columns = df_raw.columns.str.strip()
   # buscar columnas de pais y codigo de forma flexible
   col_name = next((c for c in df_raw.columns if "country name" in c.lower()), None)
   col_code = next((c for c in df_raw.columns if "country code" in c.lower()), None)
   col_series = next((c for c in df_raw.columns if "series code" in c.lower()), None)
   if not col_name or not col_code or not col_series:
       print(f"❌ Columnas esperadas no encontradas. Columnas disponibles: {list(df_raw.columns[:10])}")
       return pd.DataFrame()
   df = df_raw[df_raw[col_series] == "SM.POP.NETM"].copy()
   print(f"Filas migracion neta: {len(df)}")
   if df.empty:
       print(" No se encontro SM.POP.NETM en el archivo")
       return pd.DataFrame()
   anios_utiles = [str(a) for a in range(2015, 2023)]
   cols_anio    = [c for c in df.columns if any(a in c for a in anios_utiles)]
   df_final     = df[[col_name, col_code] + cols_anio].copy()
   df_largo     = df_final.melt(
       id_vars=[col_name, col_code],
       var_name="anio_col",
       value_name="migracion_neta")
   df_largo["anio"] = df_largo["anio_col"].str.extract(r"(\d{4})").astype(int)
   df_largo = df_largo.drop(columns=["anio_col"])
   df_largo = df_largo.rename(columns={col_name: "pais", col_code: "iso"})
   df_largo["migracion_neta"] = pd.to_numeric(df_largo["migracion_neta"], errors="coerce")
   df_largo = df_largo.dropna(subset=["migracion_neta"])
   df_largo["migracion_neta"] = df_largo["migracion_neta"].round().astype(int)
   ruta = os.path.join(CARPETA_RAW, "raw_csv_wb_data.csv")
   df_largo.to_csv(ruta, index=False, encoding="utf-8")
   print(f"Guardado: {ruta} ({len(df_largo)} registros)\n")
   return df_largo




def extraer_csv_inegi():
   print("=" * 55)
   print("[CSV 5] INEGI ENADID 2023 TMIGRANTE")
   print("=" * 55)
   if not os.path.exists(ARCHIVO_INEGI):
       print(f"❌ No encontrado: '{ARCHIVO_INEGI}'")
       return pd.DataFrame()
   df = pd.read_csv(ARCHIVO_INEGI, encoding="latin-1")
   print(f"  Filas crudas : {len(df)}")
   columnas_utiles = ["p4_4", "p4_5c", "p4_6", "p4_7c", "p4_8","p4_9", "p4_9c", "p4_10_2",
       "cond_resid", "doc_mig", "ent", "tam_loc","tpo_mig", "fac_hog",]
   df = df[[c for c in columnas_utiles if c in df.columns]].copy()
   mapa_sexo = {1: "Male", 2: "Female"}
   if "p4_6" in df.columns:
       df["sex"] = df["p4_6"].map(mapa_sexo).fillna("Other")
   mapa_motivo = {1: "Job search", 2:"Family reunification", 3:"Access to education",
                  4: "Political persecution", 5:"Violence or insecurity",
                  6: "Better quality of life", 7:"Access to healthcare",
                  8: "Other", 9:"Not specified",}
   mapa_categoria = {1: "Economic", 2:"Social", 3:"Social", 4:"Political",
                     5: "Security", 6:"Economic", 7:"Social", 8:"Other", 9:"Other",}
   if "p4_9" in df.columns:
       df["motive"] = df["p4_9"].map(mapa_motivo).fillna("Other")
       df["category"]= df["p4_9"].map(mapa_categoria).fillna("Social")
   # decodificar condición de residencia
   mapa_status = {1: "Established", 2: "Returned"}
   if "cond_resid" in df.columns:
       df["status"] = df["cond_resid"].map(mapa_status).fillna("Established")
   # nivel socioeconómico aproximado por tamaño de localidad
   mapa_nivel = {1: "Upper-Middle", 2: "Middle", 3: "Lower-Middle", 4: "Low",}
   if "tam_loc" in df.columns:
       df["socioeconomic_level"] = df["tam_loc"].map(mapa_nivel).fillna("Middle")
   mapa_paises_inegi = {
       101:"Mexico", 201:"Guatemala",202: "Belize", 203: "Honduras",
       204:"El Salvador",205:"Nicaragua",206:"Costa Rica",207:"Panama",
       301:"United States",302:"Canada",303:"Puerto Rico",401:"Cuba",
       403:"Dominican Republic",408:"Haiti",413:"Jamaica",415:"Trinidad and Tobago",
       416: "Barbados",418: "Other Caribbean",419:"Bahamas",424: "Aruba",
       501: "Colombia",502:"Venezuela",503: "Guyana",
       504: "Ecuador",505: "Peru",506: "Bolivia",
       507: "Chile",508: "Argentina",509: "Uruguay",
       510: "Paraguay",511: "Brazil",
       221: "Other Central America",}
   df["origin_country"] = "Mexico"
   if "p4_7c" in df.columns:
       df["destination_country"] = df["p4_7c"].map(mapa_paises_inegi).fillna("Other")
   df = df.rename(columns={"p4_6":"age","p4_8":"year","p4_10_2":"year_return","p4_5c":"origin_country_code","p4_7c":"destination_country_code",})
   ruta = f"{CARPETA_RAW}/raw_csv_inegi.csv"
   df.to_csv(ruta, index=False, encoding="utf-8")
   print(f"Guardado: {ruta} ({len(df)} registros)\n")
   return df




def resumen(resultados: dict):
   print("=" * 55)
   print("Resumen final de la fase 1")
   print("=" * 55)
   for nombre, df in resultados.items():
       estado = f"{len(df):>7} registros" if not df.empty else "sin datos"
       print(f"{nombre:<42}: {estado}")
   print(f"\nCSV crudos guardados en : {CARPETA_RAW}/")




if __name__ == "__main__":
   print("\n🌍Fase 1 la extraccion de datos\n")
   df_api_paises = extraer_api_paises()
   df_api_wb     = extraer_api_worldbank()
   df_api_unhcr  = extraer_api_unhcr()
   df_undesa     = extraer_csv_undesa()
   df_worldpop   = extraer_csv_worldpop()
   df_missing    = extraer_csv_missing()
   df_wb_data    = extraer_csv_wb_data()
   df_inegi      = extraer_csv_inegi()
   resumen({
       "API — REST Countries":       df_api_paises,
       "API — World Bank (neta)":    df_api_wb,
       "API — UNHCR (asilo Mexico)": df_api_unhcr,
       "CSV — UNDESA 2024":          df_undesa,
       "CSV — World Pop Migration":  df_worldpop,
       "CSV — Missing Migrants":     df_missing,
       "CSV — World Bank data.csv":  df_wb_data,
       "CSV — INEGI ENADID 2023":    df_inegi,})
