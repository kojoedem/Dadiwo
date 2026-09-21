import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "apiwarehouse.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL DEFAULT 'guest',
            api_key TEXT UNIQUE NOT NULL,
            secret_key TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            price REAL NOT NULL DEFAULT 0.0,
            is_restricted INTEGER NOT NULL DEFAULT 0,
            owner_user_id INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_url TEXT NOT NULL,
            event_type TEXT NOT NULL,
            secret_token TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            client_ip TEXT NOT NULL,
            auth_method TEXT NOT NULL
        )
    """)

    # Seed initial data if empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        users = [
            ("guest_user", "guest", "ak_guest_88291029", "secret_guest_key", "guest@warehouse.lab"),
            ("operator_jane", "warehouse_worker", "ak_worker_99210482", "secret_worker_key", "jane@warehouse.lab"),
            ("admin_boss", "warehouse_admin", "ak_admin_77301948", "secret123", "admin@warehouse.lab"),
            ("auditor_sec", "security_auditor", "ak_auditor_31415926", "secret_auditor_key", "auditor@warehouse.lab")
        ]
        cursor.executemany("""
            INSERT INTO users (username, role, api_key, secret_key, email)
            VALUES (?, ?, ?, ?, ?)
        """, users)

    cursor.execute("SELECT COUNT(*) as count FROM inventory")
    if cursor.fetchone()["count"] == 0:
        items = [
            ("SKU-1001", "Quantum Server Rack X1", "Servers", 15, 12500.00, 0, 1),
            ("SKU-1002", "Industrial Router G8", "Networking", 42, 3400.00, 0, 1),
            ("SKU-1003", "Cryptographic Hardware Security Module (HSM)", "Security Hardware", 5, 89000.00, 1, 3),
            ("SKU-1004", "Tactical Surveillance Drone v4", "Drones", 12, 18500.00, 1, 3),
            ("SKU-1005", "Fiber Optic Transceiver 100G", "Networking", 120, 450.00, 0, 2),
            ("SKU-1006", "High-Density Lithium Battery Pack", "Power", 85, 1200.00, 0, 2),
            ("SKU-1007", "Classified Defense Comms Transponder", "Defense", 2, 250000.00, 1, 3)
        ]
        cursor.executemany("""
            INSERT INTO inventory (item_code, name, category, quantity, price, is_restricted, owner_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, items)

    cursor.execute("SELECT COUNT(*) as count FROM webhooks")
    if cursor.fetchone()["count"] == 0:
        webhooks = [
            (2, "http://127.0.0.1:8089/api/v1/debug/webhook-echo", "stock_low", "whsec_worker_123"),
            (3, "http://127.0.0.1:9000/api/v1/system/check-update", "inventory_export", "whsec_admin_999")
        ]
        cursor.executemany("""
            INSERT INTO webhooks (user_id, target_url, event_type, secret_token)
            VALUES (?, ?, ?, ?)
        """, webhooks)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
