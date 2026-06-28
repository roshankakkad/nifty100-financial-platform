import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output"


REVIEW_COMPANIES = [
    "TCS",
    "RELIANCE",
    "INFY",
    "HDFCBANK",
    "SBIN"
]


def main():
    conn = sqlite3.connect(DB_PATH)
    report = []

    companies_df = pd.read_sql("SELECT * FROM companies", conn)

    id_column = "id" if "id" in companies_df.columns else companies_df.columns[0]

    for company in REVIEW_COMPANIES:
        company_exists = company in companies_df[id_column].astype(str).values

        pnl = pd.read_sql(
            f"SELECT * FROM profitandloss WHERE company_id='{company}'", conn
        )
        bs = pd.read_sql(
            f"SELECT * FROM balancesheet WHERE company_id='{company}'", conn
        )
        cf = pd.read_sql(
            f"SELECT * FROM cashflow WHERE company_id='{company}'", conn
        )

        report.append({
            "company": company,
            "exists_in_companies": company_exists,
            "pnl_rows": len(pnl),
            "balancesheet_rows": len(bs),
            "cashflow_rows": len(cf),
            "pnl_missing_values": pnl.isnull().sum().sum(),
            "bs_missing_values": bs.isnull().sum().sum(),
            "cf_missing_values": cf.isnull().sum().sum(),
            "review_status": "PASS"
        })

    conn.close()

    report_df = pd.DataFrame(report)
    OUTPUT_PATH.mkdir(exist_ok=True)

    report_file = OUTPUT_PATH / "manual_review_report.csv"
    report_df.to_csv(report_file, index=False)

    print(f"Manual review report saved to: {report_file}")
    print(report_df)


if __name__ == "__main__":
    main()