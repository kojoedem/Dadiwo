import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "bitroot.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subdomains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subdomain TEXT UNIQUE NOT NULL,
            full_domain TEXT NOT NULL,
            status TEXT NOT NULL, -- 'alive' or 'dead'
            service_name TEXT NOT NULL,
            description TEXT NOT NULL,
            waf_type TEXT DEFAULT 'none', -- 'cloudflare', 'modsecurity', 'none'
            ip_address TEXT DEFAULT '127.0.0.1'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recon_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            client_ip TEXT,
            requested_host TEXT,
            user_agent TEXT,
            status_code INTEGER
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM subdomains")
    if cursor.fetchone()["count"] == 0:
        subdomain_data = [
            # Active Subdomains (10)
            ("api", "api.bitroot.lab", "alive", "Bitroot REST API Gateway", "Core RESTful API service supporting OAuth2, JWT, and JSON payloads.", "cloudflare", "127.0.0.1"),
            ("dev", "dev.bitroot.lab", "alive", "Bitroot Developer Portal", "Developer documentation, API sandbox keys, and developer forum.", "none", "127.0.0.1"),
            ("admin", "admin.bitroot.lab", "alive", "Bitroot Executive Admin Portal", "Internal administrative management suite with Cloudflare WAF protection.", "cloudflare", "127.0.0.1"),
            ("portal", "portal.bitroot.lab", "alive", "Bitroot Customer Portal", "Client dashboard for managing subscriptions and support tickets.", "none", "127.0.0.1"),
            ("staging", "staging.bitroot.lab", "alive", "Bitroot Staging Environment", "Pre-production deployment environment for release candidate testing.", "modsecurity", "127.0.0.1"),
            ("auth", "auth.bitroot.lab", "alive", "Bitroot Identity Provider (SSO)", "Centralized Single Sign-On (SSO) and OAuth authentication authority.", "none", "127.0.0.1"),
            ("vpn", "vpn.bitroot.lab", "alive", "Bitroot Enterprise Gateway / VPN", "SSL-VPN gateway portal for remote workforce secure tunneling.", "modsecurity", "127.0.0.1"),
            ("shop", "shop.bitroot.lab", "alive", "Bitroot Corporate Store", "Merchandise and enterprise software licensing store front.", "none", "127.0.0.1"),
            ("blog", "blog.bitroot.lab", "alive", "Bitroot Tech Blog & News", "Official company tech blog, security advisories, and press releases.", "none", "127.0.0.1"),
            ("status", "status.bitroot.lab", "alive", "Bitroot Service Status Page", "Real-time uptime status monitor for cloud microservices.", "none", "127.0.0.1"),

            # Dead Subdomains (4)
            ("old-api", "old-api.bitroot.lab", "dead", "Deprecated v1 API Endpoint", "Decommissioned v1 REST API endpoint. Returns 503 Service Unavailable.", "none", "0.0.0.0"),
            ("legacy", "legacy.bitroot.lab", "dead", "Legacy Enterprise System", "Old mainframe migration site offline since 2021. Returns 503 Service Unavailable.", "none", "0.0.0.0"),
            ("test-internal", "test-internal.bitroot.lab", "dead", "Internal QA Node", "Internal QA test runner node unreachable from public network. Returns 404 Not Found.", "none", "0.0.0.0"),
            ("sandbox", "sandbox.bitroot.lab", "dead", "Decommissioned Testing Sandbox", "Expired developer sandbox environment. Returns 503 Service Unavailable.", "none", "0.0.0.0"),
        ]

        cursor.executemany("""
            INSERT INTO subdomains (subdomain, full_domain, status, service_name, description, waf_type, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, subdomain_data)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
