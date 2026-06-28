from pathlib import Path
from datetime import datetime
import sqlite3
import pandas as pd

from loader import load_all_datasets

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output"


def clean_df(df):
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)
    return df.where(pd.notnull(df), None)


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    datasets = load_all_datasets()
    audit = []

    with sqlite3.connect(DB_PATH) as conn:
        for table_name, df in datasets.items():
            print(f"Loading {table_name}...")

            try:
                df = clean_df(df)
                df.to_sql(table_name, conn, if_exists="replace", index=False)

                audit.append({
                    "table": table_name,
                    "rows_in": len(df),
                    "rows_loaded": len(df),
                    "rejected": 0,
                    "status": "SUCCESS",
                    "error": "",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                print(f"{table_name}: SUCCESS")

            except Exception as error:
                audit.append({
                    "table": table_name,
                    "rows_in": len(df),
                    "rows_loaded": 0,
                    "rejected": len(df),
                    "status": "FAILED",
                    "error": str(error),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                print(f"{table_name}: FAILED")
                print(error)

        conn.commit()

    pd.DataFrame(audit).to_csv(OUTPUT_PATH / "load_audit.csv", index=False)
    print("Load audit saved.")


if __name__ == "__main__":
    main()