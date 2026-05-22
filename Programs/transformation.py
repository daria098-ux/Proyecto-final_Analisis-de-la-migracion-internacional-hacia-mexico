import pandas as pd
import numpy as np
import os

RAW_FOLDER = "data_raw"
CLEAN_FOLDER = "data_clean"
os.makedirs(CLEAN_FOLDER, exist_ok=True)


def save(df, filename):
    path = f"{CLEAN_FOLDER}/{filename}"
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"✔️Saved: {path} ({len(df)} records)")
    return df


def read_raw(filename):
    path = f"{RAW_FOLDER}/{filename}"
    if not os.path.exists(path):
        print(f"Not found: {path}")
        return pd.DataFrame()
    if os.path.getsize(path) == 0:
        print(f"Empty file (API returned no data): {path}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, encoding="utf-8")
        if df.empty or len(df.columns) == 0:
            print(f"File with no useful records: {path}")
            return pd.DataFrame()
        return df
    except pd.errors.EmptyDataError:
        print(f"Empty file or no columns: {path} - skipped")
        return pd.DataFrame()


def clean_countries():
    print("=" * 55)
    print("Cleaning countries from REST Countries API")
    print("=" * 55)
    df = read_raw("raw_api_countries.csv")
    if df.empty:
        return df
    print(f"Raw records: {len(df)}")
    df["iso"] = df["iso"].str.strip().str.upper()
    df["name"] = df["name"].str.strip()
    df["region"] = df["region"].str.strip().fillna("Unknown")
    name_map = {"United States": "United States", "Mexico": "Mexico", "Brazil": "Brazil", "Haiti": "Haiti"}
    df["name"] = df["name"].replace(name_map)
    before = len(df)
    df = df.drop_duplicates(subset=["iso"]).reset_index(drop=True)
    print(f"Duplicates removed: {before - len(df)}")
    print(f"Clean records: {len(df)}")
    return save(df, "clean_countries.csv")


def clean_statistics():
    print("\n" + "=" * 55)
    print("Cleaning global statistics (4 sources)")
    print("=" * 55)
    frames = []
    # World Bank API
    df_wb_api = read_raw("raw_api_worldbank.csv")
    if not df_wb_api.empty:
        df_wb_api["year"] = pd.to_numeric(df_wb_api["year"], errors="coerce")
        df_wb_api["net_migration"] = pd.to_numeric(df_wb_api["net_migration"], errors="coerce")
        df_wb_api = df_wb_api.dropna(subset=["year", "net_migration", "iso"])
        df_wb_api = df_wb_api[df_wb_api["year"] >= 2015]
        df_wb_api["iso"] = df_wb_api["iso"].str.strip().str.upper()
        df_wb_api["total_migrants"] = df_wb_api["net_migration"].abs().astype(int)
        df_wb_api = df_wb_api[["iso", "country", "year", "total_migrants"]].copy()
        df_wb_api["source"] = "WB_API"
        frames.append(df_wb_api)
        print(f"  World Bank API: {len(df_wb_api)} records")
    # World Bank CSV data
    df_wb_csv = read_raw("raw_csv_wb_data.csv")
    if not df_wb_csv.empty:
        df_wb_csv["year"] = pd.to_numeric(df_wb_csv["year"], errors="coerce")
        df_wb_csv["net_migration"] = pd.to_numeric(df_wb_csv["net_migration"], errors="coerce")
        df_wb_csv = df_wb_csv.dropna(subset=["year", "net_migration", "iso"])
        df_wb_csv = df_wb_csv[df_wb_csv["year"] >= 2015]
        df_wb_csv["iso"] = df_wb_csv["iso"].str.strip().str.upper()
        df_wb_csv["total_migrants"] = df_wb_csv["net_migration"].abs().astype(int)
        df_wb_csv = df_wb_csv[["iso", "country", "year", "total_migrants"]].copy()
        df_wb_csv["source"] = "WB_CSV"
        frames.append(df_wb_csv)
        print(f"  World Bank CSV data: {len(df_wb_csv)} records")
    # World Pop Migration CSV
    df_wp = read_raw("raw_csv_worldpop.csv")
    if not df_wp.empty:
        df_wp["year"] = pd.to_numeric(df_wp["year"], errors="coerce")
        df_wp["netMigration"] = pd.to_numeric(df_wp["netMigration"], errors="coerce")
        df_wp = df_wp.dropna(subset=["year", "netMigration", "country"])
        df_wp = df_wp[df_wp["year"] >= 2015]
        df_wp["iso"] = ""
        df_wp["total_migrants"] = df_wp["netMigration"].abs().astype(int)
        df_wp = df_wp.rename(columns={"country": "country", "year": "year"})
        df_wp = df_wp[["iso", "country", "year", "total_migrants"]].copy()
        df_wp["source"] = "WORLDPOP"
        frames.append(df_wp)
        print(f"  World Pop Migration: {len(df_wp)} records")
    # UNDESA 2024 CSV
    df_un = read_raw("raw_csv_undesa.csv")
    if not df_un.empty:
        df_un["Year"] = pd.to_numeric(df_un["Year"], errors="coerce")
        df_un["Total"] = pd.to_numeric(df_un["Total"], errors="coerce")
        df_un = df_un.dropna(subset=["Year", "Total", "Destination"])
        df_un = df_un[df_un["Year"] >= 2015]
        df_un_mx = df_un[df_un["Destination"].str.strip() == "Mexico"].copy()
        df_un_mx["iso"] = ""
        df_un_mx["total_migrants"] = df_un_mx["Total"].abs().astype(int)
        df_un_mx = df_un_mx.rename(columns={"Origin": "country", "Year": "year"})
        df_un_mx = df_un_mx[["iso", "country", "year", "total_migrants"]].copy()
        df_un_mx["source"] = "UNDESA"
        frames.append(df_un_mx)
        print(f"  UNDESA (to Mexico): {len(df_un_mx)} records")
        save(df_un[["Destination", "Origin", "Year", "Total", "Male", "Female"]],
             "clean_undesa_full.csv")
    if not frames:
        print("No statistics data available")
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["year"] = df["year"].astype(int)
    df["country"] = df["country"].str.strip()
    total_year_source = df.groupby(["year", "source"])["total_migrants"].transform("sum")
    df["world_percentage"] = (df["total_migrants"] / total_year_source * 100).round(2)
    before = len(df)
    df = df.drop_duplicates(subset=["iso", "country", "year", "source"]).reset_index(drop=True)
    print(f"\n  Combined total: {len(df)} records")
    print(f"  Duplicates removed: {before - len(df)}")
    return save(df, "clean_statistics.csv")


def clean_unhcr():
    print("\n" + "=" * 55)
    print("Cleaning UNHCR migrant demographics in Mexico")
    print("=" * 55)
    df = read_raw("raw_api_unhcr.csv")
    if df.empty:
        return df
    print(f"  Raw records: {len(df)}")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0).astype(int)
    df = df.dropna(subset=["year", "origin_country"])
    df["origin_country"] = df["origin_country"].str.strip().str.title()
    df["origin_iso"] = df["origin_iso"].str.strip().str.upper()
    df["year"] = df["year"].astype(int)
    num_cols = ["f_0_4", "f_5_11", "f_12_17", "f_18_59", "f_60", "f_total",
                "m_0_4", "m_5_11", "m_12_17", "m_18_59", "m_60", "m_total", "total"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df = df[df["total"] > 0].copy()
    before = len(df)
    df = df.drop_duplicates(subset=["year", "origin_iso"]).reset_index(drop=True)
    print(f"Duplicates removed: {before - len(df)}")
    print(f"Clean records: {len(df)}")
    return save(df, "clean_unhcr.csv")


def clean_inegi():
    print("\n" + "=" * 55)
    print("Cleaning INEGI ENADID 2023 from TMIGRANTE")
    print("=" * 55)
    df = read_raw("raw_csv_inegi.csv")
    if df.empty:
        return df
    print(f"Raw records: {len(df)}")
    sex_map = {1: "Male", 2: "Female"}
    if "sex" in df.columns:
        df["sex"] = df["sex"].astype(str).str.strip()
        sex_map_str = {"1": "Male", "2": "Female"}
        df["sex"] = df["sex"].replace(sex_map_str)
        df["sex"] = df["sex"].where(df["sex"].isin(["Male", "Female", "Other"]), "Other")
    else:
        df["age"] = 28

    def convert_year(x):
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
        df["year"] = df["year"].apply(convert_year)
    df = df[df["year"].between(2015, 2024)].copy()
    df["year"] = df["year"].astype(int)
    df["origin_country"] = "Mexico"
    country_map_inegi = {
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
        df["destination_country"] = (df["destination_country_code"].map(country_map_inegi).fillna("Other"))
    elif "destination_country" not in df.columns:
        df["destination_country"] = "Other"

    # Validate motive
    if "motive" in df.columns:
        df["motive"] = df["motive"].astype(str).str.strip().replace("nan", "Other")

    valid_categories = ["Economic", "Political", "Security", "Social", "Other"]
    if "category" in df.columns:
        df["category"] = df["category"].astype(str).str.strip()
        df["category"] = df["category"].where(df["category"].isin(valid_categories), "Social")

    # Validate status
    valid_statuses = ["In transit", "Established", "Returned", "Deported"]
    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.strip()
        df["status"] = df["status"].where(df["status"].isin(valid_statuses), "Established")

    # Validate socioeconomic level
    valid_levels = ["Low", "Lower-Middle", "Middle", "Upper-Middle", "High"]
    if "socioeconomic_level" in df.columns:
        df["socioeconomic_level"] = df["socioeconomic_level"].astype(str).str.strip()
        df["socioeconomic_level"] = df["socioeconomic_level"].where(df["socioeconomic_level"].isin(valid_levels), "Middle")

    final_cols = ["age", "sex", "origin_country", "destination_country", "motive", "category", "year", "socioeconomic_level", "status"]
    final_cols = [c for c in final_cols if c in df.columns]
    df = df[final_cols].copy()

    before = len(df)
    df = df.dropna(subset=["origin_country", "year"])
    print(f"Nulls removed: {before - len(df)}")
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Duplicates removed: {before - len(df)}")
    print(f"Clean records: {len(df)}")
    return save(df, "clean_inegi.csv")


def clean_missing():
    print("\n" + "=" * 55)
    print("Cleaning Global Missing Migrants Dataset")
    print("=" * 55)
    df = read_raw("raw_csv_missing.csv")
    if df.empty:
        return df
    print(f"  Raw records: {len(df)}")

    df["Incident year"] = pd.to_numeric(df["Incident year"], errors="coerce")

    num_cols = ["Number of Dead", "Total Number of Dead and Missing",
                "Number of Survivors", "Number of Females", "Number of Males", "Number of Children",
                "Minimum Estimated Number of Missing"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df = df[df["Incident year"].between(2014, 2024)].copy()

    text_cols = ["Cause of Death", "Migration route", "Region of Incident", "Country of Origin", "Region of Origin", "UNSD Geographical Grouping"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", "Unknown")

    causes = df["Cause of Death"].dropna().unique()
    real_risks = []
    for cause in causes:
        if cause in ["Unknown", "nan"] or not cause:
            continue
        cause_lower = cause.lower()
        if any(p in cause_lower for p in ["drown", "water", "vehicle", "accident", "exposure", "heat", "hypotherm"]):
            risk_type = "Physical"
        elif any(p in cause_lower for p in ["shoot", "violen", "attack", "murder", "assault"]):
            risk_type = "Physical"
        elif any(p in cause_lower for p in ["detain", "deport", "legal"]):
            risk_type = "Legal"
        elif any(p in cause_lower for p in ["exploit", "labour", "work"]):
            risk_type = "Economic"
        else:
            risk_type = "Physical"
        real_risks.append({"description": cause, "type": risk_type})

    df_risks = pd.DataFrame(real_risks).drop_duplicates(subset=["description"])
    save(df_risks, "clean_risks_missing.csv")
    print(f"Unique causes extracted as risks: {len(df_risks)}")

    before = len(df)
    df = df.dropna(subset=["Incident year"]).drop_duplicates().reset_index(drop=True)
    print(f"Duplicates removed: {before - len(df)}")
    print(f"Clean records: {len(df)}")
    return save(df, "clean_missing.csv")


def generate_catalogs():
    print("\n" + "=" * 55)
    print("Generating static catalogs")
    print("=" * 55)
    save(pd.DataFrame({"year": list(range(2015, 2025))}), "clean_periods.csv")
    save(pd.DataFrame({"description": ["Low", "Lower-Middle", "Middle", "Upper-Middle", "High"]}), "clean_levels.csv")
    save(pd.DataFrame({"name": ["Economic", "Political", "Security", "Social"]}), "clean_categories.csv")

    motives = [
        {"name": "Job search", "category": "Economic"}, {"name": "Better quality of life", "category": "Economic"},
        {"name": "Extreme poverty", "category": "Economic"}, {"name": "Political persecution", "category": "Political"},
        {"name": "Armed conflict", "category": "Political"}, {"name": "Lack of freedoms", "category": "Political"},
        {"name": "Violence or insecurity", "category": "Security"}, {"name": "Organized crime violence", "category": "Security"},
        {"name": "Direct threats", "category": "Security"}, {"name": "Family reunification", "category": "Social"},
        {"name": "Access to education", "category": "Social"}, {"name": "Access to healthcare", "category": "Social"},
        {"name": "Other", "category": "Social"}, {"name": "Not specified", "category": "Social"},
    ]
    save(pd.DataFrame(motives), "clean_motives.csv")

    risks = [
        {"description": "Dangerous border crossings", "type": "Physical"}, {"description": "Dehydration and heat exposure", "type": "Physical"},
        {"description": "Drowning", "type": "Physical"}, {"description": "Immigration detention", "type": "Legal"},
        {"description": "Deportation", "type": "Legal"}, {"description": "Labor exploitation", "type": "Economic"},
        {"description": "Extortion by criminal groups", "type": "Economic"}, {"description": "Discrimination and xenophobia", "type": "Social"},
        {"description": "Family separation", "type": "Social"},
    ]
    save(pd.DataFrame(risks), "clean_risks.csv")

    impacts = [
        {"type": "Social", "description": "Increased demand for healthcare services"},
        {"type": "Social", "description": "Greater cultural diversity in host communities"},
        {"type": "Social", "description": "Pressure on local education systems"},
        {"type": "Economic", "description": "Labor force contribution to productive sectors"},
        {"type": "Economic", "description": "Remittances sent to countries of origin"},
        {"type": "Economic", "description": "Increased housing demand"},
    ]
    save(pd.DataFrame(impacts), "clean_impacts.csv")
    print("Catalogs generated.")


def summary():
    print("\n" + "=" * 55)
    print("PHASE 2 SUMMARY")
    print("=" * 55)
    files = [
        ("clean_countries.csv", "regions, countries"),
        ("clean_statistics.csv", "global_statistics"),
        ("clean_undesa_full.csv", "global_statistics (extra)"),
        ("clean_unhcr.csv", "global_statistics (asylum)"),
        ("clean_inegi.csv", "migrants, migrations"),
        ("clean_missing.csv", "migration_risk"),
        ("clean_risks_missing.csv", "risks (real causes)"),
        ("clean_periods.csv", "periods"),
        ("clean_levels.csv", "socioeconomic_levels"),
        ("clean_categories.csv", "motive_categories"),
        ("clean_motives.csv", "motives"),
        ("clean_risks.csv", "risks (base catalog)"),
        ("clean_impacts.csv", "impacts"),
    ]
    for filename, table in files:
        path = f"{CLEAN_FOLDER}/{filename}"
        if os.path.exists(path):
            n = len(pd.read_csv(path))
            print(f"  {filename:<35} {table:<30}: {n:>6} records")
        else:
            print(f"  {filename:<35} {table:<30}: not generated")
    print(f"\n  Files in: ./{CLEAN_FOLDER}/")


if __name__ == "__main__":
    print("\n🔄 PHASE 2 - TRANSFORMATION AND CLEANING\n")
    clean_countries()
    clean_statistics()
    clean_unhcr()
    clean_inegi()
    clean_missing()
    generate_catalogs()
    summary()