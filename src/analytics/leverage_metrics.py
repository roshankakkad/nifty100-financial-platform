import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))

import sqlite3
import pandas as pd
from analytics.ratios import (
    debt_to_equity,
    high_leverage_flag,
    interest_coverage,
    interest_coverage_label,
    interest_coverage_warning,
    net_debt,
    asset_turnover
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output"


def main():
    conn = sqlite3.connect(DB_PATH)

    pnl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    sectors = pd.read_sql("SELECT * FROM sectors", conn)

    merged = pd.merge(pnl, bs, on=["company_id", "year"], how="inner")

    if "company_id" in sectors.columns:
        merged = pd.merge(
            merged,
            sectors[["company_id", "broad_sector"]],
            on="company_id",
            how="left"
        )

    merged["debt_to_equity"] = merged.apply(
        lambda row: debt_to_equity(
            row["borrowings"],
            row["equity_capital"],
            row["reserves"]
        ),
        axis=1
    )

    merged["high_leverage_flag"] = merged.apply(
        lambda row: high_leverage_flag(
            row["debt_to_equity"],
            row.get("broad_sector", "")
        ),
        axis=1
    )

    merged["interest_coverage"] = merged.apply(
        lambda row: interest_coverage(
            row["operating_profit"],
            row["other_income"],
            row["interest"]
        ),
        axis=1
    )

    merged["icr_label"] = merged["interest_coverage"].apply(
        interest_coverage_label
    )

    merged["icr_warning"] = merged["interest_coverage"].apply(
        interest_coverage_warning
    )

    merged["net_debt"] = merged.apply(
        lambda row: net_debt(
            row["borrowings"],
            row["investments"]
        ),
        axis=1
    )

    merged["asset_turnover"] = merged.apply(
        lambda row: asset_turnover(
            row["sales"],
            row["total_assets"]
        ),
        axis=1
    )

    result = merged[
        [
            "company_id",
            "year",
            "debt_to_equity",
            "high_leverage_flag",
            "interest_coverage",
            "icr_label",
            "icr_warning",
            "net_debt",
            "asset_turnover",
        ]
    ]

    OUTPUT_PATH.mkdir(exist_ok=True)
    result.to_csv(OUTPUT_PATH / "day09_ratios.csv", index=False)

    print("Day 09 completed")
    print(result.head())

    conn.close()


if __name__ == "__main__":
    main()