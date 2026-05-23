from pymongo import MongoClient
import mysql.connector
from decimal import Decimal

# MySQL connection configuration (targeting port 3307)
mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  # Password
    database="mexico_migration",
    port=3307  # Target port
)
print("✔️ Connection to MySQL successful!")

# MongoDB connection setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["mexico_migration_nosql"]

# Automation dictionary mapping SQL tables to their respective bulk-read Stored Procedures
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
    result = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                clean_row[k] = float(v)
            else:
                clean_row[k] = v
        result.append(clean_row)
    return result

def migrate_all():

    for table, sp in sp_tablas.items():
        try:
            # Set cursor to dictionary=True to fetch rows as BSON/JSON-ready objects
            cursor = mysql_conn.cursor(dictionary=True)
            cursor.callproc(sp)

            records = []
            for result in cursor.stored_results():
                records = result.fetchall()
            cursor.close()

            # Sanitize data types before pushing to NoSQL
            records = convert_records(records)

            if records:
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