import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

_configured_path = Path(
    os.getenv("DATABASE_PATH", "data/shop.db")
).expanduser()

DATABASE_PATH = (
    _configured_path
    if _configured_path.is_absolute()
    else PROJECT_ROOT / _configured_path
)


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def create_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        country TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)

    # Customers
    cursor.executemany(
        """
        INSERT OR IGNORE INTO customers
        (customer_id, name, email, country)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1, "Alice Johnson", "alice@example.com", "USA"),
            (2, "Bob Smith", "bob@example.com", "UK"),
            (3, "Carlos Garcia", "carlos@example.com", "Spain"),
            (4, "Diana Brown", "diana@example.com", "USA"),
            (5, "Ethan Wilson", "ethan@example.com", "Canada"),
        ],
    )

    # Products
    cursor.executemany(
        """
        INSERT OR IGNORE INTO products
        (product_id, name, category, price)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1, "Laptop", "Electronics", 1200.00),
            (2, "Keyboard", "Electronics", 100.00),
            (3, "Mouse", "Electronics", 50.00),
            (4, "Desk Chair", "Furniture", 300.00),
            (5, "Monitor", "Electronics", 400.00),
        ],
    )

    # Orders
    cursor.executemany(
        """
        INSERT OR IGNORE INTO orders
        (order_id, customer_id, order_date)
        VALUES (?, ?, ?)
        """,
        [
            (1, 1, "2026-01-10"),
            (2, 2, "2026-01-15"),
            (3, 1, "2026-02-01"),
            (4, 3, "2026-02-10"),
            (5, 4, "2026-02-15"),
            (6, 5, "2026-03-01"),
        ],
    )

    # Order items
    cursor.executemany(
        """
        INSERT OR IGNORE INTO order_items
        (order_item_id, order_id, product_id, quantity)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1, 1, 1, 1),  # Alice: Laptop
            (2, 1, 2, 2),  # Alice: 2 Keyboards
            (3, 2, 3, 3),  # Bob: 3 Mice
            (4, 2, 5, 1),  # Bob: Monitor
            (5, 3, 4, 1),  # Alice: Chair
            (6, 3, 3, 2),  # Alice: 2 Mice
            (7, 4, 1, 1),  # Carlos: Laptop
            (8, 4, 5, 2),  # Carlos: 2 Monitors
            (9, 5, 2, 3),  # Diana: 3 Keyboards
            (10, 6, 4, 2), # Ethan: 2 Chairs
        ],
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print("Database created and populated.")