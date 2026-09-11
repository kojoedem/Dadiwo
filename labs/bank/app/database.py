import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "bank.db")

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
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            balance REAL NOT NULL DEFAULT 0.0,
            is_admin INTEGER DEFAULT 0,
            flag TEXT DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wire_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_account TEXT NOT NULL,
            recipient_account TEXT NOT NULL,
            amount REAL NOT NULL,
            memo TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        sample_users = [
            ("user1", "bankpass123", "Kwame Addo", "ACC-BANK-101", 5000.00, 0, None),
            ("user2", "serwaa2026", "Ama Serwaa", "ACC-BANK-102", 1250.75, 0, None),
            ("admin", "SuperBankAdmin2026!", "Chief Compliance Officer", "ACC-BANK-999", 1000000.00, 1, "FLAG{BANK_SQLI_XSS_IDOR_COMPROMISE_2026}")
        ]

        cursor.executemany("""
            INSERT INTO users (username, password, full_name, account_number, balance, is_admin, flag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_users)

        cursor.execute("""
            INSERT INTO wire_transfers (sender_account, recipient_account, amount, memo)
            VALUES ('ACC-BANK-101', 'ACC-BANK-102', 250.00, 'Monthly Allowance')
        """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
