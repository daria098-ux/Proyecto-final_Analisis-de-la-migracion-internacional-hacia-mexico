"""
Phase 3.5: Clone MySQL data to MongoDB using Stored Procedures.

This script reads every table from the mexico_migration MySQL database by
calling its corresponding bulk-read stored procedure, converts the rows
to MongoDB-compatible dictionaries, and bulk-inserts them into the
mexico_migration_nosql MongoDB database.

Typical usage:
    Run as part of the pipeline (run_all.py) or standalone:
        python phase3.5_mongodb_clone.py
"""

from pymongo import MongoClient
import mysql.connector
from decimal import Decimal

# MySQL connection configuration (targeting port 3306)
mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Politron85",
    database="mexico_migration",
    port=3306
)
print("✔️ Connection to MySQL successful!")

# MongoDB connection setup - targets the mexico_migration_nosql database
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["mexico_migration_nosql"]

# Automation dictionary mapping SQL tables to their respective bulk-read Stored Procedures.
# Each key is the target MongoDB collection name, and each value is the MySQL
# stored procedure that returns all rows for that table.
sp_tablas = {
    "regions": "sp_read_all_regions",
    "countries": "sp_read_all_countries",
    "motive_categories": "sp_read_all_motive_categories",
    "motives": "sp_read_all_motives",
    "periods": "sp_read_all_periods",
    "socioeconomic_levels": "sp_read_all_levels",
    "risks": "sp_read_all_risks",
    "impacts": "sp_read_all_impacts",
    "migrants": "sp_read_all_migrants",
    "migrations": "sp_read_all_migrations",
    "migration_risk": "sp_read_all_migration_risk",
    "migration_impact": "sp_read_all_migration_impact",
    "global_statistics": "sp_read_all_global_stats",
    "audit": "sp_read_all_audit"
}

def convert_records(records):
    """Convert MySQL result rows to MongoDB-compatible dictionaries.

    MongoDB cannot store Python Decimal objects natively, so any Decimal
    value (typically from MySQL DECIMAL columns) is cast to float.
    All other values are passed through unchanged.
    """
    result = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                # Convert Decimal to float so MongoDB can store it without errors
                clean_row[k] = float(v)
            else:
                clean_row[k] = v
        result.append(clean_row)
    return result

def migrate_all():
    """Iterate over every table-SP pair and migrate data from MySQL to MongoDB.

    For each entry in sp_tablas:
      1. Call the stored procedure via the MySQL cursor.
      2. Fetch all rows returned by the SP.
      3. Sanitize data types (Decimal -> float) using convert_records().
      4. Bulk-insert the sanitized rows into the matching MongoDB collection.
    A single table failure does not abort the remaining migrations.
    """

    for table, sp in sp_tablas.items():
        try:
            # Set cursor to dictionary=True to fetch rows as BSON/JSON-ready objects
            cursor = mysql_conn.cursor(dictionary=True)
            cursor.callproc(sp)

            # Retrieve the result set produced by the stored procedure
            records = []
            for result in cursor.stored_results():
                records = result.fetchall()
            cursor.close()

            # Sanitize data types before pushing to NoSQL
            records = convert_records(records)

            if records:
                # Bulk insert all rows into the MongoDB collection named after the table
                db[table].insert_many(records)
                print(f"✅ Table '{table}' successfully migrated.")
            else:
                print(f"⚠️ Table '{table}' is empty, skipping.")

        except Exception as e:
            # Safety net prevents a single table error from crashing the entire process
            print(f"❌ Error migrating table '{table}': {e}")

# Run the complete migration process
migrate_all()

# Gracefully terminate database connection streams
mysql_conn.close()
mongo_client.close()
print("\nDatabase connections closed gracefully.")