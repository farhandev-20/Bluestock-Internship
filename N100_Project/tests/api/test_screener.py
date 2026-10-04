"""
Unit and Integration Tests for FastAPI Screener Endpoint (Day 42).
"""

from fastapi.testclient import TestClient
import pytest
from src.api.main import app

client = TestClient(app)


def test_screener_unfiltered():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert data["matched_count"] > 0
    assert len(data["results"]) == data["matched_count"]


def test_screener_filter_roe():
    response = client.get("/api/v1/screener?min_roe=15.0")
    assert response.status_code == 200
    data = response.json()
    for row in data["results"]:
        assert row["return_on_equity_pct"] >= 15.0


def test_screener_filter_combined():
    response = client.get("/api/v1/screener?min_roe=12.0&max_de=1.0&min_fcf=0")
    assert response.status_code == 200
    data = response.json()
    for row in data["results"]:
        assert row["return_on_equity_pct"] >= 12.0
        if row["debt_to_equity"] is not None:
            assert row["debt_to_equity"] <= 1.0


def test_screener_invalid_param_400():
    response = client.get("/api/v1/screener?max_de=-5.0")
    assert response.status_code == 400
    assert "must be non-negative" in response.json()["detail"]


def test_screener_invalid_pe_400():
    response = client.get("/api/v1/screener?max_pe=-10.0")
    assert response.status_code == 400
    assert "strictly positive" in response.json()["detail"]
