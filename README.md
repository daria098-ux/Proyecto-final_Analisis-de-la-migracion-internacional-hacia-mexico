# International Migration Analysis toward Mexico
> Final Integrative Project — Programming · Database · Data Analysis
---

## User Manual — How to Run the Project

### Step 1: Clone the repository

Open a terminal (PowerShell, CMD, or Git Bash) and run:

```bash
git clone https://github.com/daria098-ux/Proyecto-final_Analisis-de-la-migracion-internacional-hacia-mexico.git
cd Proyecto-final_Analisis-de-la-migracion-internacional-hacia-mexico
```

### Step 2: Install Python 3.9+

Download it from [python.org](https://www.python.org/downloads/).

> **IMPORTANT for Windows:** During installation, check the box **"Add Python to PATH"** at the bottom of the first screen. This prevents the following errors:
> - `pip is not recognized`
> - `Python was not found`
> - `Token '-m' inesperado` in PowerShell

If Python is already installed but not in PATH, you must use the full path in PowerShell. **Replace `YourUser` with your actual Windows username** and adjust the Python version number:

```powershell
# Example — change "YourUser" and "Python314" to match your system
& "C:\Users\YourUser\AppData\Local\Programs\Python\Python314\python.exe" -m pip install -r requirements.txt
```

> **Note for PowerShell:** The `&` symbol is required before a quoted path. Without it, PowerShell throws `Token '-m' inesperado`.

### Step 3: Open the project in PyCharm

1. Open PyCharm → **File → Open** → select the cloned folder
2. Go to **File → Settings → Project → Python Interpreter**
3. Click the **gear icon** → **Add Interpreter → System Interpreter**
4. Select your Python installation (e.g. `Python314\python.exe`)
5. Click **OK**

PyCharm will automatically create a `.venv` (virtual environment). You will see `(.venv)` in green at the start of your terminal prompt. **This is normal — keep it active.**

If the `.venv` gives errors, delete it and reconfigure:
```powershell
Remove-Item -Recurse -Force .venv
```

> **If you get a PowerShell execution policy error**, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Step 4: Install dependencies

**Option A — If `.venv` is active** (you see `(.venv)` in green):

```bash
pip install -r requirements.txt
```

**Option B — If `pip` is not recognized:**

```bash
python -m pip install -r requirements.txt
```

**Option C — If neither works, use the full Python path** (replace with your username):

```powershell
& "C:\Users\YourUser\AppData\Local\Programs\Python\Python314\python.exe" -m pip install -r requirements.txt
```

> **Common mistakes:**
> - `pip install -requierements.txt` → WRONG. It's `-r requirements.txt` (with a space after `-r`)
> - `pip install requirements.txt` → WRONG. You need the `-r` flag
> - Using someone else's Python path → WRONG. Each person must use their own path

### Step 5: Set up MySQL

1. Install **MySQL Server 8.0+** and **MySQL Workbench** if not already installed
2. Open MySQL Workbench and connect to your local server
3. Run the database schema script:

```sql
source Databases/mexico_migration_final.sql;
```

This creates the `mexico_migration` database with all 14 tables, triggers, stored procedures, and views.

### Step 6: Configure your MySQL password

Open each of these files and set your MySQL root password where it says `"password": ""`:

| File | Line to change |
|------|---------------|
| `Programs/phase3_loading.py` | `"password": ""` → `"password": "your_password"` |
| `Programs/phase3.5_mongodb_clone.py` | `password=""` → `password="your_password"` |
| `Programs/phase4_patches.py` | `"password": ""` → `"password": "your_password"` |
| `Dashboards/export_views.py` | `"password": ""` → `"password": "your_password"` |

> **Security:** Never commit your password to GitHub. The files use empty strings by default. Only set your password locally.

### Step 7: Run the ETL pipeline

From the project root folder. **Make sure you are in the project root, NOT inside a subfolder:**

```bash
# Verify you're in the right folder — you should see run_all.py
dir run_all.py

# Then run the pipeline
python run_all.py
```

If `python` is not recognized:

```powershell
& "C:\Users\YourUser\AppData\Local\Programs\Python\Python314\python.exe" run_all.py
```

The pipeline runs 6 phases in order:

```
Phase 1  →  Extraction (APIs + CSVs)
Phase 2  →  Transformation (cleaning)
Phase 3  →  MySQL Loading (stored procedures)
Phase 4  →  SQL Patches (improved views)
Phase 5  →  MongoDB Clone (optional)
Phase 6  →  Export Views (generates CSVs for dashboard)
```

**Optional flags:**

```bash
python run_all.py --skip-mongo     # skip MongoDB cloning
python run_all.py --only extract   # run only Phase 1
python run_all.py --from load      # start from Phase 3
```

### Step 8: Launch the dashboard

From the project root folder (NOT inside Dashboards/):

```bash
python -m streamlit run Dashboards/dashboard.py
```

> **Important:**
> - Run this from the **project root**, not from inside the `Dashboards/` folder
> - The command must be a **single line** — do not split it across multiple lines
> - If you're inside `Dashboards/`, go back with `cd ..`

If `python` is not recognized:

```powershell
& "C:\Users\YourUser\AppData\Local\Programs\Python\Python314\python.exe" -m streamlit run Dashboards\dashboard.py
```

A browser window will open automatically at `http://localhost:8501` with 5 interactive dashboards.

> **About `.venv`:** You do NOT need to deactivate the virtual environment to run the dashboard. Keep `(.venv)` active — it works fine with Streamlit.

---

### Troubleshooting (Windows)

| Problem | Solution |
|---------|----------|
| `pip is not recognized` | Use `python -m pip install -r requirements.txt` or add Python to PATH |
| `Python was not found` | Use the full path: `& "C:\Users\YourUser\AppData\Local\Programs\Python\Python314\python.exe" -m pip ...` |
| `Token '-m' inesperado` in PowerShell | Add `&` before the quoted path: `& "C:\...\python.exe" -m pip ...` |
| `Invalid requirement: '.txt'` | You typed `-requirements.txt` instead of `-r requirements.txt`. Use `-r` with a space |
| `YourUser` path not found | Replace `YourUser` with your actual Windows username |
| PowerShell execution policy error | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `.venv` errors in PyCharm | Delete `.venv` folder and reconfigure interpreter: `Remove-Item -Recurse -Force .venv` |
| `.venv` activates automatically | This is normal. Keep it active — you can run all commands inside `.venv` |
| `IndentationError` in phase1_extraction.py | Make sure you have the latest version from GitHub (fixed) |
| `Access denied` MySQL | Check your password in the 4 files from Step 6 |
| Streamlit `File does not exist: streamlit_app.py` | You forgot to specify the file. Use `python -m streamlit run Dashboards\dashboard.py` |
| Streamlit `File does not exist: Dashboards\dashboard.py` | You're inside `Dashboards/`. Run `cd ..` and then the command from project root |
| Dashboard shows empty charts | Make sure `run_all.py` completed successfully first |
| `where python` returns nothing | Python is not installed or not in PATH. Reinstall with "Add to PATH" checked |

---

## Description

Complete ETL system that extracts, transforms, loads, and visualizes real data about international migration toward Mexico. The project answers five key questions using data from official sources (INEGI, UN, World Bank, UNHCR), a normalized relational MySQL database (up to 3NF), and interactive dashboards with Python.

### Questions answered by the system

| # | Question |
|---|----------|
| 1 | What are the main reasons for migration toward Mexico? |
| 2 | What percentage of migrants does Mexico receive compared to other countries? |
| 3 | Which countries do most migrants come from? |
| 4 | What risks do migrants face in Mexico? |
| 5 | What is the social and economic impact in Mexico? |

---
## Project structure

```
migracion-mexico/
│
├── run_all.py                        # Pipeline orchestrator (runs all phases in order)
│
├── Programs/
│   ├── phase1_extraction.py          # Phase 1 — Extract: APIs + local CSVs
│   ├── phase2_transformation.py      # Phase 2 — Transform: cleaning and standardization
│   ├── phase3_loading.py             # Phase 3 — Load: insertion into MySQL
│   ├── phase3.5_mongodb_clone.py     # Phase 3.5 — Clone: MySQL → MongoDB
│   └── phase4_patches.py            # Phase 4 — Apply SQL view patches
│
├── Dashboards/
│   ├── dashboard.py                  # 5 interactive Streamlit dashboards
│   ├── export_views.py              # Export 6 SQL views → CSV for dashboard
│   └── .streamlit/config.toml       # Streamlit theme configuration
│
├── Databases/
│   ├── mexico_migration_final.sql   # Complete DB schema (tables, triggers, SPs, views)
│   └── patches.sql                  # View patches (removes Mexico filters, adds iso_code)
│
├── CSV_Data/                         # Downloaded CSV files (local sources)
│   ├── cleaned_undesa_2024_ims_stock_by_sex_destination_and_origin_1990-2024.csv
│   ├── world_pop_mig_186_countries.csv
│   ├── Global_Missing_Migrants_Dataset.csv
│   ├── data.csv
│   └── TMIGRANTE.csv
│
├── data_raw/                         # Raw CSVs generated by Phase 1
├── data_clean/                       # Clean CSVs generated by Phase 2
│
└── README.md
```
---
## Project phases
### Phase 1 — Extraction `Programs/phase1_extraction.py`

Extracts data from **3 APIs** and **5 local CSV files** and saves them to `data_raw/`.

**APIs:**

| API | Endpoint | Data extracted |
|-----|----------|----------------|
| REST Countries | `restcountries.com/v3.1/alpha/{iso}` | Name, ISO and region of each country |
| World Bank | `api.worldbank.org` — indicator `SM.POP.NETM` | Net migration by country and year |
| UNHCR | `api.unhcr.org/population/v1/demographics/` | Migrant demographics in Mexico by country of origin |

**Local CSVs:**

| File | Source | Target table |
|------|--------|--------------|
| `cleaned_undesa_2024...csv` | UN DESA | `global_statistics` |
| `world_pop_mig_186_countries.csv` | Kaggle | `global_statistics` |
| `Global_Missing_Migrants_Dataset.csv` | IOM / Kaggle | `risks`, `migration_risk` |
| `data.csv` | World Bank | `global_statistics` |
| `TMIGRANTE.csv` | INEGI ENADID 2023 | `migrants`, `migrations` |

---

### Phase 2 — Transformation `Programs/phase2_transformation.py`

Reads CSVs from `data_raw/`, cleans them, and generates normalized CSVs in `data_clean/`.

**Applied operations:**

- Null and duplicate removal
- Country name standardization (`"México"` → `"Mexico"`)
- INEGI encoding correction (`p4_6` = sex, `p4_8` = 2-digit year)
- Type conversion (`pd.to_numeric`, `pd.to_datetime`)
- Range validation (ages 0–90, years 2015–2024)
- Classification of death causes into risk types (`Physical`, `Legal`, `Economic`, `Social`)
- Static catalog generation (periods, levels, categories, motives, risks, impacts)

**Files generated in `data_clean/`:**

```
clean_countries.csv        # regions, countries
clean_statistics.csv       # global_statistics  (4 combined sources)
clean_unhcr.csv            # global_statistics  (UNHCR demographics)
clean_inegi.csv             # migrants, migrations
clean_missing.csv           # migration_risk
clean_risks_missing.csv     # risks (real causes)
clean_periods.csv           # periods
clean_levels.csv            # socioeconomic_levels
clean_categories.csv        # motive_categories
clean_motives.csv           # motives
clean_risks.csv             # risks (base catalog)
clean_impacts.csv           # impacts
```

---

### Phase 3 — Loading `Programs/phase3_loading.py`

Inserts all data into MySQL respecting foreign key order.

**Loading order:**

```
1. regions                # clean_countries.csv
2. countries              # clean_countries.csv
3. socioeconomic_levels   # clean_levels.csv
4. motive_categories      # clean_categories.csv
5. motives                # clean_motives.csv
6. periods                # clean_periods.csv
7. risks                  # clean_risks.csv + clean_risks_missing.csv
8. impacts                # clean_impacts.csv
9. global_statistics      # clean_statistics.csv + clean_unhcr.csv
10. migrants              # clean_inegi.csv
11. migrations             # clean_inegi.csv
12. migration_risk         # clean_missing.csv
13. migration_impact        # clean_impacts.csv
```
---
### Phase 3.5 — Clone `Programs/phase3.5_mongodb_clone.py`

Clones all 14 MySQL tables into MongoDB collections using bulk-read stored procedures. Each table is read, sanitized (Decimal → float), and bulk-inserted into `mexico_migration_nosql`.

---

### Phase 4 — Patches `Programs/phase4_patches.py`

Applies `Databases/patches.sql` to improve the SQL views used by the dashboard. Patches remove Mexico-only filters and add the `iso_code` column for better international comparison.

---

### Phase 5 — Dashboard `Dashboards/dashboard.py`

5 interactive Streamlit dashboards powered by exported SQL views:

| # | Dashboard | View |
|---|-----------|------|
| 1 | Migration Motives | `vw_top_motives` |
| 2 | Origin Countries | `vw_origin_countries` |
| 3 | International Comparison | `vw_international_comparison` |
| 4 | Risks and Threats | `vw_migrant_risks` |
| 5 | Impacts on Mexico | `vw_impacts_on_mexico` + `vw_demographic_profile` |

**Run:** `python -m streamlit run Dashboards/dashboard.py`

---

### Pipeline Orchestrator `run_all.py`

Runs all phases in order with colored output, timing, and error handling:

```bash
python run_all.py                  # full pipeline
python run_all.py --skip-mongo     # skip MongoDB cloning
python run_all.py --only export    # only run the export phase
python run_all.py --from load      # start from the load phase
```
---
### Tools used

**Python libraries**

| Library | Usage |
|---------|-------|
| `pandas` | DataFrame manipulation and cleaning |
| `numpy` | Numerical operations and null handling |
| `requests` | REST API consumption |
| `mysql-connector-python` | MySQL connection and insertion |
| `pymongo` | MongoDB cloning (Phase 3.5) |
| `streamlit` | Interactive dashboard framework (Phase 5) |
| `plotly` | Interactive charts in dashboard |

**Database**

| Technology | Usage |
|------------|-------|
| MySQL 8+ | Main relational engine |
| MySQL Workbench | ERD design and script execution |
| InnoDB | Table engine (full ACID support) |
| MongoDB Compass | NoSQL document database |

**Data sources**

| Source | Type | Data |
|--------|------|------|
| INEGI ENADID 2023 | Official CSV | Mexican migrants (3,660 records) |
| UN DESA 2024 | Official CSV | Global migrant stock (224,240 records) |
| World Bank API | REST API | Net migration by country 2015–2023 |
| UNHCR API | REST API | Demographics of asylum seekers in Mexico |
| IOM Missing Migrants | CSV | Dead and missing migrants (13,020 records) |
| World Pop Migration | CSV | Population and migration 186 countries |

**Version control**

![Git](https://img.shields.io/badge/Git-F05032?logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white)

---

## License
Academic project from Universidad Autonoma de Baja California
For educational use only (by students).