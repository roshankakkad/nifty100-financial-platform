import sys
from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))

from analytics.cagr import compute_metric_cagr

DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output"


def main():
    conn = sqlite3.connect(DB_PATH)
    pnl = pd.read_sql("SELECT * FROM profitandloss", conn)

    results = []

    for company_id, group in pnl.groupby("company_id"):
        group = group.sort_values("year")

        revenue_cagr, revenue_flag = compute_metric_cagr(
            group["sales"], 5
        )

        pat_cagr, pat_flag = compute_metric_cagr(
            group["net_profit"], 5
        )

        eps_cagr, eps_flag = compute_metric_cagr(
            group["eps"], 5
        )

        results.append({
            "company_id": company_id,
            "revenue_cagr_5yr": revenue_cagr,
            "revenue_flag": revenue_flag,
            "pat_cagr_5yr": pat_cagr,
            "pat_flag": pat_flag,
            "eps_cagr_5yr": eps_cagr,
            "eps_flag": eps_flag
        })

    df = pd.DataFrame(results)
    OUTPUT_PATH.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_PATH / "day10_cagr.csv", index=False)

    print("Day 10 completed")
    print(df.head())


if __name__ == "__main__":
    main()