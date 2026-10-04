import pytest
from pathlib import Path
from src.etl.loader import load_excel, load_all_files, detect_header_row, DATA_DIR


def test_companies_file_loads():
    df = load_excel("companies.xlsx")
    assert len(df) == 92
    assert "id" in df.columns
    assert "company_name" in df.columns


def test_companies_has_id_not_company_id():
    df = load_excel("companies.xlsx")
    assert "id" in df.columns
    assert "company_id" not in df.columns


def test_analysis_file_loads():
    df = load_excel("analysis.xlsx")
    assert len(df) == 20
    assert "company_id" in df.columns


def test_balancesheet_file_loads():
    df = load_excel("balancesheet.xlsx")
    assert len(df) == 1312
    assert "equity_capital" in df.columns
    assert "total_assets" in df.columns


def test_cashflow_file_loads():
    df = load_excel("cashflow.xlsx")
    assert len(df) == 1187
    assert "operating_activity" in df.columns
    assert "net_cash_flow" in df.columns


def test_documents_file_loads():
    df = load_excel("documents.xlsx")
    assert len(df) == 1585
    assert "annual_report" in df.columns


def test_profitandloss_file_loads():
    df = load_excel("profitandloss.xlsx")
    assert len(df) == 1276
    assert "sales" in df.columns
    assert "net_profit" in df.columns


def test_prosandcons_file_loads():
    df = load_excel("prosandcons.xlsx")
    assert len(df) == 16
    assert "pros" in df.columns
    assert "cons" in df.columns


def test_financial_ratios_file_loads():
    df = load_excel("financial_ratios.xlsx")
    assert len(df) == 1184
    assert "net_profit_margin_pct" in df.columns
    assert "year" in df.columns


def test_market_cap_file_loads():
    df = load_excel("market_cap.xlsx")
    assert len(df) == 552
    assert "market_cap_crore" in df.columns
    assert "pe_ratio" in df.columns


def test_peer_groups_file_loads():
    df = load_excel("peer_groups.xlsx")
    assert len(df) == 56
    assert "peer_group_name" in df.columns
    assert "is_benchmark" in df.columns


def test_sectors_file_loads():
    df = load_excel("sectors.xlsx")
    assert len(df) == 92
    assert "broad_sector" in df.columns
    assert "index_weight_pct" in df.columns


def test_stock_prices_file_loads():
    df = load_excel("stock_prices.xlsx")
    assert len(df) == 5520
    assert "date" in df.columns
    assert "close_price" in df.columns


def test_all_twelve_files_raw_load():
    datasets = load_all_files(seed_missing_parents=False)
    assert len(datasets) == 12
    total_rows = sum(len(df) for df in datasets.values())
    assert total_rows == 12892


def test_all_twelve_files_seeded_load():
    datasets = load_all_files(seed_missing_parents=True)
    assert len(datasets) == 12
    assert len(datasets["companies"]) == 100
    total_rows = sum(len(df) for df in datasets.values())
    assert total_rows == 12900


def test_detect_header_row():
    assert detect_header_row("companies.xlsx") == 1
    assert detect_header_row("balancesheet.xlsx") == 1
    assert detect_header_row("financial_ratios.xlsx") == 0
    assert detect_header_row("stock_prices.xlsx") == 0


def test_load_excel_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_excel("non_existent_dataset.xlsx")