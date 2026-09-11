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
            environment_purpose TEXT NOT NULL DEFAULT 'cybersecurity',
            tags TEXT NOT NULL DEFAULT 'web, security',
            status TEXT NOT NULL DEFAULT 'stopped',
            container_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dns_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            dns_enabled INTEGER NOT NULL DEFAULT 0,
            host_ip TEXT NOT NULL DEFAULT '127.0.0.1',
            dns_port INTEGER NOT NULL DEFAULT 5353
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM dns_settings")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
            INSERT INTO dns_settings (id, dns_enabled, host_ip, dns_port)
            VALUES (1, 0, '127.0.0.1', 5353)
        """)

    try:
        cursor.execute("ALTER TABLE microservices ADD COLUMN environment_purpose TEXT NOT NULL DEFAULT 'cybersecurity'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE microservices ADD COLUMN tags TEXT NOT NULL DEFAULT 'web, security'")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT COUNT(*) as count FROM microservices")
    if cursor.fetchone()["count"] == 0:
        initial_labs = [
            ("atm", "🏧 Dadiwoo ATM Transaction Processing Lab", "Financial", "Simulates ATM web UI, balance operations, withdrawals, and transfers with IDOR and logic vulnerabilities.", 8080, 8080, "atm.lab", "beginner", "cybersecurity", "web, financial, idor, bola, logic-flaw", "stopped", "atm-lab-container"),
            ("bank", "🏦 Dadiwoo Online Banking Portal Lab", "Financial", "Full banking platform featuring user registration, wire transfers, transaction search, and SQLi/XSS/CSRF vulnerabilities.", 8081, 8081, "bank.lab", "intermediate", "cybersecurity", "web, financial, sqli, xss, csrf", "stopped", "bank-lab-container"),
            ("isp", "🌐 Dadiwoo ISP Customer Management Portal", "Telecom", "Customer portal integrated with simulated RADIUS, Zabbix poller, and command injection diagnostic tools.", 8082, 8082, "isp.lab", "advanced", "cybersecurity", "wifi, network, command-injection, radius, telecom", "stopped", "isp-lab-container"),
            ("school", "🎓 Dadiwoo University Student Portal", "Education", "Academic portal for grade lookup, fee payment, and document upload with insecure file upload flaws.", 8083, 8083, "school.lab", "beginner", "cybersecurity", "web, education, osint, file-upload, idor", "stopped", "school-lab-container"),
            ("shop", "🛒 Dadiwoo E-Commerce Platform Lab", "Retail", "Online store featuring catalog browsing, coupon logic flaws, client price tampering, and order lookup IDOR.", 8084, 8084, "shop.lab", "intermediate", "cybersecurity", "web, retail, logic-flaw, price-tampering, idor", "stopped", "shop-lab-container"),
            ("mobile", "📱 Dadiwoo Smartphone & Bluetooth Simulator", "Mobile", "Simulates smartphone Bluetooth discoverability, contact exfiltration, BlueBorne flaws, and weak pairing PINs.", 8085, 8085, "mobile.lab", "beginner", "cybersecurity", "bluetooth, mobile, wireless, osint, blueborne, phone", "stopped", "mobile-lab-container")
        ]

        cursor.executemany("""
            INSERT INTO microservices (id, name, category, description, default_port, configured_port, local_domain, difficulty, environment_purpose, tags, status, container_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, initial_labs)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
