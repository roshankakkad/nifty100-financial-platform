import pandas as pd
from pathlib import Path
from loader import load_all_datasets

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "output"


class DataValidator:
    def __init__(self, datasets):
        self.datasets = datasets
        self.failures = []

    def log_failure(self, table, company_id, year, field, issue, severity):
        self.failures.append({
            "table": table,
            "company_id": company_id,
            "year": year,
            "field": field,
            "issue": issue,
            "severity": severity
        })

    # DQ-01: duplicate company IDs
    def check_duplicate_companies(self):
        df = self.datasets["companies"]

        duplicates = df[df.duplicated("id", keep=False)]

        for _, row in duplicates.iterrows():
            self.log_failure(
                "companies",
                row["id"],
                None,
                "id",
                "Duplicate company ID",
                "CRITICAL"
            )

    # DQ-02: duplicate (company_id, year)
    def check_duplicate_company_year(self):
        tables = ["profitandloss", "balancesheet", "cashflow"]

        for table in tables:
            df = self.datasets[table]

            duplicates = df[df.duplicated(["company_id", "year"], keep=False)]

            for _, row in duplicates.iterrows():
                self.log_failure(
                    table,
                    row["company_id"],
                    row["year"],
                    "company_id,year",
                    "Duplicate company-year",
                    "CRITICAL"
                )

    # DQ-03: FK integrity
    def check_foreign_keys(self):
        company_ids = set(self.datasets["companies"]["id"])

        tables = [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "analysis",
            "documents",
            "prosandcons"
        ]

        for table in tables:
            df = self.datasets[table]

            for _, row in df.iterrows():
                cid = row["company_id"]

                if cid not in company_ids:
                    self.log_failure(
                        table,
                        cid,
                        row["year"] if "year" in row else None,
                        "company_id",
                        "Foreign key missing",
                        "CRITICAL"
                    )

    # DQ-04: sales > 0
    def check_positive_sales(self):
        df = self.datasets["profitandloss"]

        bad = df[df["sales"] <= 0]

        for _, row in bad.iterrows():
            self.log_failure(
                "profitandloss",
                row["company_id"],
                row["year"],
                "sales",
                "Sales must be > 0",
                "CRITICAL"
            )

    # DQ-05: OPM cross-check
    def check_opm(self):
        df = self.datasets["profitandloss"]

        for _, row in df.iterrows():
            if row["sales"] != 0:
                calc = (row["operating_profit"] / row["sales"]) * 100
                actual = row["opm_percentage"]

                if abs(calc - actual) > 1:
                    self.log_failure(
                        "profitandloss",
                        row["company_id"],
                        row["year"],
                        "opm_percentage",
                        "OPM mismatch >1%",
                        "WARNING"
                    )

    # DQ-06: balance sheet equation
    def check_balance_sheet(self):
        df = self.datasets["balancesheet"]

        for _, row in df.iterrows():
            assets = row["total_assets"]
            liabilities = row["total_liabilities"]

            if assets != 0:
                diff = abs(assets - liabilities) / assets

                if diff > 0.01:
                    self.log_failure(
                        "balancesheet",
                        row["company_id"],
                        row["year"],
                        "total_assets",
                        "Assets != Liabilities",
                        "CRITICAL"
                    )

    # DQ-07: net cash flow check
    def check_cashflow(self):
        df = self.datasets["cashflow"]

        for _, row in df.iterrows():
            calc = (
                row["operating_activity"]
                + row["investing_activity"]
                + row["financing_activity"]
            )

            actual = row["net_cash_flow"]

            if abs(calc - actual) > 10:
                self.log_failure(
                    "cashflow",
                    row["company_id"],
                    row["year"],
                    "net_cash_flow",
                    "Cashflow mismatch >10",
                    "WARNING"
                )

    def run_all_checks(self):
        self.check_duplicate_companies()
        self.check_duplicate_company_year()
        self.check_foreign_keys()
        self.check_positive_sales()
        self.check_opm()
        self.check_balance_sheet()
        self.check_cashflow()

        return pd.DataFrame(self.failures)


if __name__ == "__main__":
    datasets = load_all_datasets()
    validator = DataValidator(datasets)

    failures_df = validator.run_all_checks()

    OUTPUT_PATH.mkdir(exist_ok=True)
    output_file = OUTPUT_PATH / "validation_failures.csv"

    failures_df.to_csv(output_file, index=False)

    print(f"Validation completed.")
    print(f"Failures found: {len(failures_df)}")
    print(f"Saved to: {output_file}")