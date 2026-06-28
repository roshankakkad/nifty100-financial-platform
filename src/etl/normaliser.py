from datetime import datetime
import pandas as pd


def normalize_ticker(value):
    """Normalize NSE ticker/company_id values."""
    if pd.isna(value):
        return None
    return str(value).strip().upper()


def normalize_column_names(df):
    """Convert column names to clean snake_case format."""
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("%", "percentage", regex=False)
        .str.replace("/", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return df


def normalize_year(value):
    """Normalize year values to a 4-digit format."""
    if pd.isna(value):
        return None

    value = str(value).strip()

    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    }

    if "-" in value:
        parts = value.split("-")
        if len(parts) == 2:
            month = parts[0].lower()[:3]
            year = parts[1]

            if len(year) == 2:
                year = "20" + year

            if month in month_map:
                return f"{year}-{month_map[month]}"

    return value


def clean_text_columns(df):
    """Strip spaces and line breaks from text columns."""
    df = df.copy()

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("\n", " ", regex=False)
            .str.strip()
        )

    return df