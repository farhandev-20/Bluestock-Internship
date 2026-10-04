# N100 Financial Intelligence Platform

An institutional-grade equity analytics, machine learning clustering, automated report generation, and high-performance REST API platform for the **NIFTY 100** universe.

---

## 🚀 Quickstart & Server Launch Instructions

### 1. Environment Setup
```bash
# Clone the repository
git clone <repo-url>
cd N100_Project

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install project dependencies
pip install -r requirements.txt
```

### 2. Launch the FastAPI REST Service (Port 8000)
```bash
uvicorn src.api.main:app --port 8000
```
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Endpoint**: `http://localhost:8000/api/v1/health`

### 3. Launch the Streamlit Interactive Dashboard (Port 8501)
```bash
streamlit run src/dashboard/app.py
```
- **Live Web Dashboard**: `http://localhost:8501`

---

## ⚡ FastAPI REST API Reference (16 Endpoints)

All endpoints are mounted under the `/api/v1` prefix with CORS and sub-millisecond request logging:

| Category | Method & Path | Query Parameters / Payload | Description |
|---|---|---|---|
| **System** | `GET /api/v1/health` | None | Service status, uptime, and row counts across all 10 tables. |
| **Companies** | `GET /api/v1/companies` | `sector`, `market_cap_category`, `search` | List all 92 constituents with sector and return metrics. |
| **Companies** | `GET /api/v1/companies/{ticker}` | None | Full profile, executive summary, sector, and latest year KPIs. |
| **Financials** | `GET /api/v1/companies/{ticker}/pl` | `from_year`, `to_year` | 10-year historical Profit & Loss statements. |
| **Financials** | `GET /api/v1/companies/{ticker}/bs` | `from_year`, `to_year` | 10-year historical Balance Sheet statements. |
| **Financials** | `GET /api/v1/companies/{ticker}/cashflow`| `from_year`, `to_year` | 10-year historical Cash Flow statements (CFO, CFI, CFF). |
| **Financials** | `GET /api/v1/companies/{ticker}/ratios` | `year` (optional) | Multi-period computed KPIs and ratio engine records. |
| **Documents** | `GET /api/v1/companies/{ticker}/tearsheet`| None | Binary download of 2-page institutional PDF factsheet. |
| **Documents** | `GET /api/v1/companies/{ticker}/documents`| None | BSE annual report URLs with `is_url_valid` connectivity flag. |
| **Screener** | `GET /api/v1/screener` | `min_roe`, `max_de`, `min_fcf`, `sector`, `min_rev_cagr_5yr`, `min_pat_cagr_5yr`, `max_pe` | Multi-metric fundamental filter ranked by composite score. |
| **Sectors** | `GET /api/v1/sectors` | None | Aggregate summary and median KPIs for all 11 sectors. |
| **Sectors** | `GET /api/v1/sectors/{sector}/companies` | None | All constituent companies within the specified sector. |
| **Peers** | `GET /api/v1/peers/{group_name}` | None | Peer group constituents with 10-metric percentile rankings. |
| **Peers** | `GET /api/v1/companies/{ticker}/peers/compare`| None | 8-axis radar comparison data (Company vs Peer Avg vs Benchmark). |
| **Valuation** | `GET /api/v1/market-cap/{ticker}` | None | Historical valuation multiples (P/E, P/B, EV/EBITDA, Div Yield). |
| **Valuation** | `GET /api/v1/valuation/summary` | `flag` (`Caution`/`Discount`/`Fair`) | Valuation multiples, sector median benchmark, and mispricing flags. |
| **Portfolio** | `GET /api/v1/portfolio/stats` | None | P10, P25, P50, P75, P90, Mean, and Std for 10 core KPIs. |

---

## 🤖 Machine Learning Clustering & Statistical Analytics

1. **KMeans Clustering (5 Archetypes)**:
   - **Features**: `return_on_equity_pct`, `debt_to_equity`, `revenue_cagr_5yr`, `fcf_cagr_5yr`, `operating_profit_margin_pct`.
   - **Preprocessing**: Missing values imputed using sector medians; standardized via `StandardScaler`.
   - **Reproducibility**: $k=5$, `random_state=42`.
   - **Generated Outputs**:
     - `output/cluster_labels.csv`: 92 companies assigned to 5 labelled clusters with centroid Euclidean distances.
     - `reports/elbow_plot.png`: Inertia vs $k$ ($k=2 \dots 10$) confirming optimal $k=5$.
2. **Correlation Heatmap & Outlier Detection**:
   - `reports/correlation_heatmap.png`: Pearson correlation matrix of 10 financial KPIs.
   - `output/outlier_report.csv`: Statistical anomalies with $|Z\text{-score}| > 3$ within broad sector cohorts.
   - `output/portfolio_stats.csv`: Percentile distributions across the 92-company universe.

---

## 📑 Core Deliverables Inventory (23 Artifacts)

