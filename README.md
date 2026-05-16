
# Análisis de la Migración Internacional hacia México
> Proyecto Final Integrador — Programación · Base de Datos · Análisis de Datos
---

## Descripción
 
Sistema ETL completo que extrae, transforma, carga y visualiza datos reales sobre la migración internacional hacia México. El proyecto responde cinco preguntas clave mediante datos de fuentes oficiales (INEGI, ONU, World Bank, UNHCR), una base de datos relacional MySQL normalizada hasta 3FN y dashboards interactivos con Python.
 
### Preguntas que responde el sistema
 
| # | Pregunta |
|---|----------|
| 1 | ¿Cuáles son los principales motivos de migración hacia México? |
| 2 | ¿Qué porcentaje de migrantes recibe México comparado con otros países? |
| 3 | ¿De qué países provienen más migrantes? |
| 4 | ¿Qué riesgos enfrentan los migrantes en México? |
| 5 | ¿Cuál es el impacto social y económico en México? |
  
---
## Estructura del proyecto
 
```
migracion-mexico/
│
├── fase1_extraccion.py        # ETL — Extract: APIs + CSV locales
├── fase2_transformacion.py    # ETL — Transform: limpieza y estandarización
├── fase3_carga.py             # ETL — Load: inserción a MySQL
├── fase3.5_daseconexion.py    # ETL — clone: Clonacion a MongoDB Compass
├── fase4_dashboards.py        # Visualización: 3 dashboards
│
├── mexico_migration.sql       # Script completo de la base de datos
│
├── data_raw/                  # CSV crudos generados por Fase 1
├── data_clean/                # CSV limpios generados por Fase 2
│
├── datasets/                  # Archivos CSV descargados (fuentes locales)
│   ├── cleaned_undesa_2024_ims_stock_by_sex_destination_and_origin_1990-2024.csv
│   ├── world_pop_mig_186_countries.csv
│   ├── Global_Missing_Migrants_Dataset.csv
│   ├── data.csv
│   └── TMIGRANTE.csv
│
└── README.md
``` 
---
##  Fases del proyecto
### Fase 1 — Extracción `fase1_extraccion.py`
 
Extrae datos de **3 APIs** y **5 archivos CSV** locales y los guarda en `data_raw/`.
 
**APIs:**
 
| API | Endpoint | Datos extraídos |
|-----|----------|----------------|
| REST Countries | `restcountries.com/v3.1/alpha/{iso}` | Nombre, ISO y región de cada país |
| World Bank | `api.worldbank.org` — indicador `SM.POP.NETM` | Migración neta por país y año |
| UNHCR | `api.unhcr.org/population/v1/demographics/` | Demografía de migrantes en México por país de origen |
 
**CSV locales:**
 
| Archivo | Fuente | Tabla destino |
|---------|--------|---------------|
| `cleaned_undesa_2024...csv` | ONU DESA | `global_statistics` |
| `world_pop_mig_186_countries.csv` | Kaggle | `global_statistics` |
| `Global_Missing_Migrants_Dataset.csv` | IOM / Kaggle | `risks`, `migration_risk` |
| `data.csv` | World Bank | `global_statistics` |
| `TMIGRANTE.csv` | INEGI ENADID 2023 | `migrants`, `migrations` |
 
---
 
### Fase 2 — Transformación `fase2_transformacion.py`
 
Lee los CSV de `data_raw/`, los limpia y genera CSV normalizados en `data_clean/`.
 
**Operaciones aplicadas:**
 
- Eliminación de nulos y duplicados
- Estandarización de nombres de países (`"México"` → `"Mexico"`)
- Corrección de codificaciones INEGI (`p4_6` = sexo, `p4_8` = año en 2 dígitos)
- Conversión de tipos (`pd.to_numeric`, `pd.to_datetime`)
- Validación de rangos (edades 0–90, años 2015–2024)
- Clasificación de causas de muerte en tipos de riesgo (`Physical`, `Legal`, `Economic`, `Social`)
- Generación de catálogos estáticos (periodos, niveles, categorías, motivos, riesgos, impactos)
**Archivos generados en `data_clean/`:**
 
