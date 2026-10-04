"""
ETL Pipeline Orchestrator for N100 Financial Intelligence Platform.
Executes loading, normalization, DQ validation, SQLite persistence, and audit logging.
"""

from datetime import datetime
from pathlib import Path
import sys
import pandas as pd

from src.etl.loader import (
    load_all_files,
    load_to_sqlite,
    load_excel,
    DATA_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_SCHEMA_PATH,
    EXPECTED_FILES,
)
from src.etl.validator import DataQualityValidator, run_all_validations

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"


def run_pipeline(
    data_dir: Path = None,
    db_path: Path = None,
    schema_path: Path = None,
    output_dir: Path = None,
    audit_only: bool = False,
):
    """
    Execute full N100 ETL Pipeline:
    1. Load all 12 Excel files
    2. Normalize dataframes and seed verified parent companies
    3. Run 16 Data Quality checks
    4. Generate output/validation_failures.csv
    5. Load to SQLite database (unless audit_only) with full PK/FK constraints
    6. Generate output/load_audit.csv
    7. Return pipeline execution metrics
    """
    base_data_dir = data_dir or DATA_DIR
    target_db = db_path or DEFAULT_DB_PATH
    target_schema = schema_path or DEFAULT_SCHEMA_PATH
    out_dir = output_dir or OUTPUT_DIR

    out_dir.mkdir(parents=True, exist_ok=True)
    start_time = datetime.now()

    print("=" * 80)
    print("N100 FINANCIAL INTELLIGENCE PLATFORM - ETL PIPELINE")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 1. Load raw counts and assembled datasets
    print("\n[Step 1/4] Loading and normalizing 12 Excel source files...")
    raw_source_counts = {}
    for fname in EXPECTED_FILES:
        raw_df = load_excel(fname, data_dir=base_data_dir)
        raw_source_counts[Path(fname).stem] = len(raw_df)

    total_raw_rows = sum(raw_source_counts.values())
    print(f"-> Verified 12 raw source Excel files ({total_raw_rows:,} total source records)")

    datasets = load_all_files(data_dir=base_data_dir, seed_missing_parents=True)
    print(f"-> Assembled {len(datasets)} datasets with verified parent stubs for missing constituents")

    # 2. Data Quality Validations
    print("\n[Step 2/4] Executing 16 Data Quality rules...")
    validator = DataQualityValidator(datasets)
    failures_df = validator.run_all_rules()
    summary_df = validator.get_summary_dataframe()

    val_csv_path = out_dir / "validation_failures.csv"
    failures_df.to_csv(val_csv_path, index=False)
    print(f"-> Data Quality Checks Complete: {len(failures_df):,} total failure/warning records logged to '{val_csv_path.name}'")

    critical_failures = failures_df[failures_df["severity"] == "CRITICAL"]
    print(f"-> CRITICAL Failures: {len(critical_failures)} (Expected: 0)")

    print("\nData Quality Rule Summary:")
    for _, row in summary_df.iterrows():
        print(f"  [{row['status']}] {row['rule_id']}: {row['rule_name']} ({row['failed_records']} issues)")

    # 3. SQLite Database Loading
    db_load_summary = {}
    if not audit_only:
        print(f"\n[Step 3/4] Initializing and loading SQLite database at '{target_db.name}'...")
        db_load_summary = load_to_sqlite(
            db_path=target_db,
            schema_path=target_schema,
            datasets=datasets,
            enforce_fk=True,  # Foreign keys enforced
        )
        print("-> SQLite database populated successfully with PRAGMA foreign_keys = ON.")
    else:
        print("\n[Step 3/4] Skipping SQLite load (--audit-only mode)")

    # 4. Generate Load Audit Report
    print("\n[Step 4/4] Generating load audit report...")
    audit_rows = []
    timestamp_str = datetime.now().isoformat()

    for name in [Path(f).stem for f in EXPECTED_FILES]:
        df = datasets[name]
        raw_source_rows = raw_source_counts.get(name, len(df))
        db_stat = db_load_summary.get(name, {})
        loaded_count = db_stat.get("loaded_rows", len(df) if not audit_only else 0)
        table_failures = len(failures_df[failures_df["table_name"] == name]) if not failures_df.empty else 0
        null_count = int(df.isnull().sum().sum())

        audit_rows.append(
            {
                "table_name": name,
                "source_file": f"{name}.xlsx",
                "source_rows": raw_source_rows,
                "loaded_rows": loaded_count,
                "column_count": len(df.columns),
                "null_cell_count": null_count,
                "dq_failure_count": table_failures,
                "status": "SUCCESS" if loaded_count >= raw_source_rows else "MISMATCH",
                "load_timestamp": timestamp_str,
            }
        )

    audit_df = pd.DataFrame(audit_rows)
    audit_csv_path = out_dir / "load_audit.csv"
    audit_df.to_csv(audit_csv_path, index=False)
    print(f"-> Load audit report generated at '{audit_csv_path.name}'")

    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    for _, row in audit_df.iterrows():
        print(f"  Table: {row['table_name']:<18} | Source: {row['source_rows']:>5} | Loaded: {row['loaded_rows']:>5} | Status: {row['status']}")

    duration = (datetime.now() - start_time).total_seconds()
    print(f"\nPipeline finished in {duration:.2f} seconds.")

    return {
        "datasets": datasets,
        "failures_df": failures_df,
        "summary_df": summary_df,
        "audit_df": audit_df,
        "db_load_summary": db_load_summary,
    }


if __name__ == "__main__":
    audit_only = "--audit-only" in sys.argv
    run_pipeline(audit_only=audit_only)
