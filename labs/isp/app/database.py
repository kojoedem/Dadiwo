import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "isp.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            package_speed TEXT NOT NULL,
            router_ip TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            flag TEXT DEFAULT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM customers")
    if cursor.fetchone()["count"] == 0:
        sample_customers = [
            ("ISP-1001", "Accra Cybernet Ltd", "100 Mbps Fiber", "192.168.10.1", "ACTIVE", None),
            ("ISP-1002", "Kumasi Tech Hub", "500 Mbps Dedicated", "192.168.10.2", "ACTIVE", None),
            ("ISP-9000", "ISP Infrastructure Core", "10 Gbps Backbone", "127.0.0.1", "ADMIN_CORE", "FLAG{ISP_COMMAND_INJECTION_RADIUS_EXPLOIT_2026}")
        ]

        cursor.executemany("""
            INSERT INTO customers (account_id, customer_name, package_speed, router_ip, status, flag)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_customers)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
