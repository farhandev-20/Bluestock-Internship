"""
Fetch current NAV data from MFAPI for selected mutual fund schemes.

Scheme codes can be supplied through the MF_SCHEME_CODES environment variable
as a comma-separated list. If the variable is not supplied, the script uses
the first five AMFI codes from data/processed/fund_master.csv.

Outputs are written to data/processed as <scheme_name>_live_nav.csv.
"""

from pathlib import Path
import os
import re
import requests
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
API_BASE = "https://api.mfapi.in/mf"


def safe_filename(value: str) -> str:
    """Convert a scheme name into a filesystem-safe filename."""
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return value.strip("_") or "scheme"


def get_scheme_codes() -> list[str]:
    """Read scheme codes from the environment or fund master."""
    configured = os.getenv("MF_SCHEME_CODES", "").strip()
    if configured:
        return [code.strip() for code in configured.split(",") if code.strip()]

    fund_master = PROCESSED_DIR / "fund_master.csv"
    if not fund_master.exists():
        raise FileNotFoundError(f"Fund master not found: {fund_master}")

    df = pd.read_csv(fund_master, dtype={"amfi_code": str})
    return df["amfi_code"].dropna().astype(str).drop_duplicates().head(5).tolist()


def fetch_latest_nav(code: str) -> pd.DataFrame:
    """Fetch the latest available NAV record from MFAPI."""
    response = requests.get(f"{API_BASE}/{code}/latest", timeout=20)
    response.raise_for_status()
    payload = response.json()

    if "data" not in payload or not payload["data"]:
        raise ValueError(f"No NAV data returned for AMFI code {code}")

    records = pd.DataFrame(payload["data"])
    records["amfi_code"] = str(code)
    records["date"] = pd.to_datetime(records["date"], dayfirst=True, errors="coerce")
    records["nav"] = pd.to_numeric(records["nav"], errors="coerce")
    return records[["amfi_code", "date", "nav"]].dropna(subset=["date", "nav"])


def run_live_nav_fetch() -> list[Path]:
    """Fetch NAV data for configured schemes and save CSV outputs."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    codes = get_scheme_codes()

    fund_master_path = PROCESSED_DIR / "fund_master.csv"
    fund_master = pd.read_csv(fund_master_path, dtype={"amfi_code": str})
    name_map = (
        fund_master.drop_duplicates("amfi_code")
        .set_index("amfi_code")["scheme_name"]
        .to_dict()
    )

    outputs = []
    for code in codes:
        data = fetch_latest_nav(code)
        scheme_name = str(name_map.get(str(code), f"scheme_{code}"))
        destination = PROCESSED_DIR / f"{safe_filename(scheme_name)}_live_nav.csv"
        data.to_csv(destination, index=False)
        outputs.append(destination)

    return outputs


if __name__ == "__main__":
    outputs = run_live_nav_fetch()
    print(f"Live NAV fetch completed: {len(outputs)} files saved.")
