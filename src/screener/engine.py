from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "nifty100.db"
CONFIG_PATH = ROOT / "config" / "screener_config.yaml"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _as_year_num(series):
    return pd.to_numeric(series.astype(str).str.extract(r"(\d{4})")[0], errors="coerce")


def load_screener_data():
    conn = sqlite3.connect(DB_PATH)
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    market = pd.read_sql(
        "SELECT company_id, year, market_cap_crore, pe_ratio, pb_ratio, dividend_yield_pct FROM market_cap",
        conn,
    )
    conn.close()

    if "year_num" not in ratios.columns:
        ratios["year_num"] = _as_year_num(ratios["year"])
    else:
        ratios["year_num"] = pd.to_numeric(ratios["year_num"], errors="coerce")
    market["year_num"] = _as_year_num(market["year"])

    df = ratios.merge(sectors, on="company_id", how="left")
    df = df.merge(companies, left_on="company_id", right_on="id", how="left")
    df = df.merge(
        market.drop(columns=["year"]),
        on=["company_id", "year_num"],
        how="left",
    )

    df = df.sort_values(["company_id", "year_num"])
    df["de_prev"] = df.groupby("company_id")["debt_to_equity"].shift(1)
    df["de_declining_flag"] = df["debt_to_equity"] < df["de_prev"]
    return df


def latest_records(df):
    df = df.copy()
    key_cols = ["return_on_equity_pct", "net_profit_margin_pct", "free_cash_flow_cr"]
    valid = df.dropna(subset=[c for c in key_cols if c in df.columns])
    if valid.empty:
        valid = df
    return valid.sort_values(["company_id", "year_num"]).groupby("company_id", as_index=False).tail(1)


def latest_qualifying_per_company(df):
    return df.sort_values(["company_id", "year_num"]).groupby("company_id", as_index=False).tail(1)


def _winsor_score(series, higher_is_better=True):
    s = pd.to_numeric(series, errors="coerce")
    if s.notna().sum() == 0:
        return pd.Series(50, index=series.index, dtype=float)
    lo = s.quantile(0.10)
    hi = s.quantile(0.90)
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        score = pd.Series(50, index=series.index, dtype=float)
    else:
        clipped = s.clip(lo, hi)
        score = (clipped - lo) / (hi - lo) * 100
    if not higher_is_better:
        score = 100 - score
    return score.fillna(50)


def add_composite_quality_score(df):
    df = df.copy()
    if df.empty:
        df["composite_quality_score"] = pd.Series(dtype=float)
        df["sector_relative_score"] = pd.Series(dtype=float)
        return df

    df["score_roe"] = _winsor_score(df["return_on_equity_pct"])
    df["score_roce"] = _winsor_score(df.get("return_on_capital_employed_pct", pd.Series(0, index=df.index)))
    df["score_npm"] = _winsor_score(df["net_profit_margin_pct"])
    df["score_fcf_cagr"] = _winsor_score(df.get("fcf_cagr_5yr", df["free_cash_flow_cr"]))
    df["score_cfo_pat"] = _winsor_score(df.get("cfo_pat_ratio", pd.Series(0, index=df.index)))
    df["score_fcf_flag"] = np.where(df["free_cash_flow_cr"].fillna(0) > 0, 100, 0)
    df["score_revenue_growth"] = _winsor_score(df["revenue_cagr_5yr"])
    df["score_pat_growth"] = _winsor_score(df["pat_cagr_5yr"])
    df["score_de"] = _winsor_score(df["debt_to_equity"], higher_is_better=False)
    df["score_icr"] = _winsor_score(df["interest_coverage"].replace([np.inf, -np.inf], np.nan).fillna(999))

    df["composite_quality_score"] = (
        df["score_roe"] * 0.15
        + df["score_roce"] * 0.10
        + df["score_npm"] * 0.10
        + df["score_fcf_cagr"] * 0.15
        + df["score_cfo_pat"] * 0.10
        + df["score_fcf_flag"] * 0.05
        + df["score_revenue_growth"] * 0.10
        + df["score_pat_growth"] * 0.10
        + df["score_de"] * 0.10
        + df["score_icr"] * 0.05
    ).clip(0, 100)

    sector_parts = []
    for _, group in df.groupby("broad_sector", dropna=False):
        sector_parts.append(_winsor_score(group["composite_quality_score"]))
    df["sector_relative_score"] = pd.concat(sector_parts).sort_index()
    return df


