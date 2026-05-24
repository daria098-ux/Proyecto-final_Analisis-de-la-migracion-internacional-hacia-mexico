"""
Phase 2: Data Transformation & Cleaning

This script takes the raw CSVs produced by Phase 1 (phase1_extraction.py) from
the data_raw/ folder, cleans and normalizes them, and writes the cleaned
CSVs to data_clean/ for Phase 3 (phase3_loading.py) to load into MySQL.

Typical usage:
    Run as part of the pipeline (run_all.py) or standalone:
        python phase2_transformation.py
"""

import pandas as pd
import numpy as np
import os

# Absolute paths based on the project root directory
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))   # Programs/
PROJECT_ROOT  = os.path.dirname(SCRIPT_DIR)                  # project root
CARPETA_RAW   = os.path.join(PROJECT_ROOT, "data_raw")       # Phase 1 CSVs (input)
CARPETA_CLEAN = os.path.join(PROJECT_ROOT, "data_clean")     # Cleaned CSVs (output)
os.makedirs(CARPETA_CLEAN, exist_ok=True)
def guardar(df, nombre_archivo):
    """Save a DataFrame to the data_clean/ folder as UTF-8 CSV and print confirmation."""
    ruta = f"{CARPETA_CLEAN}/{nombre_archivo}"
    df.to_csv(ruta,index=False,encoding="utf-8")
    print(f"✔️Saved:{ruta} ({len(df)} records)")
    return df
