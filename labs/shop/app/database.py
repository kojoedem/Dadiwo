import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "shop.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            code TEXT PRIMARY KEY,
            discount_percent REAL NOT NULL,
            is_used INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            total_price REAL NOT NULL,
            items TEXT NOT NULL,
            status TEXT DEFAULT 'COMPLETED',
            flag TEXT DEFAULT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM products")
    if cursor.fetchone()["count"] == 0:
        products = [
            ("Cybersecurity Lab Router", 299.99, 10),
            ("GNS3 / EVE-NG Workstation", 1499.00, 5),
            ("Hak5 WiFi Pineapple Simulator", 199.50, 15),
            ("SANS Master Security Pass", 4500.00, 2)
        ]
        cursor.executemany("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", products)

        cursor.execute("INSERT INTO coupons (code, discount_percent, is_used) VALUES ('DISCOUNT20', 20.0, 0)")
        cursor.execute("INSERT INTO coupons (code, discount_percent, is_used) VALUES ('FREEVIP100', 100.0, 0)")

        cursor.execute("""
            INSERT INTO orders (order_id, customer_name, total_price, items, flag)
            VALUES ('ORD-9000', 'E-Commerce Admin Core', 0.00, 'SANS Master Pass', 'FLAG{SHOP_COUPON_REUSE_PRICING_FLAW_2026}')
        """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
