import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output"


def classify_pattern(cfo, cfi, cff, cfo_quality=None):
    signs = (
        "+" if cfo >= 0 else "-",
        "+" if cfi >= 0 else "-",
        "+" if cff >= 0 else "-"
    )

    if signs == ("+", "-", "-"):
        if cfo_quality is not None and cfo_quality > 1:
            return "Shareholder Returns"
        return "Reinvestor"

    if signs == ("+", "+", "-"):
        return "Liquidating Assets"

    if signs == ("-", "+", "+"):
        return "Distress Signal"

    if signs == ("-", "-", "+"):
        return "Growth Funded by Debt"

    if signs == ("+", "+", "+"):
        return "Cash Accumulator"

    if signs == ("-", "-", "-"):
        return "Pre-Revenue"

    if signs == ("+", "-", "+"):
        return "Mixed"

    return "Other"


def main():
    conn = sqlite3.connect(DB_PATH)

    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    pnl = pd.read_sql(
    "SELECT company_id, year, net_profit, operating_profit, sales FROM profitandloss",
    conn)

    merged = pd.merge(cf, pnl, on=["company_id", "year"], how="left")

    # Free Cash Flow
    merged["free_cash_flow"] = (
        merged["operating_activity"] + merged["investing_activity"]
    )

    # CFO Quality
    merged["cfo_quality_score"] = merged.apply(
        lambda row: None
        if row["net_profit"] == 0
        else row["operating_activity"] / row["net_profit"],
        axis=1
    )

    def cfo_quality_label(score):
        if score is None:
            return None
        if score > 1:
            return "High Quality"
        if score >= 0.5:
            return "Moderate"
        return "Accrual Risk"

    merged["cfo_quality_label"] = merged["cfo_quality_score"].apply(
        cfo_quality_label
    )

    # CapEx Intensity
    merged["capex_intensity"] = merged.apply(
        lambda row: None
        if row["operating_profit"] == 0
        else abs(row["investing_activity"]) / row["sales"] * 100,
        axis=1
    )

    # FCF Conversion
    merged["fcf_conversion"] = merged.apply(
        lambda row: None
        if row["operating_profit"] == 0
        else row["free_cash_flow"] / row["operating_profit"] * 100,
        axis=1
    )

    # Pattern labels
    merged["pattern_label"] = merged.apply(
        lambda row: classify_pattern(
            row["operating_activity"],
            row["investing_activity"],
            row["financing_activity"],
            row["cfo_quality_score"]
        ),
        axis=1
    )

    result = merged[
        [
            "company_id",
            "year",
            "free_cash_flow",
            "cfo_quality_score",
            "cfo_quality_label",
            "capex_intensity",
            "fcf_conversion",
            "pattern_label"
        ]
    ]

    OUTPUT_PATH.mkdir(exist_ok=True)
    result.to_csv(OUTPUT_PATH / "capital_allocation.csv", index=False)

    print("Day 11 completed")
    print(result.head())

    conn.close()


if __name__ == "__main__":
    main()