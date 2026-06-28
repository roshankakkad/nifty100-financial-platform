from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"


def create_database():
    """Create SQLite database using schema.sql."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
            schema_sql = file.read()

        conn.executescript(schema_sql)
        conn.commit()

    print("Database created successfully.")
    print(f"Database path: {DB_PATH}")


if __name__ == "__main__":
    create_database()