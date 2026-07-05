from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "nifty100.db"
OUTPUT_DIR = ROOT / "output"

METRICS = {
    "return_on_equity_pct": False,
    "return_on_capital_employed_pct": False,
    "net_profit_margin_pct": False,
    "debt_to_equity": True,
    "free_cash_flow_cr": False,
    "pat_cagr_5yr": False,
    "revenue_cagr_5yr": False,
    "eps_cagr_5yr": False,
    "interest_coverage": False,
    "asset_turnover": False,
}


def latest_ratios(conn):
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    ratios = ratios.merge(sectors, on="company_id", how="left")
    ratios = ratios.merge(companies, left_on="company_id", right_on="id", how="left")
    ratios["year_num"] = pd.to_numeric(ratios["year_num"], errors="coerce")
    ratios = ratios.dropna(subset=["year_num", "return_on_equity_pct", "net_profit_margin_pct"])
    ratios = ratios.sort_values(["company_id", "year_num"])
    return ratios.groupby("company_id", as_index=False).tail(1)


def percent_rank(values, inverse=False):
    s = pd.to_numeric(values, errors="coerce")
    valid = s.dropna()
    pct = pd.Series(np.nan, index=s.index, dtype=float)
    if len(valid) == 0:
        pct.loc[:] = 0.5
    elif len(valid) == 1:
        pct.loc[valid.index] = 1.0
    else:
        ranks = valid.rank(method="min", pct=True)
        pct.loc[valid.index] = (ranks - ranks.min()) / (ranks.max() - ranks.min())
    if inverse:
        pct = 1 - pct
    return pct.fillna(0.5)


def build_peer_percentiles():
    conn = sqlite3.connect(DB_PATH)
    ratios = latest_ratios(conn)
    peer_groups = pd.read_sql("SELECT peer_group_name, company_id, is_benchmark FROM peer_groups", conn)
    rows = []

    for group_name, members in peer_groups.groupby("peer_group_name"):
        data = members.merge(ratios, on="company_id", how="left")
        for metric, inverse in METRICS.items():
            if metric not in data.columns:
                data[metric] = np.nan
            ranks = percent_rank(data[metric], inverse=inverse)
            for idx, row in data.iterrows():
                value = row.get(metric)
                rows.append({
                    "company_id": row["company_id"],
                    "peer_group_name": group_name,
                    "metric": metric,
                    "value": None if pd.isna(value) else float(value),
                    "percentile_rank": float(ranks.loc[idx]),
                    "year": row.get("year"),
                })

    out = pd.DataFrame(rows)
    out.to_sql("peer_percentiles", conn, if_exists="replace", index=False)
    OUTPUT_DIR.mkdir(exist_ok=True)
    out.to_csv(OUTPUT_DIR / "peer_percentiles.csv", index=False)
    conn.close()
    print(f"peer_percentiles rows: {len(out)}")
    return out


def find_peer_group(company_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT peer_group_name FROM peer_groups WHERE company_id = ?",
        conn,
        params=(company_id,),
    )
    conn.close()
    if df.empty:
        return "No peer group assigned"
    return df["peer_group_name"].iloc[0]


if __name__ == "__main__":
    build_peer_percentiles()
