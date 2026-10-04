-- ==============================================================================
-- N100 Financial Intelligence Platform - SQLite Database Schema
-- ==============================================================================

-- 1. Companies Master Table
DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS sectors;
DROP TABLE IF EXISTS prosandcons;
DROP TABLE IF EXISTS profitandloss;
DROP TABLE IF EXISTS peer_groups;
DROP TABLE IF EXISTS market_cap;
DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS cashflow;
DROP TABLE IF EXISTS balancesheet;
DROP TABLE IF EXISTS analysis;
DROP TABLE IF EXISTS companies;

CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

-- 2. Analysis Table
CREATE TABLE analysis (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    compounded_sales_growth REAL,
    compounded_profit_growth REAL,
    stock_price_cagr REAL,
    roe REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 3. Balance Sheet Table
CREATE TABLE balancesheet (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    year INTEGER,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 4. Cash Flow Table
CREATE TABLE cashflow (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    year INTEGER,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 5. Documents Table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    year INTEGER,
    annual_report TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 6. Financial Ratios Table
CREATE TABLE financial_ratios (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    year INTEGER,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    revenue_cagr_5yr REAL,
    pat_cagr_5yr REAL,
    eps_cagr_5yr REAL,
    composite_quality_score REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 7. Market Cap & Valuation Table
CREATE TABLE market_cap (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    year INTEGER,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 8. Peer Groups Table
CREATE TABLE peer_groups (
    id INTEGER PRIMARY KEY,
    peer_group_name TEXT,
    company_id TEXT,
    is_benchmark BOOLEAN,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 9. Profit & Loss Table
CREATE TABLE profitandloss (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    year INTEGER,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 10. Pros and Cons Table
CREATE TABLE prosandcons (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 11. Sectors Table
CREATE TABLE sectors (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 12. Stock Prices Table
CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    date TEXT,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 13. Peer Percentiles Table
CREATE TABLE peer_percentiles (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    peer_group_name TEXT,
    metric TEXT,
    value REAL,
    percentile_rank REAL,
    year INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Indexes for optimal querying
CREATE INDEX idx_balancesheet_comp_yr ON balancesheet(company_id, year);
CREATE INDEX idx_cashflow_comp_yr ON cashflow(company_id, year);
CREATE INDEX idx_documents_comp_yr ON documents(company_id, year);
CREATE INDEX idx_financial_ratios_comp_yr ON financial_ratios(company_id, year);
CREATE INDEX idx_market_cap_comp_yr ON market_cap(company_id, year);
CREATE INDEX idx_profitandloss_comp_yr ON profitandloss(company_id, year);
CREATE INDEX idx_stock_prices_comp_dt ON stock_prices(company_id, date);
CREATE INDEX idx_sectors_broad ON sectors(broad_sector);
CREATE INDEX idx_peer_percentiles_comp_yr ON peer_percentiles(company_id, peer_group_name, metric, year);

