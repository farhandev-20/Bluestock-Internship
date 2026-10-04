import pandas as pd
from pathlib import Path
from src.etl.pipeline import run_pipeline


def test_full_pipeline_run(tmp_path):
    test_db = tmp_path / "test_pipeline.db"
    test_out = tmp_path / "output"

    results = run_pipeline(
        db_path=test_db,
        output_dir=test_out,
        audit_only=False,
    )

    # 1. Verify datasets
    assert len(results["datasets"]) == 12
    assert len(results["datasets"]["companies"]) == 100

    # 2. Verify DB created and populated
    assert test_db.exists()
    for tbl, stat in results["db_load_summary"].items():
        assert stat["status"] == "SUCCESS"
        assert stat["loaded_rows"] == stat["source_rows"]

    # 3. Verify Output CSVs created
    audit_file = test_out / "load_audit.csv"
    val_file = test_out / "validation_failures.csv"
    assert audit_file.exists()
    assert val_file.exists()

    # 4. Verify CSV content
    audit_df = pd.read_csv(audit_file)
    assert len(audit_df) == 12
    assert "source_rows" in audit_df.columns
    assert "loaded_rows" in audit_df.columns
    assert audit_df["source_rows"].sum() == 12892
    assert audit_df["loaded_rows"].sum() == 12900


def test_pipeline_audit_only_mode(tmp_path):
    test_db = tmp_path / "test_audit_only.db"
    test_out = tmp_path / "output"

    results = run_pipeline(
        db_path=test_db,
        output_dir=test_out,
        audit_only=True,
    )

    # DB should not be created in audit only mode
    assert not test_db.exists()

    audit_file = test_out / "load_audit.csv"
    val_file = test_out / "validation_failures.csv"
    assert audit_file.exists()
    assert val_file.exists()
