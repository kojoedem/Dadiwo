import sqlite3
import os
from typing import Optional

DB_PATH = os.environ.get("DB_PATH", "atm.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT UNIQUE NOT NULL,
            card_number TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL,
            holder_name TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0.0,
            account_type TEXT NOT NULL DEFAULT 'Savings',
            is_admin INTEGER NOT NULL DEFAULT 0,
            flag TEXT DEFAULT NULL
        )
    """)

    # Create transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            recipient_account TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_number) REFERENCES accounts (account_number)
        )
    """)

    # Check if accounts table is empty
    cursor.execute("SELECT COUNT(*) as count FROM accounts")
    if cursor.fetchone()["count"] == 0:
        sample_accounts = [
            ("ACC-1001", "4000123456781001", "1234", "Kofi Mensah", 2500.50, "Savings", 0, None),
            ("ACC-1002", "4000123456781002", "5678", "Ama Serwaa", 150.00, "Checking", 0, None),
            ("ACC-1003", "4000123456781003", "9999", "Kwame Osei", 12000.75, "Business", 0, None),
            ("ACC-9000", "4000999999999000", "0000", "System Admin", 999999.99, "Master", 1, "FLAG{ATM_IDOR_BOLA_AUTHORIZATION_BYPASS_2026}"),
        ]

        cursor.executemany("""
            INSERT INTO accounts (account_number, card_number, pin, holder_name, balance, account_type, is_admin, flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_accounts)

        # Initial transactions
        sample_transactions = [
            ("ACC-1001", "DEPOSIT", 2500.50, None),
            ("ACC-1002", "DEPOSIT", 150.00, None),
            ("ACC-1003", "DEPOSIT", 12000.75, None),
            ("ACC-9000", "INITIAL_RESERVE", 999999.99, None),
        ]
        cursor.executemany("""
            INSERT INTO transactions (account_number, transaction_type, amount, recipient_account)
            VALUES (?, ?, ?, ?)
        """, sample_transactions)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
