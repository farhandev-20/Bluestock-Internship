"""
Data Quality Validation Engine for N100 Financial Intelligence Platform.
Implements 16 Data Quality (DQ) Rules across all 12 datasets.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import re
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"


@dataclass
class ValidationFailure:
    rule_id: str
    severity: str  # CRITICAL, WARNING, INFO
    table_name: str
    record_id: Any
    column_name: Optional[str]
    invalid_value: Any
    failure_reason: str


@dataclass
class RuleSummary:
    rule_id: str
    rule_name: str
    severity: str
    table_name: str
    total_records: int
    failed_records: int
    status: str
    description: str


class DataQualityValidator:
    """
    Validation engine running 16 Data Quality rules across loaded datasets.
    """

    def __init__(self, datasets: Dict[str, pd.DataFrame]):
        self.datasets = datasets
        self.failures: List[ValidationFailure] = []
        self.rule_summaries: List[RuleSummary] = []
        self.company_ids = set()
        if "companies" in datasets and "id" in datasets["companies"].columns:
            self.company_ids = set(datasets["companies"]["id"].dropna().unique())

    def record_failure(
        self,
        rule_id: str,
        severity: str,
        table_name: str,
        record_id: Any,
        column_name: Optional[str],
        invalid_value: Any,
        failure_reason: str,
    ):
        self.failures.append(
            ValidationFailure(
                rule_id=rule_id,
                severity=severity,
                table_name=table_name,
                record_id=record_id,
                column_name=column_name,
                invalid_value=str(invalid_value),
                failure_reason=failure_reason,
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-01: Primary Key Null Check
    # -------------------------------------------------------------------------
    def validate_dq01_pk_not_null(self):
        rule_id = "DQ-01"
        rule_name = "Primary Key Non-Null Check"
        severity = "CRITICAL"
        total_rows = 0
        total_failed = 0

        for table_name, df in self.datasets.items():
            if "id" not in df.columns:
                continue
            total_rows += len(df)
            null_pks = df[df["id"].isna()]
            failed_count = len(null_pks)
            total_failed += failed_count

            for idx, row in null_pks.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name=table_name,
                    record_id=f"row_{idx}",
                    column_name="id",
                    invalid_value=None,
                    failure_reason="Primary key 'id' is null or empty",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="ALL",
                total_records=total_rows,
                failed_records=total_failed,
                status="PASSED" if total_failed == 0 else "FAILED",
                description="Primary key 'id' must never be null.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-02: Primary Key Uniqueness Check
    # -------------------------------------------------------------------------
    def validate_dq02_pk_uniqueness(self):
        rule_id = "DQ-02"
        rule_name = "Primary Key Uniqueness Check"
        severity = "CRITICAL"
        total_rows = 0
        total_failed = 0

        for table_name, df in self.datasets.items():
            if "id" not in df.columns:
                continue
            total_rows += len(df)
            dup_mask = df["id"].duplicated(keep=False)
            dups = df[dup_mask]
            failed_count = len(dups)
            total_failed += failed_count

            for _, row in dups.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name=table_name,
                    record_id=row["id"],
                    column_name="id",
                    invalid_value=row["id"],
                    failure_reason=f"Duplicate primary key '{row['id']}' found in {table_name}",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="ALL",
                total_records=total_rows,
                failed_records=total_failed,
                status="PASSED" if total_failed == 0 else "FAILED",
                description="Primary key 'id' must be unique in each table.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-03: Foreign Key Referential Integrity
    # -------------------------------------------------------------------------
    def validate_dq03_foreign_key_integrity(self):
        rule_id = "DQ-03"
        rule_name = "Foreign Key Referential Integrity"
        severity = "CRITICAL"
        total_rows = 0
        total_failed = 0

        for table_name, df in self.datasets.items():
            if table_name == "companies" or "company_id" not in df.columns:
                continue
            total_rows += len(df)
            orphans = df[~df["company_id"].isin(self.company_ids)]
            failed_count = len(orphans)
            total_failed += failed_count

            for _, row in orphans.iterrows():
                rec_id = row.get("id", "unknown")
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name=table_name,
                    record_id=rec_id,
                    column_name="company_id",
                    invalid_value=row["company_id"],
                    failure_reason=f"Orphaned company_id '{row['company_id']}' not present in companies master",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="CHILD_TABLES",
                total_records=total_rows,
                failed_records=total_failed,
                status="PASSED" if total_failed == 0 else "FAILED",
                description="All child company_id references must exist in companies master table.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-04: Mandatory Company Attributes
    # -------------------------------------------------------------------------
    def validate_dq04_company_mandatory_fields(self):
        rule_id = "DQ-04"
        rule_name = "Mandatory Company Attributes Check"
        severity = "CRITICAL"
        df = self.datasets.get("companies")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None and "company_name" in df.columns:
            invalid_names = df[df["company_name"].isna() | (df["company_name"].astype(str).str.strip() == "")]
            failed_count = len(invalid_names)
            for _, row in invalid_names.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="companies",
                    record_id=row["id"],
                    column_name="company_name",
                    invalid_value=row.get("company_name"),
                    failure_reason="company_name is null or empty",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="companies",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="company_name in companies master must not be null or empty.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-05: Year Range and Validity Check
    # -------------------------------------------------------------------------
    def validate_dq05_year_validity(self):
        rule_id = "DQ-05"
        rule_name = "Year Range and Non-Null Check"
        severity = "WARNING"
        total_rows = 0
        total_failed = 0

        year_tables = ["balancesheet", "cashflow", "documents", "financial_ratios", "market_cap", "profitandloss"]
        for table_name in year_tables:
            df = self.datasets.get(table_name)
            if df is None or "year" not in df.columns:
                continue
            total_rows += len(df)
            invalid_years = df[df["year"].isna() | (df["year"] < 2000) | (df["year"] > 2030)]
            failed_count = len(invalid_years)
            total_failed += failed_count

            for _, row in invalid_years.iterrows():
                rec_id = row.get("id", "unknown")
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name=table_name,
                    record_id=rec_id,
                    column_name="year",
                    invalid_value=row.get("year"),
                    failure_reason=f"Year is null or outside valid window [2000, 2030] (value: {row.get('year')})",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="YEAR_TABLES",
                total_records=total_rows,
                failed_records=total_failed,
                status="PASSED" if total_failed == 0 else "FAILED",
                description="Year values must be valid integers between 2000 and 2030.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-06: Stock Price Non-Negativity
    # -------------------------------------------------------------------------
    def validate_dq06_stock_price_non_negative(self):
        rule_id = "DQ-06"
        rule_name = "Stock Price Non-Negativity Check"
        severity = "CRITICAL"
        df = self.datasets.get("stock_prices")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None:
            neg_mask = (
                (df["open_price"] < 0)
                | (df["high_price"] < 0)
                | (df["low_price"] < 0)
                | (df["close_price"] < 0)
                | (df["volume"] < 0)
            )
            neg_rows = df[neg_mask]
            failed_count = len(neg_rows)
            for _, row in neg_rows.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="stock_prices",
                    record_id=row["id"],
                    column_name="prices/volume",
                    invalid_value=f"open={row['open_price']}, high={row['high_price']}, low={row['low_price']}, close={row['close_price']}, vol={row['volume']}",
                    failure_reason="Stock price or volume contains negative value",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="stock_prices",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="Stock prices (open, high, low, close) and trading volume must be non-negative.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-07: Stock Price High-Low Inversion Check
    # -------------------------------------------------------------------------
    def validate_dq07_stock_price_high_low_inversion(self):
        rule_id = "DQ-07"
        rule_name = "Stock Price High-Low Integrity Check"
        severity = "CRITICAL"
        df = self.datasets.get("stock_prices")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None:
            inv_mask = df["high_price"] < df["low_price"]
            inv_rows = df[inv_mask]
            failed_count = len(inv_rows)
            for _, row in inv_rows.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="stock_prices",
                    record_id=row["id"],
                    column_name="high_price",
                    invalid_value=f"high={row['high_price']} < low={row['low_price']}",
                    failure_reason="High price is strictly lower than low price",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="stock_prices",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="High price must always be greater than or equal to low price.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-08: Stock Price Open/Close Extreme Bounds Check
    # -------------------------------------------------------------------------
    def validate_dq08_stock_price_bounds(self):
        rule_id = "DQ-08"
        rule_name = "Stock Price High/Low vs Open/Close Bounds Check"
        severity = "WARNING"
        df = self.datasets.get("stock_prices")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None:
            bound_mask = (
                (df["high_price"] < df["open_price"])
                | (df["high_price"] < df["close_price"])
                | (df["low_price"] > df["open_price"])
                | (df["low_price"] > df["close_price"])
            )
            bound_rows = df[bound_mask]
            failed_count = len(bound_rows)
            for _, row in bound_rows.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="stock_prices",
                    record_id=row["id"],
                    column_name="ohlc",
                    invalid_value=f"O={row['open_price']}, H={row['high_price']}, L={row['low_price']}, C={row['close_price']}",
                    failure_reason="High price is below Open/Close or Low price is above Open/Close",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="stock_prices",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="High price must encompass Open/Close and Low price must be below Open/Close.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-09: Stock Price Date ISO Format Check
    # -------------------------------------------------------------------------
    def validate_dq09_stock_price_date_format(self):
        rule_id = "DQ-09"
        rule_name = "Stock Price Date ISO-8601 Format Check"
        severity = "CRITICAL"
        df = self.datasets.get("stock_prices")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None and "date" in df.columns:
            date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
            invalid_dates = df[
                df["date"].isna()
                | (~df["date"].astype(str).str.match(date_regex))
            ]
            failed_count = len(invalid_dates)
            for _, row in invalid_dates.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="stock_prices",
                    record_id=row["id"],
                    column_name="date",
                    invalid_value=row.get("date"),
                    failure_reason="Date is null or does not conform to YYYY-MM-DD format",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="stock_prices",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="All stock price dates must be valid ISO YYYY-MM-DD formatted strings.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-10: Balance Sheet Accounting Equation
    # -------------------------------------------------------------------------
    def validate_dq10_balance_sheet_equation(self):
        rule_id = "DQ-10"
        rule_name = "Balance Sheet Assets == Liabilities Check"
        severity = "CRITICAL"
        df = self.datasets.get("balancesheet")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None and "total_assets" in df.columns and "total_liabilities" in df.columns:
            diff = (df["total_assets"] - df["total_liabilities"]).abs()
            mismatch = df[diff > 1.0]
            failed_count = len(mismatch)
            for _, row in mismatch.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="balancesheet",
                    record_id=row["id"],
                    column_name="total_assets",
                    invalid_value=f"assets={row['total_assets']}, liabilities={row['total_liabilities']}",
                    failure_reason="Accounting equation violated: Total Assets != Total Liabilities",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="balancesheet",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="Total Assets must equal Total Liabilities.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-11: Balance Sheet Sub-Components Integrity
    # -------------------------------------------------------------------------
    def validate_dq11_balance_sheet_components(self):
        rule_id = "DQ-11"
        rule_name = "Balance Sheet Sub-Components Reconciliation"
        severity = "WARNING"
        df = self.datasets.get("balancesheet")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None:
            # Asset side: fixed_assets + cwip + investments + other_asset == total_assets
            asset_sum = (
                df["fixed_assets"].fillna(0)
                + df["cwip"].fillna(0)
                + df["investments"].fillna(0)
                + df["other_asset"].fillna(0)
            )
            diff_assets = (asset_sum - df["total_assets"]).abs()

            # Liability side: equity_capital + reserves + borrowings + other_liabilities == total_liabilities
            liab_sum = (
                df["equity_capital"].fillna(0)
                + df["reserves"].fillna(0)
                + df["borrowings"].fillna(0)
                + df["other_liabilities"].fillna(0)
            )
            diff_liab = (liab_sum - df["total_liabilities"]).abs()

            mismatch = df[(diff_assets > 1.0) | (diff_liab > 1.0)]
            failed_count = len(mismatch)
            for _, row in mismatch.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="balancesheet",
                    record_id=row["id"],
                    column_name="components",
                    invalid_value=f"calc_assets={asset_sum.loc[row.name]}, actual_assets={row['total_assets']}, calc_liab={liab_sum.loc[row.name]}, actual_liab={row['total_liabilities']}",
                    failure_reason="Sub-component summation differs from reported balance sheet total",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="balancesheet",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="Asset items and Liability items must sum to their respective totals.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-12: Cash Flow Statement Reconciliation
    # -------------------------------------------------------------------------
    def validate_dq12_cashflow_reconciliation(self):
        rule_id = "DQ-12"
        rule_name = "Cash Flow Statement Net Flow Reconciliation"
        severity = "WARNING"
        df = self.datasets.get("cashflow")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None:
            valid_rows = df.dropna(
                subset=["operating_activity", "investing_activity", "financing_activity", "net_cash_flow"]
            )
            calc_sum = (
                valid_rows["operating_activity"]
                + valid_rows["investing_activity"]
                + valid_rows["financing_activity"]
            )
            diff = (calc_sum - valid_rows["net_cash_flow"]).abs()
            mismatch = valid_rows[diff > 1.0]
            failed_count = len(mismatch)

            for _, row in mismatch.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="cashflow",
                    record_id=row["id"],
                    column_name="net_cash_flow",
                    invalid_value=f"calc_net={calc_sum.loc[row.name]}, reported_net={row['net_cash_flow']}",
                    failure_reason="Sum of Operating, Investing, and Financing flows does not reconcile with Net Cash Flow",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="cashflow",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="Operating + Investing + Financing cash flows must equal Net Cash Flow.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-13: Valuation Metrics Non-Negativity
    # -------------------------------------------------------------------------
    def validate_dq13_valuation_metrics(self):
        rule_id = "DQ-13"
        rule_name = "Market Cap Valuation Metrics Validity"
        severity = "CRITICAL"
        df = self.datasets.get("market_cap")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None:
            invalid_mcap = df[
                (df["market_cap_crore"] < 0)
                | (df["enterprise_value_crore"] < 0)
                | (df["pb_ratio"] < 0)
            ]
            failed_count = len(invalid_mcap)
            for _, row in invalid_mcap.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="market_cap",
                    record_id=row["id"],
                    column_name="market_cap_crore/pb_ratio",
                    invalid_value=f"mcap={row.get('market_cap_crore')}, pb={row.get('pb_ratio')}",
                    failure_reason="Valuation metric (Market Cap, EV, or P/B) is negative",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="market_cap",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="Market capitalization, enterprise value, and PB ratio must be non-negative.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-14: Sector Index Weight Bounds
    # -------------------------------------------------------------------------
    def validate_dq14_sector_index_weights(self):
        rule_id = "DQ-14"
        rule_name = "Sector Index Weight Percentage Range Check"
        severity = "WARNING"
        df = self.datasets.get("sectors")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None and "index_weight_pct" in df.columns:
            invalid_weights = df[
                (df["index_weight_pct"] < 0.0) | (df["index_weight_pct"] > 100.0) | df["index_weight_pct"].isna()
            ]
            failed_count = len(invalid_weights)
            for _, row in invalid_weights.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="sectors",
                    record_id=row["id"],
                    column_name="index_weight_pct",
                    invalid_value=row.get("index_weight_pct"),
                    failure_reason=f"index_weight_pct value {row.get('index_weight_pct')} is outside expected [0, 100] range",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="sectors",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="Sector index weight percentage must be between 0.0 and 100.0.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-15: Document URL Protocol and Format
    # -------------------------------------------------------------------------
    def validate_dq15_document_urls(self):
        rule_id = "DQ-15"
        rule_name = "Document URL Protocol Format Check"
        severity = "WARNING"
        df = self.datasets.get("documents")
        total_rows = len(df) if df is not None else 0
        failed_count = 0

        if df is not None and "annual_report" in df.columns:
            non_null_docs = df[df["annual_report"].notna()]
            url_pattern = re.compile(r"^https?://", re.IGNORECASE)
            invalid_urls = non_null_docs[~non_null_docs["annual_report"].astype(str).str.match(url_pattern)]
            failed_count = len(invalid_urls)

            for _, row in invalid_urls.iterrows():
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name="documents",
                    record_id=row["id"],
                    column_name="annual_report",
                    invalid_value=row.get("annual_report"),
                    failure_reason="Annual report URL does not start with http:// or https://",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="documents",
                total_records=total_rows,
                failed_records=failed_count,
                status="PASSED" if failed_count == 0 else "FAILED",
                description="Document filing links must be valid URLs starting with http:// or https://.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE DQ-16: Entity-Time Composite Uniqueness
    # -------------------------------------------------------------------------
    def validate_dq16_composite_uniqueness(self):
        rule_id = "DQ-16"
        rule_name = "Composite Key (Entity, Time) Duplicate Check"
        severity = "WARNING"
        total_rows = 0
        total_failed = 0

        target_configs = [
            ("balancesheet", ["company_id", "year"]),
            ("cashflow", ["company_id", "year"]),
            ("financial_ratios", ["company_id", "year"]),
            ("market_cap", ["company_id", "year"]),
            ("profitandloss", ["company_id", "year"]),
            ("stock_prices", ["company_id", "date"]),
        ]

        for table_name, subset_cols in target_configs:
            df = self.datasets.get(table_name)
            if df is None or not all(c in df.columns for c in subset_cols):
                continue
            
            # Filter rows where subset columns are non-null
            valid_df = df.dropna(subset=subset_cols)
            total_rows += len(valid_df)
            dup_mask = valid_df.duplicated(subset=subset_cols, keep=False)
            dups = valid_df[dup_mask]
            failed_count = len(dups)
            total_failed += failed_count

            for _, row in dups.iterrows():
                key_val = ", ".join(f"{c}={row[c]}" for c in subset_cols)
                self.record_failure(
                    rule_id=rule_id,
                    severity=severity,
                    table_name=table_name,
                    record_id=row["id"],
                    column_name=str(subset_cols),
                    invalid_value=key_val,
                    failure_reason=f"Duplicate composite key observation ({key_val})",
                )

        self.rule_summaries.append(
            RuleSummary(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                table_name="TIME_SERIES_TABLES",
                total_records=total_rows,
                failed_records=total_failed,
                status="PASSED" if total_failed == 0 else "FAILED",
                description="Unique observations expected per company and period (year or date).",
            )
        )

    # -------------------------------------------------------------------------
    # Master Execution Method
    # -------------------------------------------------------------------------
    def run_all_rules(self) -> pd.DataFrame:
        self.failures.clear()
        self.rule_summaries.clear()

        # Run all 16 DQ rules
        self.validate_dq01_pk_not_null()
        self.validate_dq02_pk_uniqueness()
        self.validate_dq03_foreign_key_integrity()
        self.validate_dq04_company_mandatory_fields()
        self.validate_dq05_year_validity()
        self.validate_dq06_stock_price_non_negative()
        self.validate_dq07_stock_price_high_low_inversion()
        self.validate_dq08_stock_price_bounds()
        self.validate_dq09_stock_price_date_format()
        self.validate_dq10_balance_sheet_equation()
        self.validate_dq11_balance_sheet_components()
        self.validate_dq12_cashflow_reconciliation()
        self.validate_dq13_valuation_metrics()
        self.validate_dq14_sector_index_weights()
        self.validate_dq15_document_urls()
        self.validate_dq16_composite_uniqueness()

        # Build Failures DataFrame
        if self.failures:
            failures_df = pd.DataFrame(
                [
                    {
                        "rule_id": f.rule_id,
                        "severity": f.severity,
                        "table_name": f.table_name,
                        "record_id": f.record_id,
                        "column_name": f.column_name,
                        "invalid_value": f.invalid_value,
                        "failure_reason": f.failure_reason,
                    }
                    for f in self.failures
                ]
            )
        else:
            failures_df = pd.DataFrame(
                columns=[
                    "rule_id",
                    "severity",
                    "table_name",
                    "record_id",
                    "column_name",
                    "invalid_value",
                    "failure_reason",
                ]
            )

        return failures_df

    def get_summary_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "rule_id": s.rule_id,
                    "rule_name": s.rule_name,
                    "severity": s.severity,
                    "table_name": s.table_name,
                    "total_records": s.total_records,
                    "failed_records": s.failed_records,
                    "status": s.status,
                    "description": s.description,
                }
                for s in self.rule_summaries
            ]
        )


def run_all_validations(datasets: Dict[str, pd.DataFrame], output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Run full suite of 16 Data Quality validations and write validation_failures.csv.
    """
    validator = DataQualityValidator(datasets)
    failures_df = validator.run_all_rules()

    out_file = output_path if output_path else OUTPUT_DIR / "validation_failures.csv"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    failures_df.to_csv(out_file, index=False)

    return failures_df
