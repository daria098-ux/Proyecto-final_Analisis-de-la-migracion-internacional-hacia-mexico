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