"""
run_all.py - Unified ETL Pipeline Orchestrator
Project: International Migration Analysis to Mexico
Universidad Autonoma de Baja California
================================================================

Runs all pipeline phases in order, reports success/failure of each
phase and prints a final summary with timings.

Usage:
    python run_all.py                  # full pipeline
    python run_all.py --skip-mongo     # skip MongoDB cloning
    python run_all.py --only export    # only run the export phase
    python run_all.py --from load      # start from the load phase
    python run_all.py --help

Phases:
    1. EXTRACTION    (Programs/extraccion.py)
    2. TRANSFORMATION (Programs/fase2_transformacion_datos.py)
    3. MYSQL LOAD    (Programs/fase3.py)
    4. SQL PATCHES   (Programs/aplicar_patches.py)
    5. MONGODB CLONE (Programs/english_cloning.py)           [optional]
    6. EXPORT VIEWS  (Dashboards/export_views.py)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ----------------------------------------------------------------------
# ANSI colors (modern Windows terminals support them; this enables them)
# ----------------------------------------------------------------------
if os.name == "nt":
    os.system("")   # enables ANSI on Windows 10+

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
GRAY   = "\033[90m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
ROOT       = Path(__file__).parent.resolve()
PROGRAMS   = ROOT / "Programs"
DASHBOARDS = ROOT / "Dashboards"
CSV_DATA   = ROOT / "CSV_Data"


# ----------------------------------------------------------------------
# Pipeline phases (in order)
# ----------------------------------------------------------------------
PHASES = [
    {
        "id":          "extract",
        "name":        "EXTRACTION",
        "script":      PROGRAMS / "extraccion.py",
        "cwd":         PROGRAMS,
        "description": "Download data from 3 APIs and read 5 local CSVs",
        "optional":    False,
    },
    {
        "id":          "transform",
        "name":        "TRANSFORMATION",
        "script":      PROGRAMS / "fase2_transformacion_datos.py",
        "cwd":         PROGRAMS,
        "description": "Clean, normalize and generate static catalogs",
        "optional":    False,
    },
    {
        "id":          "load",
        "name":        "MYSQL LOAD",
        "script":      PROGRAMS / "fase3.py",
        "cwd":         PROGRAMS,
        "description": "Insert cleaned CSVs into the mexico_migration database",
        "optional":    False,
    },
    {
        "id":          "patches",
        "name":        "SQL PATCHES",
        "script":      PROGRAMS / "aplicar_patches.py",
        "cwd":         PROGRAMS,
        "description": "Apply patches.sql (improves SQL views for the dashboard)",
        "optional":    False,
    },
    {
        "id":          "mongo",
        "name":        "MONGODB CLONE",
        "script":      PROGRAMS / "english_cloning.py",
        "cwd":         PROGRAMS,
        "description": "Clone MySQL tables to MongoDB (NoSQL)",
        "optional":    True,
    },
    {
        "id":          "export",
        "name":        "EXPORT VIEWS",
        "script":      DASHBOARDS / "export_views.py",
        "cwd":         DASHBOARDS,
        "description": "Export 6 SQL views to CSV files for the dashboard",
        "optional":    False,
    },
]


# ----------------------------------------------------------------------
# Visual helpers
# ----------------------------------------------------------------------
HLINE = "=" * 76
SLINE = "-" * 76


def header_box(line1: str, line2: str = ""):
    """Prints a nice header box at the start of the pipeline."""
    print(f"{CYAN}{HLINE}{RESET}")
    print(f"{CYAN}  {BOLD}{line1}{RESET}")
    if line2:
        print(f"{CYAN}  {line2}{RESET}")
    print(f"{CYAN}{HLINE}{RESET}")


def phase_header(num: int, total: int, fase: dict):
    """Prints the header that introduces each phase."""
    print()
    print(f"{BLUE}{SLINE}{RESET}")
    print(f"{BLUE}  [{num}/{total}]  {BOLD}{fase['name']}{RESET}")
    print(f"{BLUE}         {GRAY}{fase['description']}{RESET}")
    print(f"{BLUE}{SLINE}{RESET}")


def status_tag(state: str) -> str:
    """Returns a colored status tag like [ SUCCESS ], [ FAILED ], [ SKIPPED ]."""
    if state == "ok":
        return f"{GREEN}[ SUCCESS ]{RESET}"
    if state == "fail":
        return f"{RED}[  FAILED ]{RESET}"
    if state == "skip":
        return f"{YELLOW}[ SKIPPED ]{RESET}"
    return f"[{state.upper():^9}]"


# ----------------------------------------------------------------------
# Pre-flight check
# ----------------------------------------------------------------------
def preflight():
    """
    1. Verify the original CSVs are in CSV_Data/.
    2. Clean any leftovers in Programs/ (loose CSVs or data_raw/data_clean
       subfolders that old script versions used to create there).
    """
    print()
    print(f"{CYAN}{BOLD}Pre-flight check{RESET}")

    if not CSV_DATA.exists():
        print(f"   {RED}[ WARN ]{RESET} Missing CSV_Data/ folder (expected at {CSV_DATA})")
        return

    csvs_needed = [
        "TMIGRANTE.csv",
        "data.csv",
        "world_pop_mig_186_countries.csv",
        "Global_Missing_Migrants_Dataset.csv",
        "cleaned_undesa_2024_ims_stock_by_sex_destination_and_origin_1990-2024.csv",
    ]
    missing = [n for n in csvs_needed if not (CSV_DATA / n).exists()]
    if missing:
        print(f"   {RED}[ WARN ]{RESET} Missing CSVs in CSV_Data/:")
        for n in missing:
            print(f"           - {n}")
    else:
        print(f"   {GREEN}[ OK ]{RESET}   All original CSVs present in CSV_Data/")

    # Clean leftovers in Programs/
    cleaned = 0
    for name in csvs_needed:
        polluted = PROGRAMS / name
        if polluted.exists():
            polluted.unlink()
            cleaned += 1
    for sub in ("data_raw", "data_clean"):
        polluted_dir = PROGRAMS / sub
        if polluted_dir.exists() and polluted_dir.is_dir():
            shutil.rmtree(polluted_dir)
            cleaned += 1

    if cleaned:
        print(f"   {YELLOW}[ CLEAN ]{RESET} Removed {cleaned} leftover(s) from Programs/")
    else:
        print(f"   {GREEN}[ OK ]{RESET}   Programs/ is clean (only .py files)")


# ----------------------------------------------------------------------
# Phase execution
# ----------------------------------------------------------------------
def run_phase(fase: dict):
    if not fase["script"].exists():
        return False, 0.0, f"script not found: {fase['script'].name}"

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(fase["script"])],
            cwd=str(fase["cwd"]),
            check=False,
        )
    except KeyboardInterrupt:
        return False, time.time() - start, "interrupted by user (Ctrl+C)"
    except Exception as e:
        return False, time.time() - start, f"unexpected exception: {e}"

    elapsed = time.time() - start
    if result.returncode == 0:
        return True, elapsed, "OK"
    return False, elapsed, f"exit code {result.returncode}"


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="ETL pipeline orchestrator for the migration project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--skip-mongo", action="store_true",
                        help="Skip the MongoDB cloning phase.")
    parser.add_argument("--only", choices=[f["id"] for f in PHASES],
                        help="Run only the specified phase and exit.")
    parser.add_argument("--from", dest="start_from", choices=[f["id"] for f in PHASES],
                        help="Start the pipeline from the specified phase.")
    parser.add_argument("--no-preflight", action="store_true",
                        help="Skip the pre-flight check.")
    return parser.parse_args()


def select_phases(args):
    if args.only:
        return [f for f in PHASES if f["id"] == args.only]
    fases = list(PHASES)
    if args.start_from:
        ids = [f["id"] for f in fases]
        idx = ids.index(args.start_from)
        fases = fases[idx:]
    if args.skip_mongo:
        fases = [f for f in fases if f["id"] != "mongo"]
    return fases


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    args = parse_args()

    header_box(
        "FINAL PROJECT  -  INTERNATIONAL MIGRATION TO MEXICO ANALYSIS",
        "Unified Pipeline | UABC",
    )

    if not args.no_preflight and not args.only and not args.start_from:
        preflight()

    phases_to_run = select_phases(args)
    total = len(phases_to_run)
    results = []
    total_start = time.time()

    print()
    print(f"{CYAN}{BOLD}Phases to run: {total}{RESET}")
    for f in phases_to_run:
        mark = f" {GRAY}(optional){RESET}" if f["optional"] else ""
        print(f"   {GREEN}>{RESET} {f['name']}{mark}")

    for i, fase in enumerate(phases_to_run, start=1):
        phase_header(i, total, fase)
        ok, elapsed, msg = run_phase(fase)
        results.append({
            "name":     fase["name"],
            "ok":       ok,
            "elapsed":  elapsed,
            "msg":      msg,
            "optional": fase["optional"],
        })

        print()
        if ok:
            print(f"  {status_tag('ok')} {BOLD}{fase['name']}{RESET} completed in {GREEN}{elapsed:.1f}s{RESET}")
        elif fase["optional"]:
            print(f"  {status_tag('skip')} {fase['name']} skipped - {msg} ({elapsed:.1f}s)")
            print(f"           {GRAY}(optional, continuing pipeline){RESET}")
        else:
            print(f"  {status_tag('fail')} {BOLD}{fase['name']}{RESET} failed - {msg} ({elapsed:.1f}s)")
            print(f"           {RED}Pipeline stopped due to critical error.{RESET}")
            break

    total_elapsed = time.time() - total_start

    # ---------- Final summary ----------
    print()
    print(f"{CYAN}{HLINE}{RESET}")
    print(f"{CYAN}  {BOLD}PIPELINE SUMMARY{RESET}")
    print(f"{CYAN}{HLINE}{RESET}")
    for r in results:
        if r["ok"]:
            tag = status_tag("ok")
        elif r["optional"]:
            tag = status_tag("skip")
        else:
            tag = status_tag("fail")
        print(f"  {tag}  {r['name']:<24}  {GREEN}{r['elapsed']:>6.1f}s{RESET}   {GRAY}{r['msg']}{RESET}")
    print(f"{CYAN}{HLINE}{RESET}")
    print(f"  {BOLD}Total time:{RESET} {GREEN}{total_elapsed:.1f}s{RESET}")
    print(f"{CYAN}{HLINE}{RESET}")

    # Overall result
    critical_ok = all(r["ok"] or r["optional"] for r in results)
    if critical_ok and results:
        print()
        print(f"{GREEN}{BOLD}  Pipeline completed successfully.{RESET}")
        print()
        print(f"  {CYAN}Next step - launch the dashboard:{RESET}")
        print(f"     {BOLD}cd Dashboards{RESET}")
        print(f"     {BOLD}streamlit run dashboard.py{RESET}")
        print()
        return 0
    else:
        print()
        print(f"{RED}{BOLD}  Pipeline incomplete. Review the messages above.{RESET}")
        print()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}  Interrupted by user.{RESET}")
        sys.exit(130)
