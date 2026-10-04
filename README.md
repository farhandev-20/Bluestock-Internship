# Bluestock Fintech Engineering & Analytics Internship

This repository houses the core projects, analytics pipelines, automated reporting engines, and REST APIs built during the **Bluestock Internship**.

---

## 📂 Project Directory Structure

```text
Bluestock-Internship/
├── N100_Project/                 # NIFTY 100 Financial Intelligence & Analytics Platform
│   ├── config/                  # Screener YAML rules and weight definitions
│   ├── Data/                    # Raw SQLite database and financial sources
│   ├── db/                      # Schema definition (12 relational tables + indexes)
│   ├── docs/                    # OpenAPI specs, Postman collections, Analyst Guide PDF
│   ├── output/                  # Analytics exports (CAGR, cash flow, clusters, flags)
│   ├── pages/                   # Streamlit multi-page dashboard views
│   ├── reports/                 # 92 Institutional Company Tearsheets & 11 Sector Reports
│   ├── src/                     # Core Python engine (ETL, Analytics, Screener, NLP, API)
│   ├── tests/                   # Automated Pytest validation suite (237 test cases)
│   ├── Makefile                 # One-click execution targets
│   └── README.md                # Detailed platform documentation
│
└── mutual-fund-analytics/       # Mutual Fund Analytics, NAV Prediction & Portfolio Engine
    ├── dashboard/               # Streamlit analytics interface
    ├── data/                    # Cleaned and raw NAV, AUM, and holdings data
    ├── notebooks/               # Exploratory data analysis and modeling notebooks
    ├── reports/                 # Quality reports and presentations
    ├── scripts/                 # Ingestion, validation, and recommendation pipelines
    ├── sql/                     # PostgreSQL / SQLite query scripts and schema
    └── README.md                # Mutual fund platform guide
```

---

## 🚀 Projects Overview

### 1. NIFTY 100 Financial Intelligence Platform (`/N100_Project`)
An institutional-grade equity research and financial analytics platform analyzing **92 Nifty 100 companies** across a 10-year historical horizon.

* **Complete ETL Pipeline**: Automated ingestion, currency normalization (Cr), and 16 Data Quality validation gates.
* **KPI Engine**: Calculation of 10-year profitability, leverage, cash flow quality ratios, CAGR metrics, and Cash Flow Archetypes.
* **K-Means Clustering & Peer Analytics**: Unsupervised $k=5$ peer cohort clustering, radar charts, and percentiles.
* **Valuation & Screening**: Multi-metric composite quality scoring and pre-configured investment strategy presets.
* **Institutional Deliverables**: 92 two-page company PDF tearsheets, 11 sector PDF benchmarks, and 10-page Analyst Guide.
* **FastAPI Backend & Streamlit Dashboard**: 16 REST endpoints with OpenAPI specs and 8-screen dark-mode analytics terminal.
* **100% Test Coverage**: 237 automated Pytest unit and integration tests passing with 0 failures.

👉 Explore: [`N100_Project/README.md`](./N100_Project/README.md)

---

### 2. Mutual Fund Analytics & Portfolio Engine (`/mutual-fund-analytics`)
A comprehensive mutual fund tracking, risk-adjusted performance evaluation, and portfolio recommendation system.

* **Data Ingestion & Live NAV Fetching**: Automated daily NAV updates and historical transaction processing.
* **Fund Master Validation & AUM Tracking**: Folio distribution, category inflows, and fund house analytics.
* **Risk-Adjusted Performance**: Sharpe, Sortino, Alpha, Beta calculation vs Benchmark indices.
* **Interactive Terminal**: Streamlit-based fund comparison, SIP calculator, and recommendation engine.

👉 Explore: [`mutual-fund-analytics/README.md`](./mutual-fund-analytics/README.md)

---

## 🛠️ Tech Stack

* **Languages**: Python 3.10+, SQL
* **Data Processing & Analytics**: Pandas, NumPy, Scikit-Learn, SciPy, OpenPyXL
* **Visualization & Reporting**: Matplotlib, Seaborn, Plotly, ReportLab
* **Web & API Frameworks**: FastAPI, Uvicorn, Streamlit
* **Quality Assurance**: PyTest, PyTest-HTML, Pydantic, GitHub Actions

---

## 👨‍💻 Author

**Farhan Attar**  
GitHub: [@farhandev-20](https://github.com/farhandev-20)
