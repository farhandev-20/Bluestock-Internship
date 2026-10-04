"""
Master execution script for the Bluestock Mutual Fund Analytics project.

Run from the project root with:
    python scripts/run_pipeline.py

The script executes ETL, live NAV retrieval, performance metrics and
recommendation generation in sequence.
"""

from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def run_script(script_name: str) -> None:
    """Run a project script with the current Python interpreter."""
    script_path = SCRIPTS_DIR / script_name
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {result.returncode}")


def main() -> None:
    """Execute the complete analytics pipeline."""
    run_script("etl_pipeline.py")
    run_script("live_nav_fetch.py")
    run_script("compute_metrics.py")
    run_script("recommender.py")
    print("Master pipeline completed successfully.")


if __name__ == "__main__":
    main()
