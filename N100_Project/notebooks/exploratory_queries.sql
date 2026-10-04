-- ==============================================================================
-- N100 Financial Intelligence Platform - Exploratory SQL Queries
-- Database: nifty100.db
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Table Row Counts Overview
-- ------------------------------------------------------------------------------
SELECT 'companies' AS table_name, COUNT(*) AS total_rows FROM companies
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices;

-- ------------------------------------------------------------------------------
-- 2. Top 10 Companies by Market Capitalization (Latest Year)
-- ------------------------------------------------------------------------------
SELECT 
    c.id AS ticker,
    c.company_name,
    s.broad_sector,
    m.year,
    m.market_cap_crore,
    m.enterprise_value_crore,
    m.pe_ratio,
    m.pb_ratio
FROM market_cap m
JOIN companies c ON m.company_id = c.id
LEFT JOIN sectors s ON c.id = s.company_id
WHERE m.year = (SELECT MAX(year) FROM market_cap)
ORDER BY m.market_cap_crore DESC
LIMIT 10;

-- ------------------------------------------------------------------------------
-- 3. Sector Distribution and Cumulative Index Weights
-- ------------------------------------------------------------------------------
SELECT 
    broad_sector,
    COUNT(company_id) AS company_count,
    ROUND(SUM(index_weight_pct), 2) AS total_sector_weight_pct,
    ROUND(AVG(index_weight_pct), 2) AS avg_stock_weight_pct
FROM sectors
GROUP BY broad_sector
ORDER BY total_sector_weight_pct DESC;

-- ------------------------------------------------------------------------------
-- 4. Profitability Leaders: Top Companies by ROE & ROCE
-- ------------------------------------------------------------------------------
SELECT 
    id AS ticker,
    company_name,
    roe_percentage,
    roce_percentage,
    book_value,
    face_value
FROM companies
WHERE roe_percentage IS NOT NULL
ORDER BY roe_percentage DESC
LIMIT 10;

-- ------------------------------------------------------------------------------
-- 5. Revenue and Net Profit Growth Trend (Sample Company: ABB)
-- ------------------------------------------------------------------------------
SELECT 
    company_id,
    year,
    sales,
    expenses,
    operating_profit,
    opm_percentage,
    profit_before_tax,
    net_profit,
    eps
FROM profitandloss
WHERE company_id = 'ABB' AND year IS NOT NULL
ORDER BY year ASC;

-- ------------------------------------------------------------------------------
-- 6. Balance Sheet Solvency and Leverage Check
-- ------------------------------------------------------------------------------
SELECT 
    b.company_id,
    b.year,
    b.total_assets,
    b.total_liabilities,
    b.borrowings,
    b.equity_capital + b.reserves AS net_worth,
    ROUND(b.borrowings / NULLIF(b.equity_capital + b.reserves, 0), 2) AS debt_to_equity_calc
FROM balancesheet b
WHERE b.company_id IN ('TCS', 'INFY', 'HDFCBANK', 'RELIANCE', 'ABB')
  AND b.year >= 2020
ORDER BY b.company_id, b.year DESC;

-- ------------------------------------------------------------------------------
-- 7. Cash Flow Quality: Operating vs Net Cash Flow
-- ------------------------------------------------------------------------------
SELECT 
    company_id,
    year,
    operating_activity,
    investing_activity,
    financing_activity,
    net_cash_flow
FROM cashflow
WHERE company_id IN ('TCS', 'INFY', 'ABB')
ORDER BY company_id, year DESC;

-- ------------------------------------------------------------------------------
-- 8. Stock Price Volatility and Trading Summary (2020-2024)
-- ------------------------------------------------------------------------------
SELECT 
    company_id,
    COUNT(date) AS total_trading_periods,
    ROUND(MIN(low_price), 2) AS period_low,
    ROUND(MAX(high_price), 2) AS period_high,
    ROUND(AVG(close_price), 2) AS avg_close,
    ROUND(SUM(volume), 0) AS total_traded_volume
FROM stock_prices
GROUP BY company_id
ORDER BY total_traded_volume DESC
LIMIT 15;

-- ------------------------------------------------------------------------------
-- 9. Peer Group Comparisons & Benchmark Companies
-- ------------------------------------------------------------------------------
SELECT 
    p.peer_group_name,
    p.company_id,
    c.company_name,
    p.is_benchmark,
    s.broad_sector
FROM peer_groups p
LEFT JOIN companies c ON p.company_id = c.id
LEFT JOIN sectors s ON p.company_id = s.company_id
ORDER BY p.peer_group_name, p.is_benchmark DESC, p.company_id;

-- ------------------------------------------------------------------------------
-- 10. Annual Report Filing Coverage Summary
-- ------------------------------------------------------------------------------
SELECT 
    company_id,
    COUNT(year) AS total_reports_filed,
    MIN(year) AS earliest_report_year,
    MAX(year) AS latest_report_year
FROM documents
WHERE annual_report IS NOT NULL
GROUP BY company_id
ORDER BY total_reports_filed DESC
LIMIT 15;
