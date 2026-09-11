import sqlite3
import os

DB_PATH = os.environ.get("MANAGER_DB_PATH", "manager.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS microservices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            default_port INTEGER NOT NULL,
            configured_port INTEGER NOT NULL,
            local_domain TEXT NOT NULL,
            difficulty TEXT NOT NULL DEFAULT 'beginner',
            status TEXT NOT NULL DEFAULT 'stopped',
            container_name TEXT NOT NULL
        )
    """)

    # Check if table is empty, seed available microservices
    cursor.execute("SELECT COUNT(*) as count FROM microservices")
    if cursor.fetchone()["count"] == 0:
        initial_labs = [
            ("atm", "🏧 ATM Transaction Processing Lab", "Financial", "Simulates ATM web UI, balance operations, withdrawals, and transfers with IDOR and logic vulnerabilities.", 8080, 8080, "atm.lab", "beginner", "stopped", "atm-lab-container"),
            ("bank", "🏦 Online Banking Portal Lab", "Financial", "Full banking platform featuring user registration, wire transfers, transaction search, and SQLi/XSS/CSRF vulnerabilities.", 8081, 8081, "bank.lab", "intermediate", "stopped", "bank-lab-container"),
            ("isp", "🌐 ISP Customer Management Portal", "Telecom", "Customer portal integrated with simulated RADIUS and Zabbix network monitoring endpoints.", 8082, 8082, "isp.lab", "advanced", "stopped", "isp-lab-container"),
            ("school", "🎓 Student University Portal", "Education", "Academic portal for grade lookup, fee payment, and course registration with access control flaws.", 8083, 8083, "school.lab", "beginner", "stopped", "school-lab-container")
        ]

        cursor.executemany("""
            INSERT INTO microservices (id, name, category, description, default_port, configured_port, local_domain, difficulty, status, container_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, initial_labs)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
