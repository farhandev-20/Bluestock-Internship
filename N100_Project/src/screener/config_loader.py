"""
Screener Configuration Loader for N100 Intelligence Platform.
Reads and validates config/screener_config.yaml.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "screener_config.yaml"


def load_screener_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load YAML configuration file defining metrics and screener presets.
    """
    cfg_file = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not cfg_file.exists():
        raise FileNotFoundError(f"Screener configuration file not found: {cfg_file}")

    with open(cfg_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Invalid YAML configuration: root element must be a dictionary.")

    if "presets" not in config:
        raise ValueError("Invalid YAML configuration: 'presets' section is missing.")

    return config
