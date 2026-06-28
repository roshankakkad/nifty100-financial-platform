import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"


def main():
    conn = sqlite3.connect(DB_PATH)

    query = """
    WITH latest_year AS (
        SELECT company_id, MAX(year) AS latest_year
        FROM financial_ratios
        GROUP BY company_id
    )
    SELECT f.company_id,
           f.year,
           f.return_on_equity_pct,
           f.debt_to_equity
    FROM financial_ratios f
    JOIN latest_year l
      ON f.company_id = l.company_id
     AND f.year = l.latest_year
    WHERE f.return_on_equity_pct > 15
      AND f.debt_to_equity < 1
    ORDER BY f.return_on_equity_pct DESC
    """

    result = pd.read_sql(query, conn)

    print(result)
    print(f"\nTotal screened companies: {result['company_id'].nunique()}")

    conn.close()


if __name__ == "__main__":
    main()