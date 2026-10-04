"""
Database helper and SQLite utilities for FastAPI REST service.
Includes JSON-safe cleaning for NaN and Infinite float values.
"""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_db_connection() -> sqlite3.Connection:
    """Returns a new sqlite3 connection with Row factory enabled."""
    conn = sqlite3.connect(str(DEFAULT_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def query_df(query: str, params: Optional[Sequence[Any]] = None) -> pd.DataFrame:
    """Executes a SQL query and returns a pandas DataFrame."""
    conn = sqlite3.connect(str(DEFAULT_DB_PATH))
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def clean_val(val: Any) -> Any:
    """Converts NaN, Inf, and numpy types to JSON-serializable Python native types."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (float, np.floating)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (bool, np.bool_)):
        return bool(val)
    return val


def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively cleans a dictionary for JSON compliance."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k] = clean_dict(v)
        elif isinstance(v, list):
            out[k] = [clean_dict(x) if isinstance(x, dict) else clean_val(x) for x in v]
        else:
            out[k] = clean_val(v)
    return out


def df_to_clean_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Converts a DataFrame to list of dicts with NaN/Inf values converted to None."""
    records = df.to_dict(orient="records")
    return [clean_dict(row) for row in records]
