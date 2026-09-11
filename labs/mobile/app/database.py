import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "mobile.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_info (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            device_name TEXT NOT NULL DEFAULT 'Pixel 8 Pro (Victim Mobile)',
            bluetooth_mac TEXT NOT NULL DEFAULT 'AA:BB:CC:11:22:33',
            bluetooth_state TEXT NOT NULL DEFAULT 'DISCOVERABLE',
            pairing_code TEXT NOT NULL DEFAULT '0000',
            owner_name TEXT NOT NULL DEFAULT 'Kofi Mensah',
            flag TEXT DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            secret_note TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bluetooth_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attacker_mac TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM device_info")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
            INSERT INTO device_info (id, device_name, bluetooth_mac, bluetooth_state, pairing_code, owner_name, flag)
            VALUES (1, 'Pixel 8 Pro (Victim Mobile)', 'AA:BB:CC:11:22:33', 'DISCOVERABLE', '0000', 'Kofi Mensah', 'FLAG{BLUETOOTH_BLUEBORNE_EXFILTRATION_2026}')
        """)

        sample_contacts = [
            ("Ama Serwaa", "+233241234567", "Personal Bank PIN: 9876"),
            ("Kwame Addo", "+233209876543", "Wi-Fi Password: GhanaSecLab2026!"),
            ("Chief Compliance Officer", "+233550009999", "Master Vault Backup Key: FLAG{BLUETOOTH_BLUEBORNE_EXFILTRATION_2026}")
        ]
        cursor.executemany("INSERT INTO contacts (name, phone_number, secret_note) VALUES (?, ?, ?)", sample_contacts)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
