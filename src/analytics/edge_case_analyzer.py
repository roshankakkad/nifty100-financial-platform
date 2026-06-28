import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output"


def main():
    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql("SELECT * FROM companies", conn)
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    sectors = pd.read_sql("SELECT * FROM sectors", conn)

    merged = ratios.merge(
        companies[["id", "roe_percentage", "roce_percentage"]],
        left_on="company_id",
        right_on="id",
        how="left"
    )

    if "company_id" in sectors.columns:
        merged = merged.merge(
            sectors[["company_id", "broad_sector"]],
            on="company_id",
            how="left"
        )

    log_entries = []

    for _, row in merged.iterrows():
        company = row["company_id"]

        # Financial sector carve-out
        if row.get("broad_sector", "") == "Financials":
            if row["debt_to_equity"] > 5:
                log_entries.append(
                    f"{company}: High D/E suppressed (Financial sector)"
                )

        # ROE anomaly
        computed_roe = row["return_on_equity_pct"]
        source_roe = row["roe_percentage"]

        if pd.notna(source_roe):
            if abs(computed_roe - source_roe) > 5:
                log_entries.append(
                    f"{company}: ROE anomaly | computed={computed_roe:.2f}, source={source_roe}"
                )

        # ROCE anomaly
        computed_roce = row["composite_quality_score"]  # temporary proxy
        source_roce = row["roce_percentage"]

        if pd.notna(source_roce):
            if abs(computed_roce - source_roce) > 5:
                log_entries.append(
                    f"{company}: ROCE anomaly | computed={computed_roce:.2f}, source={source_roce}"
                )

    OUTPUT_PATH.mkdir(exist_ok=True)
    log_file = OUTPUT_PATH / "ratio_edge_cases.log"

    with open(log_file, "w", encoding="utf-8") as f:
        for line in log_entries:
            f.write(line + "\n")

    print(f"Day 13 completed")
    print(f"Edge cases logged: {len(log_entries)}")

    conn.close()


if __name__ == "__main__":
    main()