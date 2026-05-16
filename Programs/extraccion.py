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