def apply_filters(df, rules):
    df = df.copy()
    rules = dict(rules or {})

    if rules.get("roe_min") is not None:
        df = df[df["return_on_equity_pct"] > rules["roe_min"]]
    if rules.get("debt_equal_zero"):
        df = df[df["debt_to_equity"].fillna(np.inf) <= 0.01]
    elif rules.get("de_max") is not None:
        financials = df["broad_sector"].eq("Financials")
        df = df[(df["debt_to_equity"] <= rules["de_max"]) | financials]
    if rules.get("fcf_min") is not None:
        df = df[df["free_cash_flow_cr"] > rules["fcf_min"]]
    if rules.get("revenue_cagr_3yr_min") is not None:
        df = df[df["revenue_cagr_3yr"] > rules["revenue_cagr_3yr_min"]]
    if rules.get("revenue_cagr_5yr_min") is not None:
        df = df[df["revenue_cagr_5yr"] > rules["revenue_cagr_5yr_min"]]
    if rules.get("pat_cagr_5yr_min") is not None:
        df = df[df["pat_cagr_5yr"] > rules["pat_cagr_5yr_min"]]
    if rules.get("opm_min") is not None:
        df = df[df["operating_profit_margin_pct"] > rules["opm_min"]]
    if rules.get("pe_max") is not None:
        df = df[df["pe_ratio"] < rules["pe_max"]]
    if rules.get("pb_max") is not None:
        df = df[df["pb_ratio"] < rules["pb_max"]]
    if rules.get("dividend_yield_min") is not None:
        df = df[df["dividend_yield_pct"] > rules["dividend_yield_min"]]
    if rules.get("dividend_payout_max") is not None:
        df = df[df["dividend_payout_ratio_pct"] < rules["dividend_payout_max"]]
    if rules.get("icr_min") is not None:
        icr = df["interest_coverage"].fillna(np.inf)
        df = df[icr >= rules["icr_min"]]
    if rules.get("market_cap_min") is not None:
        df = df[df["market_cap_crore"] > rules["market_cap_min"]]
    if rules.get("net_profit_min") is not None:
        df = df[df["net_profit"] > rules["net_profit_min"]]
    if rules.get("eps_cagr_min") is not None:
        df = df[df["eps_cagr_5yr"] > rules["eps_cagr_min"]]
    if rules.get("asset_turnover_min") is not None:
        df = df[df["asset_turnover"] > rules["asset_turnover_min"]]
    if rules.get("sales_min") is not None:
        df = df[df["sales"] > rules["sales_min"]]
    if rules.get("de_declining") is True:
        df = df[df["de_declining_flag"].fillna(False)]

    df = latest_qualifying_per_company(df)
    df = add_composite_quality_score(df).sort_values("composite_quality_score", ascending=False)

    max_results = rules.get("max_results")
    if max_results is not None:
        df = df.head(int(max_results))
    return df


def run_custom_screen(rules):
    rules = rules or {}
    df = load_screener_data()
    if rules.get("filter_scope") != "all_years":
        df = latest_records(df)
    return apply_filters(df, rules)


if __name__ == "__main__":
    sample = {"roe_min": 15, "de_max": 1.0, "fcf_min": 0}
    result = run_custom_screen(sample)
    cols = ["company_id", "year", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "composite_quality_score"]
    print(result[cols].head(20))
    print("Total companies:", result["company_id"].nunique())
