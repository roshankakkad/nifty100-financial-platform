from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "nifty100.db"
OUTPUT_DIR = ROOT / "output"


def year_number(value):
    match = pd.Series([str(value)]).str.extract(r"(\d{4})").iloc[0, 0]
    if pd.isna(match):
        return np.nan
    return int(match)


def safe_div(num, den):
    if pd.isna(den) or den == 0:
        return np.nan
    return num / den


def cagr_pair(start, end, years):
    if pd.isna(start) or pd.isna(end):
        return np.nan, "INSUFFICIENT"
    if start == 0:
        return np.nan, "ZERO_BASE"
    if start > 0 and end > 0:
        return (((end / start) ** (1 / years)) - 1) * 100, "NORMAL"
    if start > 0 and end < 0:
        return np.nan, "DECLINE_TO_LOSS"
    if start < 0 and end > 0:
        return np.nan, "TURNAROUND"
    if start < 0 and end < 0:
        return np.nan, "BOTH_NEGATIVE"
    return np.nan, "UNKNOWN"


def add_cagr_columns(df, metric, windows=(3, 5, 10)):
    df = df.copy()
    for window in windows:
        values = []
        flags = []
        for _, group in df.groupby("company_id", sort=False):
            group = group.sort_values("year_num")
            metric_values = group[metric].reset_index(drop=True)
            for i, end_value in enumerate(metric_values):
                if i < window:
                    values.append(np.nan)
                    flags.append("INSUFFICIENT")
                else:
                    start_value = metric_values.iloc[i - window]
                    value, flag = cagr_pair(start_value, end_value, window)
                    values.append(value)
                    flags.append(flag)
        df[f"{metric}_cagr_{window}yr"] = values
        df[f"{metric}_cagr_{window}yr_flag"] = flags
    return df


