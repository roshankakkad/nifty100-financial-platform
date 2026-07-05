from pathlib import Path
import sqlite3
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from screener.presets import run_all_presets


def test_six_presets_return_expected_range():
    results = run_all_presets()
    assert len(results) == 6
    for name, df in results.items():
        count = df["company_id"].nunique()
        assert 5 <= count <= 50, f"{name} returned {count} companies"


def test_quality_compounder_rules_hold():
    df = run_all_presets()["quality_compounder"]
    assert (df["return_on_equity_pct"] > 15).all()
    non_financials = df[df["broad_sector"] != "Financials"]
    assert (non_financials["debt_to_equity"] <= 1).all()


def test_peer_percentiles_table_exists():
    conn = sqlite3.connect(ROOT / "data" / "db" / "nifty100.db")
    count = pd.read_sql("SELECT COUNT(*) AS c FROM peer_percentiles", conn)["c"].iloc[0]
    groups = pd.read_sql("SELECT COUNT(DISTINCT peer_group_name) AS c FROM peer_percentiles", conn)["c"].iloc[0]
    conn.close()
    assert count > 0
    assert groups == 11


def test_it_services_highest_roe_gets_highest_percentile():
    conn = sqlite3.connect(ROOT / "data" / "db" / "nifty100.db")
    df = pd.read_sql(
        """
        SELECT company_id, value, percentile_rank
        FROM peer_percentiles
        WHERE peer_group_name='IT Services'
          AND metric='return_on_equity_pct'
        ORDER BY value DESC
        """,
        conn,
    )
    conn.close()
    assert not df.empty
    assert df.iloc[0]["percentile_rank"] == df["percentile_rank"].max()
