# N100 Intelligence Platform — Performance Benchmarks & QA Notes

## 1. Concurrent Screener Load Test (Day 43)
- **Target SLA**: 10 concurrent requests completed within 10.0 seconds.
- **Concurrent Workers**: 10 threads
- **Total Elapsed Time**: **0.115 seconds** (✅ PASSED SLA)
- **Average API Response Latency**: **87.14 ms**
- **Min / Max Latency**: 72.23 ms / 111.36 ms

## 2. Company Profile Load Latencies (5 Representative Tickers)
- **Target SLA**: Under 3.0 seconds per profile.

| Ticker | Latency (ms) | Status Code | Within 3s SLA |
|---|:---:|:---:|:---:|
| **TCS** | 7.04 ms | 200 | ✅ YES |
| **HDFCBANK** | 4.37 ms | 200 | ✅ YES |
| **RELIANCE** | 4.77 ms | 200 | ✅ YES |
| **INFY** | 7.99 ms | 200 | ✅ YES |
| **SUNPHARMA** | 6.95 ms | 200 | ✅ YES |

## 3. SQLite Database Index Optimizations
The following B-Tree compound indexes were created on `nifty100.db` to accelerate time-series queries and sector aggregations:
- `CREATE INDEX IF NOT EXISTS idx_ratios_cid_yr ON financial_ratios(company_id, year)`
- `CREATE INDEX IF NOT EXISTS idx_pnl_cid_yr ON profitandloss(company_id, year)`
- `CREATE INDEX IF NOT EXISTS idx_bs_cid_yr ON balancesheet(company_id, year)`
- `CREATE INDEX IF NOT EXISTS idx_cf_cid_yr ON cashflow(company_id, year)`
- `CREATE INDEX IF NOT EXISTS idx_mc_cid_yr ON market_cap(company_id, year)`
- `CREATE INDEX IF NOT EXISTS idx_sec_cid ON sectors(company_id)`
- `CREATE INDEX IF NOT EXISTS idx_pg_group ON peer_groups(peer_group_name)`
- `CREATE INDEX IF NOT EXISTS idx_pp_group ON peer_percentiles(peer_group_name)`
- `CREATE INDEX IF NOT EXISTS idx_docs_cid_yr ON documents(company_id, year)`

## 4. End-to-End Architecture Verification
- **FastAPI REST Service**: Running on port `8000` with 16 active endpoints and OpenAPI `/docs`.
- **Streamlit Web Dashboard**: Running on port `8501` with 8 interactive pages.
- **Port Conflict Analysis**: Zero port collisions; independent async I/O event loops.
