from pathlib import Path
import pandas as pd

from normaliser import (
    normalize_ticker,
    normalize_year,
    normalize_column_names,
    clean_text_columns,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"


CORE_FILES = {
    "companies": "companies.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "prosandcons": "prosandcons.xlsx",
}

SUPPLEMENTARY_FILES = {
    "sectors": "sectors.xlsx",
    "stock_prices": "stock_prices.xlsx",
    "market_cap": "market_cap.xlsx",
    "financial_ratios": "financial_ratios.xlsx",
    "peer_groups": "peer_groups.xlsx",
}


def load_excel_file(file_path, header):
    """Load Excel file using the correct header row."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_excel(file_path, header=header)
    df = normalize_column_names(df)
    df = clean_text_columns(df)

    return df


def normalize_dataframe(df, table_name):
    """Apply table-specific cleaning rules."""
    df = df.copy()

    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)

    if table_name == "companies" and "id" in df.columns:
        df["id"] = df["id"].apply(normalize_ticker)

    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df = df.drop_duplicates()

    return df


def load_all_datasets():
    """Load all 7 core and 5 supplementary datasets."""
    datasets = {}

    print("Loading core datasets...")
    for table_name, filename in CORE_FILES.items():
        path = RAW_DATA_PATH / filename
        df = load_excel_file(path, header=1)
        df = normalize_dataframe(df, table_name)
        datasets[table_name] = df
        print(f"Loaded {table_name}: {len(df)} rows")

    print("\nLoading supplementary datasets...")
    for table_name, filename in SUPPLEMENTARY_FILES.items():
        path = RAW_DATA_PATH / filename
        df = load_excel_file(path, header=0)
        df = normalize_dataframe(df, table_name)
        datasets[table_name] = df
        print(f"Loaded {table_name}: {len(df)} rows")

    return datasets


def save_preview_csvs(datasets):
    """Save first 10 rows of each dataset for checking."""
    output_path = PROJECT_ROOT / "output" / "preview"
    output_path.mkdir(parents=True, exist_ok=True)

    for table_name, df in datasets.items():
        df.head(10).to_csv(output_path / f"{table_name}_preview.csv", index=False)


if __name__ == "__main__":
    datasets = load_all_datasets()
    save_preview_csvs(datasets)