def leer_raw(nombre):
    """Read a raw CSV from data_raw/. Returns an empty DataFrame if the file
    is missing, empty, or has no useful columns."""
    ruta = f"{CARPETA_RAW}/{nombre}"
    if not os.path.exists(ruta):
        print(f"Not found: {ruta}")
        return pd.DataFrame()
    if os.path.getsize(ruta) == 0:
        print(f"Empty file (API returned no data): {ruta}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(ruta, encoding="utf-8")
        if df.empty or len(df.columns) == 0:
            print(f" File without useful records: {ruta}")
            return pd.DataFrame()
        return df
    except pd.errors.EmptyDataError:
        print(f"Empty file or no columns: {ruta}  skipped")
        return pd.DataFrame()
def limpiar_paises():
    """Clean country data from the REST Countries API.

    Normalizes ISO codes and names, removes duplicates, and saves to
    clean_paises.csv. Used to populate the 'countries' and 'regions' tables.
    """
    print("=" * 55)
    print("Cleaning countries from REST Countries API")
    print("=" * 55)
    df = leer_raw("raw_api_paises.csv")
    if df.empty:
        return df
    print(f"Raw records: {len(df)}")
    df["iso"]    = df["iso"].str.strip().str.upper()
    df["nombre"] = df["nombre"].str.strip()
    df["region"] = df["region"].str.strip().fillna("Unknown")
    mapa_nombres = {"United States":"United States","Mexico":"Mexico","Brazil":"Brazil","Haiti": "Haiti",}
    df["nombre"] = df["nombre"].replace(mapa_nombres)
    antes = len(df)
    df = df.drop_duplicates(subset=["iso"]).reset_index(drop=True)
    print(f"Duplicates removed:{antes - len(df)}")
    print(f"Clean records:{len(df)}")
    return guardar(df,"clean_paises.csv")
def limpiar_estadisticas():
    """Clean and merge global statistics from 4 sources:

    1. World Bank API (net migration by country/year)
    2. World Bank CSV (SM.POP.NETM indicator, wide format)
    3. World Pop Migration (186 countries)
    4. UNDESA 2024 (international migrant stock to Mexico)

    Normalizes all sources into a common schema (iso, pais, anio,
    total_migrantes, world_percentage, fuente) and saves the combined
    dataset to clean_estadisticas.csv.
    """
    print("\n" + "=" * 55)
    print("Cleaning global statistics (4 sources)")
    print("=" * 55)
    frames = []
    # Source 1: World Bank API (net migration by country and year)
    df_wb_api = leer_raw("raw_api_worldbank.csv")
    if not df_wb_api.empty:
        df_wb_api["anio"]= pd.to_numeric(df_wb_api["anio"], errors="coerce")
        df_wb_api["migracion_neta"] = pd.to_numeric(df_wb_api["migracion_neta"], errors="coerce")
        df_wb_api = df_wb_api.dropna(subset=["anio", "migracion_neta", "iso"])
        df_wb_api = df_wb_api[df_wb_api["anio"] >= 2015]
        df_wb_api["iso"] = df_wb_api["iso"].str.strip().str.upper()
        df_wb_api["total_migrantes"] = df_wb_api["migracion_neta"].abs().astype(int)
        df_wb_api = df_wb_api[["iso","pais", "anio", "total_migrantes"]].copy()
        df_wb_api["fuente"] = "WB_API"
        frames.append(df_wb_api)
        print(f"  API World Bank: {len(df_wb_api)} records")
    # Source 2: World Bank CSV data (SM.POP.NETM indicator in wide format)
    df_wb_csv = leer_raw("raw_csv_wb_data.csv")
    if not df_wb_csv.empty:
        df_wb_csv["anio"]= pd.to_numeric(df_wb_csv["anio"], errors="coerce")
        df_wb_csv["migracion_neta"] = pd.to_numeric(df_wb_csv["migracion_neta"], errors="coerce")
        df_wb_csv = df_wb_csv.dropna(subset=["anio", "migracion_neta", "iso"])
        df_wb_csv = df_wb_csv[df_wb_csv["anio"] >= 2015]
        df_wb_csv["iso"]= df_wb_csv["iso"].str.strip().str.upper()
        df_wb_csv["total_migrantes"] = df_wb_csv["migracion_neta"].abs().astype(int)
        df_wb_csv = df_wb_csv[["iso", "pais", "anio", "total_migrantes"]].copy()
        df_wb_csv["fuente"] = "WB_CSV"
        frames.append(df_wb_csv)
        print(f"  CSV World Bank data  : {len(df_wb_csv)} records")
    # Source 3: World Pop Migration CSV (186 countries)
    df_wp = leer_raw("raw_csv_worldpop.csv")
    if not df_wp.empty:
        df_wp["year"] = pd.to_numeric(df_wp["year"], errors="coerce")
        df_wp["netMigration"] = pd.to_numeric(df_wp["netMigration"], errors="coerce")
        df_wp = df_wp.dropna(subset=["year", "netMigration", "country"])
        df_wp = df_wp[df_wp["year"] >= 2015]
        df_wp["iso"] = ""
        df_wp["total_migrantes"] = df_wp["netMigration"].abs().astype(int)
        df_wp = df_wp.rename(columns={"country": "pais", "year": "anio"})
        df_wp = df_wp[["iso", "pais", "anio", "total_migrantes"]].copy()
        df_wp["fuente"] = "WORLDPOP"
        frames.append(df_wp)
        print(f"  CSV World Pop Mig: {len(df_wp)} records")
    # Source 4: UNDESA 2024 (international migrant stock to Mexico)
    df_un = leer_raw("raw_csv_undesa.csv")
    if not df_un.empty:
        df_un["Year"]  = pd.to_numeric(df_un["Year"],  errors="coerce")
        df_un["Total"] = pd.to_numeric(df_un["Total"], errors="coerce")
        df_un = df_un.dropna(subset=["Year", "Total", "Destination"])
        df_un = df_un[df_un["Year"] >= 2015]
        df_un_mx = df_un[df_un["Destination"].str.strip() == "Mexico"].copy()
        df_un_mx["iso"]= ""
        df_un_mx["total_migrantes"] = df_un_mx["Total"].abs().astype(int)
        df_un_mx = df_un_mx.rename(columns={"Origin": "pais", "Year": "anio"})
        df_un_mx = df_un_mx[["iso", "pais", "anio", "total_migrantes"]].copy()
        df_un_mx["fuente"] = "UNDESA"
        frames.append(df_un_mx)
        print(f"  CSV UNDESA (to Mexico): {len(df_un_mx)} records")
        guardar(df_un[["Destination", "Origin", "Year", "Total", "Male", "Female"]],
                "clean_undesa_completo.csv")
    if not frames:
        print("No statistics data")
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["anio"] = df["anio"].astype(int)
    df["pais"] = df["pais"].str.strip()
    total_anio_fuente = df.groupby(["anio", "fuente"])["total_migrantes"].transform("sum")
    df["world_percentage"] = (df["total_migrantes"] / total_anio_fuente * 100).round(2)
    antes = len(df)
    df = df.drop_duplicates(subset=["iso", "pais", "anio", "fuente"]).reset_index(drop=True)
    print(f"\n Combined total: {len(df)} records")
    print(f"  Duplicates removed: {antes - len(df)}")
    return guardar(df, "clean_estadisticas.csv")
def limpiar_unhcr():
    """Clean UNHCR asylum-seeker demographics data.

    Filters for records with total > 0, removes duplicates, normalizes
    numeric columns, and saves to clean_unhcr.csv.
    """
    print("\n" + "=" * 55)
    print("Cleaning UNHCR migrant demographics in Mexico")
    print("=" * 55)
    df = leer_raw("raw_api_unhcr.csv")
    if df.empty:
        return df
    print(f"  Raw records: {len(df)}")
    df["anio"]= pd.to_numeric(df["anio"],errors="coerce")
    df["total"]= pd.to_numeric(df["total"],errors="coerce").fillna(0).astype(int)
    df = df.dropna(subset=["anio", "pais_origen"])
    df["pais_origen"]= df["pais_origen"].str.strip().str.title()
    df["iso_origen"]= df["iso_origen"].str.strip().str.upper()
    df["anio"]= df["anio"].astype(int)
    cols_num = ["f_0_4","f_5_11","f_12_17","f_18_59","f_60","f_total","m_0_4","m_5_11","m_12_17","m_18_59","m_60","m_total","total"]
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df = df[df["total"] > 0].copy()
    antes = len(df)
    df = df.drop_duplicates(subset=["anio","iso_origen"]).reset_index(drop=True)
    print(f"Duplicates removed:{antes - len(df)}")
    print(f"Clean records:{len(df)}")
    return guardar(df,"clean_unhcr.csv")

def limpiar_inegi():
    """Clean INEGI ENADID 2023 migrant survey data.

    Validates and normalizes sex, motive, category, status, and
    socioeconomic_level fields. Converts 2-digit years and filters for
    2015-2024. Maps country codes to names. Saves to clean_inegi.csv.
    """
    print("\n" + "=" * 55)
    print("Cleaning INEGI ENADID 2023 from TMIGRANTE")
    print("=" * 55)
    df = leer_raw("raw_csv_inegi.csv")
    if df.empty:
        return df
    print(f"Raw records:{len(df)}")
    mapa_sexo = {1: "Male", 2: "Female"}
    if "sex" in df.columns:
        df["sex"] = df["sex"].astype(str).str.strip()
        mapa_sexo_num = {"1": "Male", "2": "Female"}
        df["sex"] = df["sex"].replace(mapa_sexo_num)
        df["sex"] = df["sex"].where(df["sex"].isin(["Male", "Female", "Other"]), "Other")
    else:
        df["age"] = 28

    def convertir_anio(x):
        try:
            x = int(x)
        except (ValueError, TypeError):
            return None
        if x in [999, 99, 0]:
            return None
        if x <= 24:
            return 2000 + x
        elif x <= 98:
            return 1900 + x
        return None

    if "year" in df.columns:
        df["year"] = df["year"].apply(convertir_anio)
    df = df[df["year"].between(2015, 2024)].copy()
    df["year"] = df["year"].astype(int)
    df["origin_country"] = "Mexico"
    mapa_paises_inegi = {
        101: "Mexico", 201: "Guatemala", 202: "Belize", 203: "Honduras",
        204: "El Salvador", 205: "Nicaragua", 206: "Costa Rica", 207: "Panama",
        301: "United States", 302: "Canada", 303: "Puerto Rico", 401: "Cuba",
        403: "Dominican Republic", 408: "Haiti", 413: "Jamaica", 415: "Trinidad and Tobago",
        416: "Barbados", 418: "Other Caribbean", 419: "Bahamas", 424: "Aruba",
        501: "Colombia", 502: "Venezuela", 503: "Guyana", 504: "Ecuador",
        505: "Peru", 506: "Bolivia", 507: "Chile", 508: "Argentina",
        509: "Uruguay", 510: "Paraguay", 511: "Brazil", 221: "Other Central America",
    }
    if "destination_country_code" in df.columns:
        df["destination_country"] = (df["destination_country_code"].map(mapa_paises_inegi).fillna("Other"))
    elif "destination_country" not in df.columns:
        df["destination_country"] = "Other"

    # validate motive field
    if "motive" in df.columns:
        df["motive"] = df["motive"].astype(str).str.strip().replace("nan", "Other")

    categorias_validas = ["Economic", "Political", "Security", "Social", "Other"]
    if "category" in df.columns:
        df["category"] = df["category"].astype(str).str.strip()
        df["category"] = df["category"].where(df["category"].isin(categorias_validas), "Social")

    # validate migration status
    status_validos = ["In transit", "Established", "Returned", "Deported"]
    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.strip()
        df["status"] = df["status"].where(df["status"].isin(status_validos), "Established")

    # validate socioeconomic level
    niveles_validos = ["Low", "Lower-Middle", "Middle", "Upper-Middle", "High"]
    if "socioeconomic_level" in df.columns:
        df["socioeconomic_level"] = df["socioeconomic_level"].astype(str).str.strip()
        df["socioeconomic_level"] = df["socioeconomic_level"].where(df["socioeconomic_level"].isin(niveles_validos), "Middle")

    cols_finales = ["age", "sex", "origin_country", "destination_country", "motive", "category", "year", "socioeconomic_level", "status"]
    cols_finales = [c for c in cols_finales if c in df.columns]
    df = df[cols_finales].copy()

    antes = len(df)
    df = df.dropna(subset=["origin_country", "year"])
    print(f"Nulls removed:{antes - len(df)}")
    antes = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Duplicates removed:{antes - len(df)}")
    print(f"Clean records:{len(df)}")
    return guardar(df, "clean_inegi.csv")

def limpiar_missing():
    """Clean the Global Missing Migrants Dataset.

    Filters for 2014-2024 incidents, normalizes numeric and text columns,
    and extracts unique causes of death as risk entries. Saves two files:
    clean_missing.csv (incident data) and clean_riesgos_missing.csv (unique
    causes mapped to risk types: Physical, Legal, Economic, Social).
    """
    print("\n" + "=" * 55)
    print("Cleaning Global Missing Migrants Dataset")
    print("=" * 55)
    df = leer_raw("raw_csv_missing.csv")
    if df.empty:
        return df
    print(f"  Raw records:{len(df)}")

    df["Incident year"] = pd.to_numeric(df["Incident year"], errors="coerce")

    cols_num = ["Number of Dead", "Total Number of Dead and Missing",
                "Number of Survivors", "Number of Females", "Number of Males", "Number of Children",
                "Minimum Estimated Number of Missing"]
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df = df[df["Incident year"].between(2014, 2024)].copy()

    cols_texto = ["Cause of Death", "Migration route", "Region of Incident", "Country of Origin", "Region of Origin", "UNSD Geographical Grouping"]
    for col in cols_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", "Unknown")

    causas = df["Cause of Death"].dropna().unique()
    riesgos_reales = []
    for causa in causas:
        if causa in ["Unknown", "nan"] or not causa:
            continue
        causa_lower = causa.lower()
        if any(p in causa_lower for p in ["drown", "water", "vehicle", "accident", "exposure", "heat", "hypotherm"]):
            tipo = "Physical"
        elif any(p in causa_lower for p in ["shoot", "violen", "attack", "murder", "assault"]):
            tipo = "Physical"
        elif any(p in causa_lower for p in ["detain", "deport", "legal"]):
            tipo = "Legal"
        elif any(p in causa_lower for p in ["exploit", "labour", "work"]):
            tipo = "Economic"
        else:
            tipo = "Physical"
        riesgos_reales.append({"description": causa, "type": tipo})

    df_riesgos = pd.DataFrame(riesgos_reales).drop_duplicates(subset=["description"])
    guardar(df_riesgos, "clean_riesgos_missing.csv")
    print(f"Unique causes extracted as risks:{len(df_riesgos)}")

    antes = len(df)
    df = df.dropna(subset=["Incident year"]).drop_duplicates().reset_index(drop=True)
    print(f"Duplicates removed:{antes - len(df)}")
    print(f"Clean records:{len(df)}")
    return guardar(df, "clean_missing.csv")

def generar_catalogos():
    """Generate static reference catalogs that don't come from any API or CSV.

    Creates the following clean CSVs:
    - clean_periodos.csv: Years 2015-2024
    - clean_niveles.csv: 5 socioeconomic levels
    - clean_categorias.csv: 4 motive categories (Economic, Political, Security, Social)
    - clean_motivos.csv: 14 specific motives mapped to their categories
    - clean_riesgos.csv: 9 base risks mapped to types
    - clean_impactos.csv: 6 impacts (Social and Economic types)
    """
    print("\n" + "=" * 55)
    print("Generating static catalogs")
    print("=" * 55)
    guardar(pd.DataFrame({"year": list(range(2015, 2025))}), "clean_periodos.csv")
    guardar(pd.DataFrame({"description": ["Low", "Lower-Middle", "Middle", "Upper-Middle", "High"]}), "clean_niveles.csv")
    guardar(pd.DataFrame({"name": ["Economic", "Political", "Security", "Social"]}), "clean_categorias.csv")

    motivos = [
        {"name": "Job search", "category": "Economic"}, {"name": "Better quality of life", "category": "Economic"},
        {"name": "Extreme poverty", "category": "Economic"}, {"name": "Political persecution", "category": "Political"},
        {"name": "Armed conflict", "category": "Political"}, {"name": "Lack of freedoms", "category": "Political"},
        {"name": "Violence or insecurity", "category": "Security"}, {"name": "Organized crime violence", "category": "Security"},
        {"name": "Direct threats", "category": "Security"}, {"name": "Family reunification", "category": "Social"},
        {"name": "Access to education", "category": "Social"}, {"name": "Access to healthcare", "category": "Social"},
        {"name": "Other", "category": "Social"}, {"name": "Not specified", "category": "Social"},
    ]
    guardar(pd.DataFrame(motivos), "clean_motivos.csv")

    riesgos = [
        {"description": "Dangerous border crossings", "type": "Physical"}, {"description": "Dehydration and heat exposure", "type": "Physical"},
        {"description": "Drowning", "type": "Physical"}, {"description": "Immigration detention", "type": "Legal"},
        {"description": "Deportation", "type": "Legal"}, {"description": "Labor exploitation", "type": "Economic"},
        {"description": "Extortion by criminal groups", "type": "Economic"}, {"description": "Discrimination and xenophobia", "type": "Social"},
        {"description": "Family separation", "type": "Social"},
    ]
    guardar(pd.DataFrame(riesgos), "clean_riesgos.csv")

    impactos = [
        {"type": "Social", "description": "Increased demand for healthcare services"},
        {"type": "Social", "description": "Greater cultural diversity in host communities"},
        {"type": "Social", "description": "Pressure on local education systems"},
        {"type": "Economic", "description": "Labor force contribution to productive sectors"},
        {"type": "Economic", "description": "Remittances sent to countries of origin"},
        {"type": "Economic", "description": "Increased housing demand"},
    ]
    guardar(pd.DataFrame(impactos), "clean_impactos.csv")
    print("Catalogs generated.")

def resumen():
    """Print a summary of all generated clean CSVs with record counts."""
    print("\n" + "=" * 55)
    print("PHASE 2 SUMMARY")
    print("=" * 55)
    archivos = [
        ("clean_paises.csv", "regions, countries"),
        ("clean_estadisticas.csv", "global_statistics"),
        ("clean_undesa_completo.csv", "global_statistics (extra)"),
        ("clean_unhcr.csv", "global_statistics (asylum)"),
        ("clean_inegi.csv", "migrants, migrations"),
        ("clean_missing.csv", "migration_risk"),
        ("clean_riesgos_missing.csv", "risks (real causes)"),
        ("clean_periodos.csv", "periods"),
        ("clean_niveles.csv", "socioeconomic_levels"),
        ("clean_categorias.csv", "motive_categories"),
        ("clean_motivos.csv", "motives"),
        ("clean_riesgos.csv", "risks (base catalog)"),
        ("clean_impactos.csv", "impacts"),
    ]
    for archivo, tabla in archivos:
        ruta = f"{CARPETA_CLEAN}/{archivo}"
        if os.path.exists(ruta):
            n = len(pd.read_csv(ruta))
            print(f"  {archivo:<35} {tabla:<30}: {n:>6} records")
        else:
            print(f"  {archivo:<35} {tabla:<30}: not generated")
    print(f"\n  Files in : ./{CARPETA_CLEAN}/")

# =============================================================================
# Main execution: run all cleaning functions and print summary
# =============================================================================
if __name__ == "__main__":
    print("\nPHASE 2: Transformation & Cleaning\n")
    limpiar_paises()
    limpiar_estadisticas()
    limpiar_unhcr()
    limpiar_inegi()
    limpiar_missing()
    generar_catalogos()
    resumen()