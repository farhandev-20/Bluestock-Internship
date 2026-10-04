Bluestock Mutual Fund Analytics Capstone

1. Project Overview

Bluestock Mutual Fund Analytics is an end-to-end data analytics project for exploring mutual fund performance, risk, investor behavior, SIP trends and fund recommendations.

The project converts raw CSV datasets into cleaned analytical data, stores structured data in SQLite, calculates performance and risk metrics with Python, performs advanced analytics, and presents business insights through an interactive Power BI dashboard.

Main objectives

Build a reusable ETL pipeline.

Clean and validate mutual fund datasets.

Store analytical data in a relational SQLite database.

Perform exploratory data analysis (EDA).

Calculate performance and risk metrics.

Analyze investor cohort retention.

Generate a rule-based fund recommendation score.

Build an interactive four-page Power BI dashboard.

Provide reproducible documentation and deliverables.

2. Project Structure

bluestock_mf_capstone/
│
├── README.md
│
├── data/
│   ├── raw/                  # Original source CSV files
│   ├── processed/            # Cleaned and calculated datasets
│   └── db/                   # Local SQLite database files
│
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
│
├── scripts/
│   ├── etl_pipeline.py
│   ├── live_nav_fetch.py
│   ├── compute_metrics.py
│   ├── recommender.py
│   ├── run_pipeline.py
│   ├── load_database.py
│   └── verify_database.py
│
├── sql/
│   ├── schema.sql
│   └── queries.sql
│
├── dashboard/
│   └── bluestock_mf_capstone.pbix
│
└── reports/
    ├── Final_Report.pdf
    └── Presentation.pptx

3. Technologies Used

Python 3

Pandas

NumPy

Matplotlib

Seaborn

Requests

Jupyter Notebook

SQLite

SQL

Power BI Desktop

Git and GitHub

4. Dataset Description

The project uses multiple datasets covering mutual fund, market and investor information.

Dataset

Description

fund_master.csv

Fund scheme master data, category, fund house, benchmark, expense ratio, risk category and other scheme attributes

nav_history.csv

Historical NAV observations by AMFI scheme code and date

scheme_performance.csv

Scheme returns, benchmark return, alpha, beta, Sharpe, Sortino, volatility, drawdown, AUM and ratings

benchmark_indices.csv

Historical benchmark index values

aum_by_fund_house.csv

AUM and scheme counts by fund house and date

monthly_sip_inflows.csv

Monthly SIP inflows, active SIP accounts, new accounts, SIP AUM and YoY growth

category_inflows.csv

Monthly net inflows by mutual fund category

industry_folio_count.csv

Industry-level folio counts across equity, debt, hybrid and other segments

portfolio_holdings.csv

Scheme portfolio holdings, sectors, weights, market values and prices

investor_transactions.csv

Investor transaction activity, amount, location, demographics, payment mode and KYC status

Live NAV CSVs

Current/latest NAV data fetched for selected schemes using MFAPI

5. Setup Instructions

Step 1 — Clone the repository

git clone https://github.com/farhandev-20/mutual-fund-analytics.git
cd mutual-fund-analytics

Step 2 — Create a virtual environment (recommended)

Windows:

python -m venv .venv
.venv\Scripts\activate

Step 3 — Install dependencies

python -m pip install -r requirements.txt

If python is not recognized on Windows, use:

py -m pip install -r requirements.txt

6. How to Run the ETL and Analytics Pipeline

The master execution script is:

scripts/run_pipeline.py

Run it from the project root:

python scripts/run_pipeline.py

Windows alternative:

py scripts/run_pipeline.py

The master script executes the main workflow in sequence:

etl_pipeline.py — cleans and processes CSV files.

live_nav_fetch.py — fetches latest NAV data for selected schemes.

compute_metrics.py — calculates performance and risk metrics.

recommender.py — generates the fund recommendation output.

Generated/updated analytical files are stored in:

data/processed/

Expected successful pipeline output

ETL completed successfully
Live NAV fetch completed
Performance metrics completed
Recommendation model completed
Master pipeline completed successfully

7. ETL Design

The ETL pipeline uses project-relative paths based on the location of the Python script. This avoids machine-specific hard-coded paths.

The workflow performs:

CSV discovery from data/raw

Removal of completely empty rows and columns

Removal of exact duplicate records

Standardization of column names to lowercase snake_case

Whitespace cleanup for text fields

Writing cleaned datasets to data/processed

Error handling for individual processing failures

8. Data Cleaning

The data-cleaning notebook is:

notebooks/02_data_cleaning.ipynb

Validation includes:

Missing-value checks

Duplicate checks

Data-type checks

Numeric range checks

Date conversion and validation

AMFI-code consistency checks

