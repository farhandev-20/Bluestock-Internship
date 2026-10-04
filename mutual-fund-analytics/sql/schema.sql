PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS fund_master (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT,
    scheme_name TEXT,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount REAL,
    min_lumpsum_amount REAL,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE IF NOT EXISTS nav_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    date TEXT NOT NULL,
    nav REAL,
    FOREIGN KEY (amfi_code) REFERENCES fund_master(amfi_code)
);

CREATE INDEX IF NOT EXISTS idx_nav_amfi_code
ON nav_history(amfi_code);

CREATE TABLE IF NOT EXISTS aum_by_fund_house (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    fund_house TEXT,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER
);

CREATE TABLE IF NOT EXISTS monthly_sip_inflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT,
    sip_inflow_crore REAL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL
);

CREATE TABLE IF NOT EXISTS category_inflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT,
    category TEXT,
    net_inflow_crore REAL
);

CREATE TABLE IF NOT EXISTS industry_folio_count (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT,
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);

CREATE TABLE IF NOT EXISTS scheme_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    scheme_name TEXT,
    fund_house TEXT,
    category TEXT,
    plan TEXT,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT,
    FOREIGN KEY (amfi_code) REFERENCES fund_master(amfi_code)
);

CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    stock_symbol TEXT,
    stock_name TEXT,
    sector TEXT,
    weight_pct REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date TEXT,
    FOREIGN KEY (amfi_code) REFERENCES fund_master(amfi_code)
);

CREATE TABLE IF NOT EXISTS investor_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT,
    transaction_date TEXT,
    amfi_code INTEGER,
    transaction_type TEXT,
    amount_inr REAL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES fund_master(amfi_code)
);

CREATE TABLE IF NOT EXISTS benchmark_indices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    index_name TEXT,
    close_value REAL
);