import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"


def main():
    conn = sqlite3.connect(DB_PATH)

    pnl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)

    merged = pnl.merge(bs, on=["company_id", "year"], how="inner")
    merged = merged.merge(cf, on=["company_id", "year"], how="inner")

    merged["net_profit_margin_pct"] = (
        merged["net_profit"] / merged["sales"].replace(0, 1)
    ) * 100

    merged["operating_profit_margin_pct"] = (
        merged["operating_profit"] / merged["sales"].replace(0, 1)
    ) * 100

    merged["return_on_equity_pct"] = (
        merged["net_profit"] /
        (merged["equity_capital"] + merged["reserves"]).replace(0, 1)
    ) * 100

    merged["debt_to_equity"] = (
        merged["borrowings"] /
        (merged["equity_capital"] + merged["reserves"]).replace(0, 1)
    )

    merged["interest_coverage"] = (
        (merged["operating_profit"] + merged["other_income"]) /
        merged["interest"].replace(0, 1)
    )

    merged["asset_turnover"] = (
        merged["sales"] / merged["total_assets"].replace(0, 1)
    )

    merged["free_cash_flow_cr"] = (
        merged["operating_activity"] + merged["investing_activity"]
    )

    merged["capex_cr"] = abs(merged["investing_activity"])

    merged["earnings_per_share"] = merged["eps"]

    merged["book_value_per_share"] = (
        (merged["equity_capital"] + merged["reserves"]) /
        merged["equity_capital"].replace(0, 1)
    )

    merged["dividend_payout_ratio_pct"] = merged["dividend_payout"]

    merged["total_debt_cr"] = merged["borrowings"]

    merged["cash_from_operations_cr"] = merged["operating_activity"]

    # temporary placeholders from Day 10
    merged["revenue_cagr_5yr"] = 0
    merged["pat_cagr_5yr"] = 0
    merged["eps_cagr_5yr"] = 0

    merged["composite_quality_score"] = (
        merged["return_on_equity_pct"] * 0.35
        + merged["operating_profit_margin_pct"] * 0.25
        + merged["asset_turnover"] * 20
    )

    final = merged[
        [
            "company_id",
            "year",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "free_cash_flow_cr",
            "capex_cr",
            "earnings_per_share",
            "book_value_per_share",
            "dividend_payout_ratio_pct",
            "total_debt_cr",
            "cash_from_operations_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",
            "composite_quality_score"
        ]
    ]

    final.to_sql("financial_ratios", conn, if_exists="replace", index=False)

    count = pd.read_sql("SELECT COUNT(*) as cnt FROM financial_ratios", conn)
    print(count)

    conn.close()
    print("Day 12 completed")


if __name__ == "__main__":
    main()