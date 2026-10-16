
from pathlib import Path
import sqlite3

import pandas as pd


# Resolve paths relative to the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = PROJECT_ROOT / "data" / "Online Retail.xlsx"
DATABASE_PATH = PROJECT_ROOT / "data" / "retail.db"


def main():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"Retail dataset not found: {EXCEL_PATH}"
        )

    print("Reading Excel dataset...")
    df = pd.read_excel(EXCEL_PATH)

    print(f"Original rows: {len(df):,}")
    print(f"Original columns: {list(df.columns)}")

    # Convert column names into consistent snake_case names.
    df = df.rename(
        columns={
            "InvoiceNo": "invoice_no",
            "StockCode": "stock_code",
            "Description": "description",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "UnitPrice": "unit_price",
            "CustomerID": "customer_id",
            "Country": "country",
        }
    )

    required_columns = [
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "country",
    ]

    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing expected columns: {sorted(missing)}"
        )

    df = df[required_columns].copy()

    # Normalize data types.
    df["invoice_no"] = df["invoice_no"].astype(str)
    df["stock_code"] = df["stock_code"].astype(str)
    df["description"] = df["description"].astype("string")
    df["country"] = df["country"].astype("string")

    df["quantity"] = pd.to_numeric(
        df["quantity"], errors="raise"
    ).astype("int64")

    df["unit_price"] = pd.to_numeric(
        df["unit_price"], errors="raise"
    )

    df["invoice_date"] = pd.to_datetime(
        df["invoice_date"], errors="raise"
    ).dt.strftime("%Y-%m-%d %H:%M:%S")

    # Customer IDs can be missing. Preserve those as SQL NULL.
    customer_ids = pd.to_numeric(
        df["customer_id"], errors="coerce"
    )
    df["customer_id"] = customer_ids.map(
        lambda value: int(value)
        if pd.notna(value)
        else None
    )

    print("Loading records into SQLite...")

    with sqlite3.connect(DATABASE_PATH) as conn:
        df.to_sql(
            "online_retail",
            conn,
            if_exists="replace",
            index=False,
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_retail_invoice
            ON online_retail(invoice_no)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_retail_customer
            ON online_retail(customer_id)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_retail_date
            ON online_retail(invoice_date)
            """
        )

        row_count = conn.execute(
            "SELECT COUNT(*) FROM online_retail"
        ).fetchone()[0]

        invoice_count = conn.execute(
            "SELECT COUNT(DISTINCT invoice_no) "
            "FROM online_retail"
        ).fetchone()[0]

        product_count = conn.execute(
            "SELECT COUNT(DISTINCT stock_code) "
            "FROM online_retail"
        ).fetchone()[0]

        customer_count = conn.execute(
            "SELECT COUNT(DISTINCT customer_id) "
            "FROM online_retail "
            "WHERE customer_id IS NOT NULL"
        ).fetchone()[0]

        missing_customers = conn.execute(
            "SELECT COUNT(*) FROM online_retail "
            "WHERE customer_id IS NULL"
        ).fetchone()[0]

        date_range = conn.execute(
            "SELECT MIN(invoice_date), MAX(invoice_date) "
            "FROM online_retail"
        ).fetchone()

    print("\nImport completed successfully!")
    print(f"Database: {DATABASE_PATH}")
    print(f"Transaction rows: {row_count:,}")
    print(f"Unique invoices: {invoice_count:,}")
    print(f"Unique products: {product_count:,}")
    print(f"Identified customers: {customer_count:,}")
    print(f"Rows without customer IDs: {missing_customers:,}")
    print(f"Date range: {date_range[0]} to {date_range[1]}")


if __name__ == "__main__":
    main()