def build_ratios():
    conn = sqlite3.connect(DB_PATH)
    pnl = pd.read_sql("SELECT * FROM profitandloss", conn).drop_duplicates(["company_id", "year"])
    bs = pd.read_sql("SELECT * FROM balancesheet", conn).drop_duplicates(["company_id", "year"])
    cf = pd.read_sql("SELECT * FROM cashflow", conn).drop_duplicates(["company_id", "year"])
    companies = pd.read_sql("SELECT id, face_value FROM companies", conn)

    df = pnl.merge(bs, on=["company_id", "year"], how="left", suffixes=("", "_bs"))
    df = df.merge(cf, on=["company_id", "year"], how="left", suffixes=("", "_cf"))
    df = df.merge(companies, left_on="company_id", right_on="id", how="left")

    df["year_num"] = df["year"].apply(year_number)
    df = df.sort_values(["company_id", "year_num"])

    equity = df["equity_capital"].fillna(0) + df["reserves"].fillna(0)
    capital_employed = equity + df["borrowings"].fillna(0)
    ebit = df["operating_profit"].fillna(0) - df["depreciation"].fillna(0)

    df["net_profit_margin_pct"] = np.where(df["sales"] == 0, np.nan, df["net_profit"] / df["sales"] * 100)
    df["operating_profit_margin_pct"] = np.where(df["sales"] == 0, np.nan, df["operating_profit"] / df["sales"] * 100)
    df["return_on_equity_pct"] = np.where(equity <= 0, np.nan, df["net_profit"] / equity * 100)
    df["return_on_capital_employed_pct"] = np.where(capital_employed <= 0, np.nan, ebit / capital_employed * 100)
    df["return_on_assets_pct"] = np.where(df["total_assets"] == 0, np.nan, df["net_profit"] / df["total_assets"] * 100)
    df["debt_to_equity"] = np.where(df["borrowings"].fillna(0) == 0, 0, df["borrowings"] / equity.replace(0, np.nan))
    df["interest_coverage"] = np.where(df["interest"].fillna(0) == 0, np.nan, (df["operating_profit"] + df["other_income"].fillna(0)) / df["interest"])
    df["icr_label"] = np.where(df["interest"].fillna(0) == 0, "Debt Free", "")
    df["asset_turnover"] = np.where(df["total_assets"] == 0, np.nan, df["sales"] / df["total_assets"])
    df["free_cash_flow_cr"] = df["operating_activity"].fillna(0) + df["investing_activity"].fillna(0)
    df["capex_cr"] = df["investing_activity"].abs()
    df["earnings_per_share"] = df["eps"]
    share_count = df["equity_capital"] / df["face_value"].replace(0, np.nan)
    df["book_value_per_share"] = equity / share_count.replace(0, np.nan)
    df["dividend_payout_ratio_pct"] = df["dividend_payout"]
    df["total_debt_cr"] = df["borrowings"]
    df["cash_from_operations_cr"] = df["operating_activity"]
    df["net_profit"] = df["net_profit"]
    df["sales"] = df["sales"]

    df = add_cagr_columns(df, "sales", (3, 5, 10))
    df = add_cagr_columns(df, "net_profit", (3, 5, 10))
    df = add_cagr_columns(df, "eps", (3, 5, 10))
    df = df.rename(columns={
        "sales_cagr_3yr": "revenue_cagr_3yr",
        "sales_cagr_5yr": "revenue_cagr_5yr",
        "sales_cagr_10yr": "revenue_cagr_10yr",
        "sales_cagr_3yr_flag": "revenue_cagr_3yr_flag",
        "sales_cagr_5yr_flag": "revenue_cagr_5yr_flag",
        "sales_cagr_10yr_flag": "revenue_cagr_10yr_flag",
        "net_profit_cagr_3yr": "pat_cagr_3yr",
        "net_profit_cagr_5yr": "pat_cagr_5yr",
        "net_profit_cagr_10yr": "pat_cagr_10yr",
        "net_profit_cagr_3yr_flag": "pat_cagr_3yr_flag",
        "net_profit_cagr_5yr_flag": "pat_cagr_5yr_flag",
        "net_profit_cagr_10yr_flag": "pat_cagr_10yr_flag",
        "eps_cagr_3yr": "eps_cagr_3yr",
        "eps_cagr_5yr": "eps_cagr_5yr",
        "eps_cagr_10yr": "eps_cagr_10yr",
    })

    df["cfo_pat_ratio"] = np.where(df["net_profit"] == 0, np.nan, df["operating_activity"] / df["net_profit"])
    df["fcf_positive_flag"] = (df["free_cash_flow_cr"] > 0).astype(int)

    # Initial score; screener recalculates the sector-aware score later.
    df["composite_quality_score"] = (
        df["return_on_equity_pct"].fillna(0) * 0.35
        + df["operating_profit_margin_pct"].fillna(0) * 0.20
        + df["free_cash_flow_cr"].gt(0).astype(int) * 20
        + np.clip(1 / (1 + df["debt_to_equity"].fillna(10)), 0, 1) * 25
    )

    keep = [
        "company_id", "year", "year_num", "net_profit_margin_pct", "operating_profit_margin_pct",
        "return_on_equity_pct", "return_on_capital_employed_pct", "return_on_assets_pct",
        "debt_to_equity", "interest_coverage", "icr_label", "asset_turnover", "free_cash_flow_cr",
        "capex_cr", "earnings_per_share", "book_value_per_share", "dividend_payout_ratio_pct",
        "total_debt_cr", "cash_from_operations_cr", "net_profit", "sales", "operating_profit",
        "revenue_cagr_3yr", "revenue_cagr_5yr", "revenue_cagr_10yr",
        "pat_cagr_3yr", "pat_cagr_5yr", "pat_cagr_10yr",
        "eps_cagr_3yr", "eps_cagr_5yr", "eps_cagr_10yr",
        "revenue_cagr_3yr_flag", "revenue_cagr_5yr_flag", "pat_cagr_5yr_flag", "eps_cagr_5yr_flag",
        "cfo_pat_ratio", "fcf_positive_flag", "composite_quality_score"
    ]
    final = df[keep].copy()
    final.to_sql("financial_ratios", conn, if_exists="replace", index=False)
    OUTPUT_DIR.mkdir(exist_ok=True)
    final.to_csv(OUTPUT_DIR / "financial_ratios_computed.csv", index=False)
    print(f"financial_ratios rows: {len(final)}")
    conn.close()


if __name__ == "__main__":
    build_ratios()