| Deliverable Name | File Path | Format / Size | Description |
|---|---|---|---|
| **Cluster Labels** | `output/cluster_labels.csv` | CSV (92 rows) | KMeans cluster assignment and distance from centroid |
| **Elbow Plot** | `reports/elbow_plot.png` | PNG (160 DPI) | Elbow inertia curve confirming $k=5$ |
| **Correlation Heatmap** | `reports/correlation_heatmap.png`| PNG (160 DPI) | Seaborn Pearson correlation matrix of 10 KPIs |
| **Outlier Report** | `output/outlier_report.csv` | CSV | Companies with $|Z\text{-score}| > 3$ within sector |
| **Portfolio Stats** | `output/portfolio_stats.csv` | CSV (10 KPIs) | P10 to P90 percentile distribution table |
| **REST API Engine** | `src/api/` | Python Package | 16 FastAPI REST endpoints with CORS & middleware |
| **OpenAPI Schema** | `docs/openapi.json` | JSON Schema | OpenAPI 3.0 specification |
| **Postman Collection**| `docs/postman_collection.json`| JSON Collection | Complete Postman integration collection |
| **PyTest HTML Report**| `reports/pytest_report.html` | HTML (Interactive)| Complete test suite execution evidence |
| **Analyst Guide** | `docs/analyst_guide.pdf` | PDF (10 Pages) | Comprehensive 10-page user & developer guide |
| **Acceptance Checklist**| `docs/acceptance_checklist.pdf` | PDF (Day 45) | Verification checklist for all 20 Acceptance Gates |
| **NLP Pros & Cons** | `output/pros_cons_generated.csv` | CSV (591 rows) | 12 Pro & 12 Con rules with confidence scores |
| **Parsed CAGRs** | `output/analysis_parsed.csv` | CSV (80 rows) | Regex parsed CAGR metrics from `analysis.xlsx` |
| **Cash Flow Intel** | `output/cashflow_intelligence.xlsx`| Excel (2 Sheets)| CFO Quality, CapEx Intensity & Pattern distribution |
| **Distress Alerts** | `output/distress_alerts.csv` | CSV (13 rows) | Companies raising financing while CFO is negative |
| **Pattern Changes** | `output/pattern_changes.csv` | CSV (35 rows) | Capital allocation YoY archetype transitions |
| **Valuation Summary**| `output/valuation_summary.xlsx` | Excel (92 rows) | FCF yields, sector median P/E, and caution flags |
| **Valuation Flags** | `output/valuation_flags.csv` | CSV | Filtered list of Caution / Discount flagged equities |
| **Screener Output** | `output/screener_output.xlsx` | Excel (Formatted) | Winsorised composite quality rankings |
| **Peer Comparison** | `output/peer_comparison.xlsx` | Excel | 11 specialized peer group comparison matrices |
| **Data Quality Audit**| `output/validation_failures.csv`| CSV | 16 DQ rules audit failure log |
| **Company Tearsheets**| `reports/tearsheets/*.pdf` | PDF (92 Files) | 2-page institutional company tearsheets |
| **Sector Reports** | `reports/sector/*.pdf` | PDF (11 Files) | Sector median KPI benchmarks and constituent tables |

---

## 🧪 Verification & Acceptance Gates (100% PASS)

All **20 Acceptance Gates (AC-01 through AC-20)** and **237 automated pytest unit/integration tests** pass with 0 failures:
```bash
pytest --html=reports/pytest_report.html --self-contained-html
```
```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
collected 237 items

tests/api/test_companies.py ........                                     [  3%]
tests/api/test_health.py .                                               [  3%]
tests/api/test_screener.py .....                                         [  5%]
tests/api/test_sectors.py ........                                       [  9%]
tests/dashboard/test_dashboard_integration.py .....................      [ 18%]
tests/dq/test_rules.py ..............                                    [ 24%]
tests/etl/test_database.py ....                                          [ 25%]
tests/etl/test_loader.py .................                               [ 32%]
tests/etl/test_normalise.py ....................                         [ 41%]
tests/etl/test_normalizer.py .................                           [ 48%]
tests/etl/test_pipeline.py ..                                            [ 49%]
tests/etl/test_validator.py ..................                           [ 56%]
tests/kpi/test_cagr.py ..........                                        [ 61%]
tests/kpi/test_cashflow_intelligence.py ...                              [ 62%]
tests/kpi/test_cashflow_kpis.py .....                                    [ 64%]
tests/kpi/test_leverage_ratios.py .........                              [ 68%]
tests/kpi/test_profitability_ratios.py ..........                        [ 72%]
tests/kpi/test_ratio_engine.py .....                                     [ 74%]
tests/kpi/test_ratios.py ....................                            [ 83%]
tests/nlp/test_parser.py ...                                             [ 84%]
tests/nlp/test_pros_cons.py ..                                           [ 85%]
tests/peer/test_peer_comparison.py ..                                    [ 86%]
tests/peer/test_peer_percentiles.py .....                                [ 88%]
tests/peer/test_radar_charts.py .                                        [ 88%]
tests/reports/test_reports.py .....                                      [ 90%]
tests/screener/test_composite_score.py ..                                [ 91%]
tests/screener/test_filter_engine.py ....                                [ 93%]
tests/screener/test_presets.py .......                                   [ 96%]
tests/valuation/test_valuation.py .........                              [100%]

======================= 237 passed, 1 warning in 30.95s =======================
```
