import requests
import pandas as pd
import os


BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RAW_FOLDER = os.path.join(BASE_DIR, "data_raw")
os.makedirs(RAW_FOLDER, exist_ok=True)


UNDESA_FILE   = os.path.join(BASE_DIR, "cleaned_undesa_2024_ims_stock_by_sex_destination_and_origin_1990-2024.csv")
WORLDPOP_FILE = os.path.join(BASE_DIR, "world_pop_mig_186_countries.csv")
MISSING_FILE  = os.path.join(BASE_DIR, "Global_Missing_Migrants_Dataset.csv")
WB_DATA_FILE  = os.path.join(BASE_DIR, "data.csv")
INEGI_FILE    = os.path.join(BASE_DIR, "TMIGRANTE.csv")


MAX_UNHCR_PAGES = 50




def _detect_encoding(path, candidates=("utf-16", "utf-8-sig", "utf-8", "latin-1")):
   for enc in candidates:
       try:
           with open(path, encoding=enc) as f:
               f.read(2048)
           return enc
       except (UnicodeDecodeError, UnicodeError):
           continue
   return "latin-1"




# SECTION: APIs


def extract_countries_api():
   print("=" * 55)
   print("[API 1] REST Countries - country information")
   print("=" * 55)
   country_codes = [
       "MX", "US", "GT", "HN", "SV", "VE", "CO",
       "CU", "HT", "NI", "EC", "PE", "BO", "BR",
       "AR", "DO", "JM", "PY", "UY", "PA",]
   records = []
   for iso in country_codes:
       url = f"https://restcountries.com/v3.1/alpha/{iso}"
       try:
           resp = requests.get(url, timeout=10)
           if resp.status_code == 200:
               info = resp.json()[0]
               records.append({
                   "iso":    iso,
                   "name": info["name"]["common"],
                   "region": info.get("region", "Unknown"),})
               print(f"✔️{iso} — {info['name']['common']}")
           else:
               print(f"❌{iso} — HTTP {resp.status_code}")
       except Exception as e:
           print(f"❌{iso} — Error: {e}")
   df   = pd.DataFrame(records)
   path = os.path.join(RAW_FOLDER, "raw_api_countries.csv")
   df.to_csv(path, index=False, encoding="utf-8")
   print(f"\nSaved: {path} ({len(df)} records)\n")
   return df




def extract_worldbank_api():
   print("=" * 55)
   print("[API 2] World Bank - net migration")
   print("=" * 55)
   country_codes = ["MX", "US", "GT", "HN", "SV", "VE", "CO",
                 "CU", "HT", "NI", "EC", "PE", "BO", "BR",
                 "AR", "DO", "JM", "PY", "UY", "PA",]
   start_year = 2015
   end_year    = 2023
   records   = []
   for iso in country_codes:
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
                       year  = int(item["date"])
                       value = item.get("value")
                       if value is not None and start_year <= year <= end_year:
                           records.append({
                               "iso":            iso,
                               "country":           item["country"]["value"],
                               "year":           year,
                               "net_migration": int(round(float(value))),})
                   print(f"✔️{iso}")
               else:
                   print(f"❌{iso} no data")
           else:
               print(f"❌{iso} HTTP {resp.status_code}")
       except Exception as e:
           print(f"❌{iso} Error: {e}")
   df   = pd.DataFrame(records)
   path = os.path.join(RAW_FOLDER, "raw_api_worldbank.csv")
   df.to_csv(path, index=False, encoding="utf-8")
   print(f"\nSaved: {path} ({len(df)} records)\n")
   return df




def extract_unhcr_api():
   print("=" * 55)
   print("[API 3] UNHCR - migrant demographics in Mexico by country")
   print("=" * 55)
   url = "https://api.unhcr.org/population/v1/demographics/"
   origin_countries = {
       "GTM": "Guatemala",        "HND": "Honduras",           "SLV": "El Salvador",
       "VEN": "Venezuela",        "CUB": "Cuba",               "HTI": "Haiti",
       "NIC": "Nicaragua",        "ECU": "Ecuador",            "COL": "Colombia",
       "PER": "Peru",             "BOL": "Bolivia",            "BRA": "Brazil",
       "ARG": "Argentina",        "DOM": "Dominican Republic", "JAM": "Jamaica",
       "PRY": "Paraguay",         "URY": "Uruguay",            "PAN": "Panama",
       "SYR": "Syria",            "AFG": "Afghanistan",        "CMR": "Cameroon",
       "SOM": "Somalia",          "YEM": "Yemen",              "COD": "Dem. Rep. Congo",
       "ETH": "Ethiopia"}
   records = []
   for iso3, name in origin_countries.items():
       page     = 1
       total_country = 0
       while page <= MAX_UNHCR_PAGES:
           params = {
               "coa":      "MEX",
               "coo":      iso3,
               "yearFrom": 2015,
               "yearTo":   2023,
               "limit":    300,
               "page":     page,}
           try:
               resp = requests.get(url, params=params, timeout=15)
               if resp.status_code != 200:
                   print(f"❌ {iso3} p.{page} HTTP {resp.status_code}")
                   break
               data  = resp.json()
               items = data.get("items", [])
               if not items:
                   break
               for item in items:
                   records.append({
                       "year":           item.get("year"),
                       "origin_country": item.get("coo_name", name),
                       "origin_iso":     item.get("coo",      iso3),
                       "destination_country": item.get("coa_name", "Mexico"),
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
               total_country += len(items)
               max_pages = data.get("maxPages", 1)
               if page >= max_pages:
                   break
               page += 1
           except Exception as e:
               print(f"❌ {iso3} p.{page} error: {e}")
               break
       if total_country > 0:
           print(f"✔️{name:<22} - {total_country} records")
       else:
           print(f"{name:<22} no data")
   df   = pd.DataFrame(records)
   path = os.path.join(RAW_FOLDER, "raw_api_unhcr.csv")
   df.to_csv(path, index=False, encoding="utf-8")
   print(f"\nSaved: {path} ({len(df)} records)\n")
   return df