import pandas as pd
import numpy as np
import os
CARPETA_RAW= "data_raw"
CARPETA_CLEAN= "data_clean"
os.makedirs(CARPETA_CLEAN, exist_ok=True)
def guardar(df, nombre_archivo):
    ruta = f"{CARPETA_CLEAN}/{nombre_archivo}"
    df.to_csv(ruta,index=False,encoding="utf-8")
    print(f"✔️Guardado:{ruta} ({len(df)} registros)")
    return df
def leer_raw(nombre):
    ruta = f"{CARPETA_RAW}/{nombre}"
    if not os.path.exists(ruta):
        print(f"No encontrado: {ruta}")
        return pd.DataFrame()
    if os.path.getsize(ruta) == 0:
        print(f"Archivo vacío (API no devolvió datos): {ruta}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(ruta, encoding="utf-8")
        if df.empty or len(df.columns) == 0:
            print(f" Archivo sin registros útiles: {ruta}")
            return pd.DataFrame()
        return df
    except pd.errors.EmptyDataError:
        print(f"Archivo vacío o sin columnas: {ruta}  se omite")
        return pd.DataFrame()
def limpiar_paises():
    print("=" * 55)
    print("Limpiando países REST Countries API")
    print("=" * 55)
    df = leer_raw("raw_api_paises.csv")
    if df.empty:
        return df
    print(f"Registros crudos: {len(df)}")
    df["iso"]    = df["iso"].str.strip().str.upper()
    df["nombre"] = df["nombre"].str.strip()
    df["region"] = df["region"].str.strip().fillna("Unknown")
    mapa_nombres = {"United States":"United States","Mexico":"Mexico","Brazil":"Brazil","Haiti": "Haiti",}
    df["nombre"] = df["nombre"].replace(mapa_nombres)
    antes = len(df)
    df = df.drop_duplicates(subset=["iso"]).reset_index(drop=True)
    print(f"Duplicados eliminados:{antes - len(df)}")
    print(f"Registros limpios:{len(df)}")
    return guardar(df,"clean_paises.csv")
def limpiar_estadisticas():
    print("\n" + "=" * 55)
    print("Limpiando estadísticas globales (4 fuentes)")
    print("=" * 55)
    frames = []
    # api world bank
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
        print(f"  API World Bank: {len(df_wb_api)} registros")
    # CSV World Bank data
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
        print(f"  CSV World Bank data  : {len(df_wb_csv)} registros")
    # CSV World Pop Migration
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
        print(f"  CSV World Pop Mig: {len(df_wp)} registros")
    # CSV UNDESA 2024
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
        print(f"  CSV UNDESA (a México): {len(df_un_mx)} registros")
        guardar(df_un[["Destination", "Origin", "Year", "Total", "Male", "Female"]],
                "clean_undesa_completo.csv")
    if not frames:
        print("Sin datos de estadísticas")
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["anio"] = df["anio"].astype(int)
    df["pais"] = df["pais"].str.strip()
    total_anio_fuente = df.groupby(["anio", "fuente"])["total_migrantes"].transform("sum")
    df["world_percentage"] = (df["total_migrantes"] / total_anio_fuente * 100).round(2)
    antes = len(df)
    df = df.drop_duplicates(subset=["iso", "pais", "anio", "fuente"]).reset_index(drop=True)
    print(f"\n Total combinado: {len(df)} registros")
    print(f"  Duplicados eliminados: {antes - len(df)}")
    return guardar(df, "clean_estadisticas.csv")
def limpiar_unhcr():
    print("\n" + "=" * 55)
    print("Limpiando UNHCR demografía migrantes en México")
    print("=" * 55)
    df = leer_raw("raw_api_unhcr.csv")
    if df.empty:
        return df
    print(f"  Registros crudos: {len(df)}")
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
    print(f"Duplicados eliminados:{antes - len(df)}")
    print(f"Registros limpios:{len(df)}")
    return guardar(df,"clean_unhcr.csv")

def limpiar_inegi():
    print("\n" + "=" * 55)
    print("Limpiando INEGI ENADID 2023 de TMIGRANTE")
    print("=" * 55)
    df = leer_raw("raw_csv_inegi.csv")
    if df.empty:
        return df
    print(f"Registros crudos:{len(df)}")
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

    # validar motivo
    if "motive" in df.columns:
        df["motive"] = df["motive"].astype(str).str.strip().replace("nan", "Other")

    categorias_validas = ["Economic", "Political", "Security", "Social", "Other"]
    if "category" in df.columns:
        df["category"] = df["category"].astype(str).str.strip()
        df["category"] = df["category"].where(df["category"].isin(categorias_validas), "Social")

    # validar status
    status_validos = ["In transit", "Established", "Returned", "Deported"]
    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.strip()
        df["status"] = df["status"].where(df["status"].isin(status_validos), "Established")

    # validar nivel socioeconomico
    niveles_validos = ["Low", "Lower-Middle", "Middle", "Upper-Middle", "High"]
    if "socioeconomic_level" in df.columns:
        df["socioeconomic_level"] = df["socioeconomic_level"].astype(str).str.strip()
        df["socioeconomic_level"] = df["socioeconomic_level"].where(df["socioeconomic_level"].isin(niveles_validos), "Middle")

    cols_finales = ["age", "sex", "origin_country", "destination_country", "motive", "category", "year", "socioeconomic_level", "status"]
    cols_finales = [c for c in cols_finales if c in df.columns]
    df = df[cols_finales].copy()

    antes = len(df)
    df = df.dropna(subset=["origin_country", "year"])
    print(f"Nulos eliminados:{antes - len(df)}")
    antes = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Duplicados eliminados:{antes - len(df)}")
    print(f"Registros limpios:{len(df)}")
    return guardar(df, "clean_inegi.csv")

def limpiar_missing():
    print("\n" + "=" * 55)
    print("Limpiando Global Missing Migrants Dataset")
    print("=" * 55)
    df = leer_raw("raw_csv_missing.csv")
    if df.empty:
        return df
    print(f"  Registros crudos:{len(df)}")

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
    print(f"Causas únicas extraídas como riesgos:{len(df_riesgos)}")

    antes = len(df)
    df = df.dropna(subset=["Incident year"]).drop_duplicates().reset_index(drop=True)
    print(f"Duplicados eliminados:{antes - len(df)}")
    print(f"Registros limpios:{len(df)}")
    return guardar(df, "clean_missing.csv")

def generar_catalogos():
    print("\n" + "=" * 55)
    print("Generando catálogos estáticos")
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
    print("Catálogos generados.")

def resumen():
    print("\n" + "=" * 55)
    print("RESUMEN de la FASE 2")
    print("=" * 55)
    archivos = [
        ("clean_paises.csv", "regions, countries"),
        ("clean_estadisticas.csv", "global_statistics"),
        ("clean_undesa_completo.csv", "global_statistics (extra)"),
        ("clean_unhcr.csv", "global_statistics (asilo)"),
        ("clean_inegi.csv", "migrants, migrations"),
        ("clean_missing.csv", "migration_risk"),
        ("clean_riesgos_missing.csv", "risks (causas reales)"),
        ("clean_periodos.csv", "periods"),
        ("clean_niveles.csv", "socioeconomic_levels"),
        ("clean_categorias.csv", "motive_categories"),
        ("clean_motivos.csv", "motives"),
        ("clean_riesgos.csv", "risks (catálogo base)"),
        ("clean_impactos.csv", "impacts"),
    ]
    for archivo, tabla in archivos:
        ruta = f"{CARPETA_CLEAN}/{archivo}"
        if os.path.exists(ruta):
            n = len(pd.read_csv(ruta))
            print(f"  {archivo:<35} {tabla:<30}: {n:>6} registros")
        else:
            print(f"  {archivo:<35} {tabla:<30}: no generado")
    print(f"\n  Archivos en : ./{CARPETA_CLEAN}/")

if __name__ == "__main__":
    print("\n🔄FASE 2 TRANSFORMACIÓN Y LIMPIEZA\n")
    limpiar_paises()
    limpiar_estadisticas()
    limpiar_unhcr()
    limpiar_inegi()
    limpiar_missing()
    generar_catalogos()
    resumen()