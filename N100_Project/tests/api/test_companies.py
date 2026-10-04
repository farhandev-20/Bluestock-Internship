"""
Unit and Integration Tests for FastAPI Company Endpoints (Day 42).
"""

from fastapi.testclient import TestClient
import pytest
from src.api.main import app

client = TestClient(app)


def test_list_companies():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 92
    assert len(data["companies"]) == 92
    first = data["companies"][0]
    assert "id" in first
    assert "company_name" in first
    assert "broad_sector" in first


def test_get_company_profile_valid():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert "Tata Consultancy" in data["company_name"]
    assert "sector" in data
    assert "latest_financials" in data
    assert "return_on_equity_pct" in data["latest_financials"]


def test_get_company_profile_invalid_404():
    response = client.get("/api/v1/companies/INVALID_TICKER_XYZ")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_company_pl_statement():
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert len(data["profit_and_loss"]) >= 10


def test_get_company_bs_statement():
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert len(data["balance_sheet"]) >= 10


def test_get_company_cashflow_statement():
    response = client.get("/api/v1/companies/TCS/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert len(data["cash_flow"]) >= 10


def test_get_company_ratios():
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert len(data["ratios"]) >= 10


def test_get_company_tearsheet_pdf_download():
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) >= 30 * 1024  # At least 30 KB