```
clean_paises.csv           # regions, countries
clean_estadisticas.csv     # global_statistics  (4 fuentes combinadas)
clean_unhcr.csv            # global_statistics  (demografía UNHCR)
clean_inegi.csv            # migrants, migrations
clean_missing.csv          # migration_risk
clean_riesgos_missing.csv  # risks (causas reales)
clean_periodos.csv         # periods
clean_niveles.csv          # socioeconomic_levels
clean_categorias.csv       # motive_categories
clean_motivos.csv          # motives
clean_riesgos.csv          # risks (catálogo base)
clean_impactos.csv         # impacts
```
 
---
 
### Fase 3 — Carga `fase3_carga.py`
 
Inserta todos los datos en MySQL respetando el orden de las llaves foráneas.
 
**Orden de carga:**
 
```
1. regions                # clean_paises.csv
2. countries              # clean_paises.csv
3. socioeconomic_levels   # clean_niveles.csv
4. motive_categories      # clean_categorias.csv
5. motives                # clean_motivos.csv
6. periods                # clean_periodos.csv
7. risks                  # clean_riesgos.csv + clean_riesgos_missing.csv
8. impacts                # clean_impactos.csv
9. global_statistics      # clean_estadisticas.csv + clean_unhcr.csv
10. migrants              # clean_inegi.csv
11. migrations            # clean_inegi.csv
12. migration_risk        # clean_missing.csv
13. migration_impact      # clean_impactos.csv
```
---
### Fase 3.5 — Clonar `daseconexion.py`
---
### Herramientas utilizadas
![](https://xpertlab.com/wp-content/uploads/2020/01/pyCharm.png)
> Pycharm:PyCharm es un entorno de desarrollo integrado (IDE) diseñado específicamente para programar en el lenguaje Python
**Librerías Python**
 
| Librería | Uso |
|----------|-----|
| `pandas` | Manipulación y limpieza de DataFrames |
| `numpy` | Operaciones numéricas y manejo de nulos |
| `requests` | Consumo de APIs REST |
| `mysql-connector-python` | Conexión e inserción a MySQL |
| `matplotlib` | Gráficas estáticas (Fase 4) |
| `seaborn` | Gráficas estadísticas (Fase 4) |
| `plotly` | Dashboards interactivos (Fase 4) |

![](https://www.ovhcloud.com/sites/default/files/styles/large_screens_1x/public/2021-09/ECX-1909_Hero_MySQL_600x400%402x-1.png)
> MySQL es el sistema de gestión de bases de datos relacionales (Relational Database Management System) de código abierto más popular del mundo y se utiliza principalmente para almacenar, organizar y recuperar grandes volúmenes de datos de manera eficiente mediante el lenguaje SQL (Structured Query Language).

| Tecnología | Uso |
|------------|-----|
| MySQL 8+ | Motor relacional principal |
| MySQL Workbench | Diseño del DER y ejecución de scripts |
| InnoDB | Motor de tablas (soporte ACID completo) |

![](https://programacion.net/files/new/new_02240_.jpeg)
> MongoDB es un sistema de base de datos NoSQL orientado a documentos, diseñado para almacenar grandes volúmenes de datos con alta flexibilidad y escalabilidad

**Fuentes de datos**
 
| Fuente | Tipo | Datos |
|--------|------|-------|
| INEGI ENADID 2023 | CSV oficial | Migrantes mexicanos (3,660 registros) |
| ONU DESA 2024 | CSV oficial | Stock migratorio mundial (224,240 registros) |
| World Bank API | API REST | Migración neta por país 2015–2023 |
| UNHCR API | API REST | Demografía de solicitantes de asilo en México |
| IOM Missing Migrants | CSV | Migrantes muertos y desaparecidos (13,020 registros) |
| World Pop Migration | CSV | Población y migración 186 países |

**Control de versiones**
 
![Git](https://img.shields.io/badge/Git-F05032?logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white)
 
---

## Licencia 
Proyecto académico de la Universidad Autónoma de Baja California
Uso exclusivo para fines educativos ( de estudiantes).
