from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "nifty100.db"
RADAR_DIR = ROOT / "reports" / "radar_charts"

AXES = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "composite_quality_score",
]
LABELS = ["ROE", "ROCE", "NPM", "D/E", "FCF", "PAT CAGR", "Rev CAGR", "Score"]


def latest_ratios(conn):
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    companies = pd.read_sql("SELECT id FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    ratios = ratios.merge(sectors, on="company_id", how="left")
    ratios["year_num"] = pd.to_numeric(ratios["year_num"], errors="coerce")
    ratios = ratios.dropna(subset=["year_num", "return_on_equity_pct", "net_profit_margin_pct"])
    ratios = ratios.sort_values(["company_id", "year_num"]).groupby("company_id", as_index=False).tail(1)
    ratios = companies.rename(columns={"id": "company_id"}).merge(ratios, on="company_id", how="left")
    return ratios


def add_scores(frame):
    out = frame.copy()
    for col in AXES:
        s = pd.to_numeric(out[col], errors="coerce")
        if col == "debt_to_equity":
            s = -s
        lo, hi = s.quantile(0.10), s.quantile(0.90)
        if pd.isna(lo) or pd.isna(hi) or hi == lo:
            out[col + "_score"] = 50.0
        else:
            out[col + "_score"] = ((s.clip(lo, hi) - lo) / (hi - lo) * 100).fillna(50)
    return out


def draw_chart(company_id, group_name, company_scores, reference_scores, reference_label):
    vals = company_scores + company_scores[:1]
    ref = reference_scores + reference_scores[:1]
    angles = np.linspace(0, 2 * np.pi, len(AXES), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(7, 7))
    ax = plt.subplot(111, polar=True)
    ax.plot(angles, vals, linewidth=2, label=company_id)
    ax.fill(angles, vals, alpha=0.25)
    ax.plot(angles, ref, linewidth=2, linestyle="--", label=reference_label)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(LABELS, fontsize=9)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_ylim(0, 100)
    ax.set_title(f"{company_id} - {group_name}", pad=20, fontsize=12)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.12))
    RADAR_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(RADAR_DIR / f"{company_id}_radar.png", dpi=130)
    plt.close(fig)


def generate_radar_charts():
    conn = sqlite3.connect(DB_PATH)
    ratios = latest_ratios(conn)
    peer_groups = pd.read_sql("SELECT peer_group_name, company_id FROM peer_groups", conn)
    conn.close()

    # remove old charts so the report is reproducible
    RADAR_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in RADAR_DIR.glob("*_radar.png"):
        old_file.unlink()

    score_cols = [c + "_score" for c in AXES]
    all_scored = add_scores(ratios)
    nifty_avg = all_scored[score_cols].mean().tolist()
    assigned = set(peer_groups["company_id"].dropna())

    for group_name, members in peer_groups.groupby("peer_group_name"):
        data = members.merge(ratios, on="company_id", how="left")
        if data.empty:
            continue
        data = add_scores(data)
        peer_avg = data[score_cols].mean().tolist()
        for _, row in data.iterrows():
            draw_chart(row["company_id"], group_name, row[score_cols].tolist(), peer_avg, "Peer Avg")

    for _, row in all_scored[~all_scored["company_id"].isin(assigned)].iterrows():
        draw_chart(row["company_id"], "No Peer Group", row[score_cols].tolist(), nifty_avg, "Nifty 100 Avg")

    print(f"radar charts saved to {RADAR_DIR}")


if __name__ == "__main__":
    generate_radar_charts()
