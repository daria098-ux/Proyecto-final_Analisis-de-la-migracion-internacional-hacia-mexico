"""
Phase 4: Apply SQL Patches to MySQL

This script reads the Databases/patches.sql file, cleans it (removes
comments), splits it into individual SQL statements, and executes each
one against the mexico_migration database.

It runs automatically as part of the pipeline (run_all.py) AFTER the
data load (fase3.py) and BEFORE the view export (export_views.py).

If you modify patches.sql, just re-run this script — no need to open
MySQL Workbench manually.
"""

import os
import re
import sys

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Missing library 'mysql-connector-python'.")
    print("Install it with:  pip install mysql-connector-python")
    sys.exit(1)


# Configuration — same credentials as the other scripts
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "Politron85",
    "database": "mexico_migration",
    "port":     3306,
}

# Absolute path to the patches.sql file
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))   # Programs/
PROJECT_ROOT  = os.path.dirname(SCRIPT_DIR)                  # raiz del proyecto
PATCHES_FILE  = os.path.join(PROJECT_ROOT, "Databases", "patches.sql")


def leer_sql_limpio(ruta):
    """Read the SQL file and return a list of individual statements.

    Strips line comments (--) and splits by semicolons to produce
    executable SQL statements.
    """
    if not os.path.exists(ruta):
        print(f"Not found: {ruta}")
        return []

    with open(ruta, encoding="utf-8") as f:
        sql = f.read()

    # Strip line comments (everything starting with --)
    sql_limpio = re.sub(r"--[^\n]*", "", sql)

    # Split by semicolons and remove empty statements
    statements = [s.strip() for s in sql_limpio.split(";") if s.strip()]
    return statements


def main():
    print("=" * 60)
    print("APPLYING patches.sql TO MYSQL")
    print("=" * 60)

    if not os.path.exists(PATCHES_FILE):
        print(f"Not found {PATCHES_FILE}")
        print("Verify that Databases/patches.sql exists.")
        sys.exit(1)

    statements = leer_sql_limpio(PATCHES_FILE)
    if not statements:
        print("patches.sql is empty or only has comments.")
        return 0

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print(f"MySQL connection OK  (base = {DB_CONFIG['database']})")
    except Error as e:
        print(f"Could not connect to MySQL: {e}")
        sys.exit(1)

    cursor = conn.cursor()
    n_ok = 0
    n_err = 0

    for i, stmt in enumerate(statements, start=1):
        # Short summary of the statement (first few words)
        resumen = " ".join(stmt.split()[:5])[:60]
        try:
            cursor.execute(stmt)
            # If the query returns rows, print them (useful for the final SELECT)
            if cursor.with_rows:
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description] if cursor.description else []
                if rows:
                    print()
                    print("  Results:")
                    print(f"  {' | '.join(cols)}")
                    print(f"  {'-' * 50}")
                    for row in rows:
                        print(f"  {' | '.join(str(c) for c in row)}")
            print(f"  OK  [{i:>2}] {resumen}")
            n_ok += 1
        except Error as e:
            print(f"  ERR [{i:>2}] {resumen}")
            print(f"        -> {e.msg if hasattr(e, 'msg') else e}")
            n_err += 1

    conn.commit()
    cursor.close()
    conn.close()

    print()
    print("=" * 60)
    print(f"  Statements executed: {n_ok}")
    print(f"  Errors             : {n_err}")
    print("=" * 60)

    if n_err == 0:
        print("\nOK Patches applied successfully.")
        return 0
    else:
        print("\nThere were errors applying patches. Review the messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
