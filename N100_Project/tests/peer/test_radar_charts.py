"""
Unit tests for Radar Charts Generation (Day 19).
"""

from pathlib import Path
import pytest
from src.analytics.peer import generate_radar_charts, RADAR_CHARTS_DIR


def test_radar_charts_generation(tmp_path):
    out_dir = tmp_path / "radar_charts"
    charts = generate_radar_charts(output_dir=out_dir)

    assert len(charts) > 0, "No radar charts were generated"
    assert out_dir.exists()

    # Verify PNG files exist and are non-empty
    for chart_path in charts[:10]:
        assert chart_path.exists()
        assert chart_path.suffix == ".png"
        assert chart_path.stat().st_size > 1000  # Valid non-empty PNG
