import pandas as pd
from pymongo import MongoClient
import mysql.connector


# MySQL configuration
mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="", # Enter your password
    database="mexico_migration",
    port=3306
)

print("Connection successful!")

# MongoDB connection
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["mexico_migration_nosql"]

# Tables to migrate
tables = [
    "regions", "countries", "motive_categories", "motives",
    "periods", "socioeconomic_levels", "risks", "impacts",
    "migrants", "migrations", "migration_risk",
    "migration_impact", "global_statistics", "audit"
]


def migrate_all():
    for table in tables:
        try:
            query = f"SELECT * FROM {table}"
            df = pd.read_sql(query, mysql_conn)
            df = df.where(pd.notnull(df), None)  # Convert empty values to None so MongoDB stores them as Null
            records = df.to_dict(orient='records')

            if records:
                # Insert into MongoDB
                db[table].insert_many(records)
                print(f"✅ Table '{table}' migrated successfully.")
            else:
                print(f"⚠️ Table '{table}' is empty, skipped.")

        except Exception as e:
            print(f"❌ Error migrating {table}: {e}")

migrate_all()