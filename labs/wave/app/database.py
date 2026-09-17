import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "wave.db")

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
            pin TEXT NOT NULL DEFAULT '1234',
            full_name TEXT NOT NULL,
            bio TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            workplace TEXT,
            job_title TEXT,
            relationship_status TEXT,
            profile_pic TEXT,
            flag TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            caption TEXT,
            location_tag TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT,
            file_size_kb REAL NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode_type TEXT UNIQUE NOT NULL,
            issuer TEXT NOT NULL,
            subject TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            key_algorithm TEXT NOT NULL,
            key_size INTEGER NOT NULL,
            cipher_suite TEXT NOT NULL,
            status TEXT NOT NULL,
            private_key_leaked INTEGER NOT NULL DEFAULT 0,
            private_key_pem TEXT,
            public_cert_pem TEXT NOT NULL,
            flag TEXT DEFAULT NULL,
            exploit_instructions TEXT
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        sample_users = [
            (
                "alex_ceo", "1234", "Alex Mercer",
                "CEO & Founder at Apex Wave Dynamics. Technology enthusiast, keynote speaker & angel investor.",
                "alex.mercer@apexwave.lab", "+1-555-019-2831", "Seattle, WA",
                "Apex Wave Dynamics", "Chief Executive Officer", "Married",
                "avatar_alex.jpg", "FLAG{WAVE_OSINT_CEO_LOCATION_RECON_2026}"
            ),
            (
                "sarah_sec", "1234", "Sarah Connor",
                "Lead Cybersecurity Engineer. Threat hunting, Incident Response & Zero Trust Architectures.",
                "s.connor@apexwave.lab", "+1-555-014-9982", "Austin, TX",
                "Apex Wave Dynamics", "Lead Cyber Security Engineer", "Single",
                "avatar_sarah.jpg", None
            ),
            (
                "david_dev", "1234", "David Miller",
                "Senior Full Stack Developer building scalable cloud microservices. Coffee & Python.",
                "david.m@devlabs.io", "+1-555-018-4421", "San Francisco, CA",
                "DevLabs Global", "Senior Developer", "In a relationship",
                "avatar_david.jpg", None
            ),
            (
                "elena_mkt", "1234", "Elena Rostova",
                "VP of Global Marketing & Public Relations. Digital campaigns, social growth & brand strategy.",
                "elena.r@wavechat.lab", "+1-555-012-7710", "New York, NY",
                "Wave Chat Inc.", "VP of Marketing", "Single",
                "avatar_elena.jpg", None
            ),
            (
                "marcus_ops", "1234", "Marcus Vance",
                "Infrastructure & Cloud Operations Lead. Kubernetes, DevSecOps & High Availability Systems.",
                "m.vance@wavechat.lab", "+1-555-016-3390", "Chicago, IL",
                "Wave Chat Inc.", "Cloud Ops Lead", "Married",
                "avatar_marcus.jpg", None
            )
        ]

        cursor.executemany("""
            INSERT INTO users (username, pin, full_name, bio, email, phone, location, workplace, job_title, relationship_status, profile_pic, flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_users)

        sample_posts = [
            ("alex_ceo", "Excited to launch our new Wave Chat platform! Connectivity redefined. 🌊🚀", "Seattle HQ"),
            ("sarah_sec", "Performing annual penetration tests on our perimeter services today. Safety first! 🔐", "Security Lab"),
            ("david_dev", "Deploying microservices with lightweight asset pipeline. Clean code everyday!", "San Francisco HQ")
        ]

        for username, caption, loc in sample_posts:
            cursor.execute("INSERT INTO posts (username, caption, location_tag) VALUES (?, ?, ?)", (username, caption, loc))

    cursor.execute("SELECT COUNT(*) as count FROM certificates")
    if cursor.fetchone()["count"] == 0:
        weak_pem = """-----BEGIN CERTIFICATE-----
MIICvDCCAaQCCQCx8q+2b
-----END CERTIFICATE-----"""
        weak_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAz81... [WEAK 1024-BIT RSA LEAKED PRIVATE KEY] ...
-----END RSA PRIVATE KEY-----"""

        secure_pem = """-----BEGIN CERTIFICATE-----
MIIF4zCCBMugAwIBAgIQ... [SECURE 4096-BIT RSA / ECDSA CERTIFICATE] ...
-----END CERTIFICATE-----"""

        certs = [
            (
                "vulnerable",
                "Let's Encrypt Authority X3 (Staging Test CA)",
                "CN=wave.lab, O=Wave Chat Test Network, C=US",
                "2023-01-01 00:00:00 UTC",
                "2023-12-31 23:59:59 UTC (EXPIRED)",
                "RSA",
                1024,
                "TLS_RSA_WITH_3DES_EDE_CBC_SHA (Obsolete / Broken)",
                "CRITICAL_VULNERABLE",
                1,
                weak_key,
                weak_pem,
                "FLAG{LETS_ENCRYPT_STAGING_KEY_EXPLOITED_2026}",
                "Exploitation Guide: The Let's Encrypt Staging private key is leaked and key length is weak (1024-bit RSA). In Kali Linux, load the private key into Wireshark (Edit -> Preferences -> Protocols -> TLS -> RSA Keys List) to decrypt captured pcap files or execute a spoofed SSL/TLS Man-in-the-Middle proxy using bettercap."
            ),
            (
                "secure",
                "Let's Encrypt ISRG Root X1 (Production Production Trusted)",
                "CN=wave.lab, O=Wave Chat Secure Network, C=US",
                "2026-01-01 00:00:00 UTC",
                "2027-01-01 23:59:59 UTC (VALID)",
                "ECDSA P-384 / RSA",
                4096,
                "TLS_AES_256_GCM_SHA384 (TLS 1.3 Perfect Forward Secrecy)",
                "SECURE",
                0,
                None,
                secure_pem,
                None,
                "Secure Certificate Defense: Protected by 4096-bit RSA / ECDSA keys, TLS 1.3 Perfect Forward Secrecy (PFS), and strict HSTS headers. Exploitation via key extraction or passive PCAP decryption in Kali Linux is mathematically impossible."
            )
        ]

        cursor.executemany("""
            INSERT INTO certificates (mode_type, issuer, subject, valid_from, valid_until, key_algorithm, key_size, cipher_suite, status, private_key_leaked, private_key_pem, public_cert_pem, flag, exploit_instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, certs)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
