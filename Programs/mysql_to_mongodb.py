import pandas as pd
from pymongo import MongoClient
import mysql.connector


# Configuración con el puerto correcto según tu imagen
mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="", # Pon tu contraseña
    database="mexico_migration",
    port=3306
)

print("¡Conexión exitosa!")

# Conexión con MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["mexico_migration_nosql"]

#Tablas
tablas = [
    "regions", "countries", "motive_categories", "motives",
    "periods", "socioeconomic_levels", "risks", "impacts",
    "migrants", "migrations", "migration_risk",
    "migration_impact", "global_statistics", "audit"
]


def migrar_todo():
    for tabla in tablas:
        try:
            query = f"SELECT * FROM {tabla}"
            df = pd.read_sql(query, mysql_conn)
            df = df.where(pd.notnull(df), None) # Convertir valores vacios a None, para que en Mongo se guarde como Null
            registros = df.to_dict(orient='records')

            if registros:
                # Insertar en MongoDB
                db[tabla].insert_many(registros)
                print(f"✅ Tabla '{tabla}' migrada con éxito.")
            else:
                print(f"⚠️ Tabla '{tabla}' está vacía, se saltó.")

        except Exception as e:
            print(f"❌ Error migrando {tabla}: {e}")

migrar_todo()