Meaningful missing values are not blindly replaced. For example, missing yoy_growth_pct observations in the SIP dataset are retained when the underlying value is unavailable.

9. SQLite Database

The database schema is defined in:

sql/schema.sql

The database contains tables for:

Fund master

NAV history

AUM by fund house

Monthly SIP inflows

Category inflows

Industry folio counts

Scheme performance

Portfolio holdings

Investor transactions

Benchmark indices

AMFI codes are used to connect dependent datasets to the fund master where appropriate.

Database scripts

Create/load the database:

python scripts/load_database.py

Verify the database:

python scripts/verify_database.py

The SQLite database is intended to remain local and is excluded from Git tracking through .gitignore.

10. Exploratory Data Analysis

The EDA notebook is:

notebooks/03_eda_analysis.ipynb

Key analyses include:

AUM by fund house

Monthly SIP inflow trends

Category-wise inflows

Top schemes by 3-year return

NAV trends

Correlation analysis

11. Performance and Risk Analytics

The performance notebook is:

notebooks/04_performance_analytics.ipynb

Metrics include:

CAGR

CAGR is calculated using the actual elapsed time between observations rather than blindly assuming a fixed 252-day investment period.

Annualized volatility

Daily return volatility is annualized using:

daily standard deviation × √252

Maximum drawdown

Maximum drawdown measures the largest peak-to-trough decline in the NAV return series.

Historical 95% daily VaR

Historical Value at Risk is calculated from the empirical daily-return distribution. The output uses a positive loss convention for easier interpretation.

Beta

Beta is calculated by aligning fund returns with a benchmark return series. The project uses NIFTY100 when available.

Sharpe ratio

Sharpe ratio is calculated from daily returns and annualized. Because a separate risk-free-rate series was not supplied, the analysis uses a zero risk-free-rate assumption.

12. Advanced Analytics

The advanced analytics notebook is:

notebooks/05_advanced_analytics.ipynb

Cohort retention analysis

Investors are grouped according to their first transaction month. Subsequent transaction activity is measured by months since the cohort's first transaction.

The output is saved as:

data/processed/cohort_retention.csv

Recommendation model

The recommender uses a rank-based weighted score:

Metric

Weight

3-year return

30%

Sharpe ratio

25%

Volatility

20%

Maximum drawdown

15%

Expense ratio

10%

Higher return and Sharpe scores are preferred. Lower volatility, drawdown magnitude and expense ratio are preferred.

Output:

data/processed/fund_recommendations.csv

This is an analytical ranking model, not personalized financial advice.

13. Power BI Dashboard

Power BI dashboard file:

dashboard/bluestock_mf_capstone.pbix

Open it using Power BI Desktop.

The dashboard contains four pages:

Page 1 — Executive Overview

Provides a high-level view of:

Total funds

Average 3-year return

Average Sharpe ratio

AUM by fund house

Top schemes by return

Interactive filters

Page 2 — Fund Performance & Risk

Includes:

3-year return comparison

Sharpe ratio comparison

Risk/return scatter analysis

Maximum drawdown

Category and risk filters

Page 3 — Investor & SIP Analytics

Includes:

SIP inflow trend

Transaction-type analysis

Investor distribution by city tier

YoY SIP growth

Investor filters

Page 4 — Advanced Analytics

Includes:

Fund recommendation analysis

VaR analysis

Cohort retention analysis

Sharpe ratio vs 3-year return analysis

Interactive analytical filters

14. Project Deliverables

The final project contains:

README.md

Python ETL and analytics scripts

Five Jupyter notebooks

SQLite schema and SQL queries

Processed analytical datasets

Power BI dashboard

Final_Report.pdf

Presentation.pptx

15. GitHub

Repository:

https://github.com/farhandev-20/mutual-fund-analytics

The project is maintained using Git. The SQLite database is excluded from version control because it is a generated/local database artifact.

16. Limitations

Historical analysis depends on the supplied datasets and their available time periods.

Historical VaR does not guarantee future loss estimates.

Sharpe ratio uses a zero risk-free-rate assumption because no risk-free series was supplied.

Cohort retention measures observed transaction activity, not investor profitability.

The recommendation model is rule-based and should not be interpreted as personalized investment advice.

Live NAV availability depends on the external MFAPI service and its response data.

17. Future Enhancements

Possible extensions include:

Scheduled/cron-based pipeline execution

Streamlit analytics application

Monte Carlo simulation

Markowitz portfolio optimization

Automated email reporting

Power BI Service deployment

Automated data-quality alerts

18. Conclusion

The Bluestock Mutual Fund Analytics Capstone provides a complete workflow from raw data ingestion to analytical reporting.

It combines data engineering, database management, exploratory analysis, performance and risk measurement, investor cohort analysis, recommendation logic and interactive business intelligence in a single reproducible project.