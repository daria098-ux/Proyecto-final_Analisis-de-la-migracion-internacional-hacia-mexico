from pymongo import MongoClient
import mysql.connector
from decimal import Decimal
# Configuración con el puerto correcto según tu imagen
mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="", #contraseña
    database="mexico_migration2",
    port=3307 #modifica a tu puerto
)
print("¡Conexión exitosa!")

# Conexión con MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["mexico_migration_nosql2"]

# Stored procedures de lectura masiva por tabla
sp_tablas = {
    "regions":"sp_read_all_regions",
    "countries":"sp_read_all_countries",
    "motive_categories": "sp_read_all_motive_categories",
    "motives":"sp_read_all_motives",
    "periods": "sp_read_all_periods",
    "socioeconomic_levels": "sp_read_all_levels",
    "risks":"sp_read_all_risks",
    "impacts":"sp_read_all_impacts",
    "migrants":"sp_read_all_migrants",
    "migrations":"sp_read_all_migrations",
    "migration_risk":"sp_read_all_migration_risk",
    "migration_impact":"sp_read_all_migration_impact",
    "global_statistics":"sp_read_all_global_stats",
    "audit":"sp_read_all_audit",}

def convertir_registros(registros):
     #
    resultado = []
    for fila in registros:
        fila_limpia = {}
        for k, v in fila.items():
            if isinstance(v, Decimal):
                fila_limpia[k] = float(v)
            else:
                fila_limpia[k] = v
        resultado.append(fila_limpia)
    return resultado

def migrar_todo():
    for tabla, sp in sp_tablas.items():
        try:
            cursor = mysql_conn.cursor(dictionary=True)
            cursor.callproc(sp)

            registros = []
            for resultado in cursor.stored_results():
                registros = resultado.fetchall()
            cursor.close()

            # Conveirte los decimales a float para pasarlo a MongoDB
            registros = convertir_registros(registros)

            if registros:
                db[tabla].insert_many(registros)
                print(f"✅ Tabla '{tabla}' migrada con éxito.")
            else:
                print(f"⚠️ Tabla '{tabla}' está vacía, se saltó.")

        except Exception as e:
            print(f"❌ Error migrando {tabla}: {e}")

migrar_todo()

mysql_conn.close()
mongo_client.close()
print("\nConexiones cerradas.")