"""
Unit and Integration Tests for FastAPI Health Endpoint (Day 42).
"""

from fastapi.testclient import TestClient
import pytest
from src.api.main import app

client = TestClient(app)


def test_get_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "version" in data
    assert "db_row_counts" in data

    # Verify all 10 tables are present
    expected_tables = [
        "companies",
        "analysis",
        "balancesheet",
        "cashflow",
        "documents",
        "financial_ratios",
        "market_cap",
        "peer_groups",
        "profitandloss",
        "sectors",
    ]
    for tbl in expected_tables:
        assert tbl in data["db_row_counts"]
        assert data["db_row_counts"][tbl] > 0
