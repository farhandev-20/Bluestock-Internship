-- Bluestock Mutual Fund Analytics
-- SQL Analysis Queries

-- 1. Display all funds
SELECT * 
FROM fund_master;

-- 2. Count total mutual fund schemes
SELECT COUNT(*) AS total_schemes
FROM fund_master;

-- 3. Funds by category
SELECT category, COUNT(*) AS scheme_count
FROM fund_master
GROUP BY category
ORDER BY scheme_count DESC;

-- 4. Top 10 schemes by 3-year return
SELECT scheme_name, fund_house, category, return_3yr_pct
FROM scheme_performance
ORDER BY return_3yr_pct DESC
LIMIT 10;

-- 5. Top 10 schemes by Sharpe ratio
SELECT scheme_name, fund_house, sharpe_ratio
FROM scheme_performance
ORDER BY sharpe_ratio DESC
LIMIT 10;

-- 6. Lowest expense ratio funds
SELECT scheme_name, fund_house, expense_ratio_pct
FROM scheme_performance
ORDER BY expense_ratio_pct ASC
LIMIT 10;

-- 7. Highest AUM schemes
SELECT scheme_name, fund_house, aum_crore
FROM scheme_performance
ORDER BY aum_crore DESC
LIMIT 10;

-- 8. Average return by category
SELECT category,
       AVG(return_1yr_pct) AS avg_1yr_return,
       AVG(return_3yr_pct) AS avg_3yr_return,
       AVG(return_5yr_pct) AS avg_5yr_return
FROM scheme_performance
GROUP BY category
ORDER BY avg_3yr_return DESC;

-- 9. Average risk metrics by category
SELECT category,
       AVG(std_dev_ann_pct) AS avg_volatility,
       AVG(max_drawdown_pct) AS avg_drawdown,
       AVG(sharpe_ratio) AS avg_sharpe
FROM scheme_performance
GROUP BY category
ORDER BY avg_sharpe DESC;

-- 10. SIP inflow trend
SELECT month, sip_inflow_crore, yoy_growth_pct
FROM monthly_sip_inflows
ORDER BY month;

-- 11. Total category-wise net inflow
SELECT category,
       SUM(net_inflow_crore) AS total_net_inflow
FROM category_inflows
GROUP BY category
ORDER BY total_net_inflow DESC;

-- 12. Fund-house AUM
SELECT fund_house,
       SUM(aum_crore) AS total_aum_crore
FROM aum_by_fund_house
GROUP BY fund_house
ORDER BY total_aum_crore DESC;

-- 13. Transaction type summary
SELECT transaction_type,
       COUNT(*) AS transaction_count,
       SUM(amount_inr) AS total_amount_inr
FROM investor_transactions
GROUP BY transaction_type
ORDER BY total_amount_inr DESC;

-- 14. Investor count by state
SELECT state,
       COUNT(DISTINCT investor_id) AS investor_count
FROM investor_transactions
GROUP BY state
ORDER BY investor_count DESC;

-- 15. Investor count by city tier
SELECT city_tier,
       COUNT(DISTINCT investor_id) AS investor_count
FROM investor_transactions
GROUP BY city_tier
ORDER BY investor_count DESC;

-- 16. Portfolio holdings by sector
SELECT sector,
       SUM(weight_pct) AS total_weight_pct,
       SUM(market_value_cr) AS total_market_value_cr
FROM portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC;