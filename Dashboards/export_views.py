"""
export_views.py - Export the 6 SQL views from mexico_migration to CSV files.

How to use:
    1. Make sure Phases 1, 2 and 3 have been executed (the DB must be populated).
    2. Adjust DB_CONFIG below with your MySQL password.
    3. Run this script:
         python export_views.py
    4. Six vw_*.csv files will be generated in this same folder.
    5. Then run the dashboard:
         streamlit run dashboard.py

The dashboard reads the CSVs from the same folder where it lives — it does not
need a live MySQL connection. If the database changes, just re-run this export.
"""

import os
import sys
import warnings
import pandas as pd

# Silence pandas warnings about mysql.connector (SQLAlchemy)
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Missing library 'mysql-connector-python'.")
    print("Install it with:  pip install mysql-connector-python")
    sys.exit(1)


# Configuration — adjust your MySQL password
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",
    "database": "mexico_migration",
    "port":     3306,
}

# Views that the dashboard expects, mapped to their CSV file names
VISTAS = {
    "vw_top_motives":              "vw_top_motives.csv",
    "vw_origin_countries":         "vw_origin_countries.csv",
    "vw_international_comparison": "vw_international_comparison.csv",
    "vw_migrant_risks":            "vw_migrant_risks.csv",
    "vw_impacts_on_mexico":        "vw_impacts_on_mexico.csv",
    "vw_demographic_profile":      "vw_demographic_profile.csv",
}

# Output folder = where this script lives (Dashboards/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def conectar():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print(f"MySQL connection OK  (base = {DB_CONFIG['database']})")
        return conn
    except Error as e:
        print(f"Could not connect to MySQL: {e}")
        print("Check that the server is running and the password in DB_CONFIG.")
        sys.exit(1)


def exportar_vista(conn, nombre_vista, archivo_destino):
    """Read a complete SQL view and save it as a CSV file."""
    ruta = os.path.join(BASE_DIR, archivo_destino)
    try:
        df = pd.read_sql(f"SELECT * FROM {nombre_vista}", conn)
        df.to_csv(ruta, index=False, encoding="utf-8")
        return len(df), ruta
    except Exception as e:
        print(f"   Error en {nombre_vista}: {e}")
        return 0, None


def main():
    print("=" * 60)
    print("EXPORTING SQL VIEWS -> CSV")
    print("=" * 60)

    conn = conectar()
    print(f"\nDestination: {BASE_DIR}\n")

    total_filas = 0
    exitosas = 0
    for vista, archivo in VISTAS.items():
        n, ruta = exportar_vista(conn, vista, archivo)
        if ruta is not None:
            print(f"  OK  {archivo:<40} {n:>6} rows")
            total_filas += n
            exitosas += 1
        else:
            print(f"  ERR {archivo:<40}    not exported")

    conn.close()

    print()
    print("=" * 60)
    print(f"  Views exported: {exitosas} / {len(VISTAS)}")
    print(f"  Total rows      : {total_filas}")
    print("=" * 60)

    if exitosas == len(VISTAS):
        print("\nDone. Now you can run:")
        print('     streamlit run dashboard.py')
    else:
        print("\nNot all views were exported.")
        print("Verify that Phases 1, 2 and 3 completed successfully.")


if __name__ == "__main__":
    main()
