"""
Unit and Integration Tests for FastAPI Sector and Peer Endpoints (Day 42).
"""

from fastapi.testclient import TestClient
import pytest
from src.api.main import app

client = TestClient(app)


def test_list_all_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 11
    assert len(data["sectors"]) == 11
    first_sec = data["sectors"][0]
    assert "sector" in first_sec
    assert "company_count" in first_sec
    assert "median_roe" in first_sec


def test_get_sector_constituents_valid():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    for comp in data["companies"]:
        assert comp["broad_sector"] == "Information Technology"


def test_get_sector_constituents_invalid_404():
    response = client.get("/api/v1/sectors/INVALID_SECTOR_ABC/companies")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_peer_group_details():
    response = client.get("/api/v1/peers/Private%20Banks")
    assert response.status_code == 200
    data = response.json()
    assert data["peer_group"] == "Private Banks"
    assert data["constituent_count"] > 0


def test_get_peer_radar_compare():
    response = client.get("/api/v1/companies/TCS/peers/compare")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert "peer_group_average" in data
    assert "benchmark_metrics" in data


def test_get_market_cap_multiples():
    response = client.get("/api/v1/market-cap/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert len(data["multiples"]) >= 5


def test_get_portfolio_stats():
    response = client.get("/api/v1/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["kpi_count"] == 10
    assert len(data["statistics"]) == 10


def test_get_company_documents():
    response = client.get("/api/v1/companies/TCS/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert len(data["documents"]) > 0
