import sqlite3
import os
import secrets
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

DB_PATH = os.environ.get("DB_PATH", "ssh.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_rsa_keypair() -> tuple[str, str]:
    """Generates a valid 2048-bit RSA private and public key pair in OpenSSH format."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    ).decode('utf-8')
    return private_pem, public_pem

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssh_users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            home_dir TEXT NOT NULL,
            shell TEXT NOT NULL DEFAULT '/bin/bash',
            public_key TEXT DEFAULT NULL,
            ctf_flag TEXT DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssh_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            private_key_pem TEXT NOT NULL,
            public_key_pem TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssh_sessions (
            session_id TEXT PRIMARY KEY,
            client_ip TEXT NOT NULL,
            client_port INTEGER NOT NULL,
            username TEXT NOT NULL,
            auth_method TEXT NOT NULL,
            login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active',
            commands_count INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssh_fail2ban (
            ip_address TEXT PRIMARY KEY,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            banned_until DATETIME DEFAULT NULL,
            last_attempt DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssh_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            ssh_port INTEGER NOT NULL DEFAULT 2222,
            password_auth_enabled INTEGER NOT NULL DEFAULT 1,
            pubkey_auth_enabled INTEGER NOT NULL DEFAULT 1,
            fail2ban_enabled INTEGER NOT NULL DEFAULT 1,
            max_failed_attempts INTEGER NOT NULL DEFAULT 3,
            ban_duration_seconds INTEGER NOT NULL DEFAULT 300,
            restricted_shell_enabled INTEGER NOT NULL DEFAULT 0,
            custom_banner TEXT NOT NULL DEFAULT 'Dadiwoo Cyber Range Hardened SSH Gateway v2.4\nAuthorized Personnel Only.\n',
            allowed_ips TEXT NOT NULL DEFAULT '127.0.0.1,10.0.0.0/8,192.168.0.0/16'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssh_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            client_ip TEXT NOT NULL,
            username TEXT NOT NULL,
            auth_method TEXT NOT NULL,
            status TEXT NOT NULL,
            command TEXT DEFAULT NULL,
            details TEXT NOT NULL
        )
    """)

    # Seed Users
    cursor.execute("SELECT COUNT(*) as count FROM ssh_users")
    if cursor.fetchone()["count"] == 0:
        # Generate leak key pair for 'user'
        priv_pem, pub_pem = generate_rsa_keypair()

        user_seed = [
            ("user", "user123", "user", "/home/user", "/bin/bash", pub_pem, "FLAG{SSH_STANDARD_USER_SESSION_2026}"),
            ("admin", "AdminSecretPass2026!", "admin", "/root", "/bin/bash", None, "FLAG{SSH_PARAMIKO_BRUTE_FORCE_PWNED_2026}"),
            ("guest", "guest", "restricted", "/home/guest", "/bin/rbash", None, "FLAG{SSH_RESTRICTED_SHELL_ESCAPE_2026}")
        ]
        cursor.executemany("""
            INSERT INTO ssh_users (username, password, role, home_dir, shell, public_key, ctf_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, user_seed)

        cursor.execute("""
            INSERT INTO ssh_keys (key_name, username, private_key_pem, public_key_pem, description)
            VALUES ('id_rsa_user', 'user', ?, ?, 'Leaked RSA Private Key for User SSH Login')
        """, (priv_pem, pub_pem))

    # Seed Settings
    cursor.execute("SELECT COUNT(*) as count FROM ssh_settings")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
            INSERT INTO ssh_settings (id, ssh_port, password_auth_enabled, pubkey_auth_enabled, fail2ban_enabled, max_failed_attempts, ban_duration_seconds, restricted_shell_enabled, custom_banner, allowed_ips)
            VALUES (1, 2222, 1, 1, 1, 3, 300, 0, 'Dadiwoo Cyber Range Hardened SSH Gateway v2.4\nAuthorized Personnel Only.\n', '127.0.0.1,10.0.0.0/8,192.168.0.0/16')
        """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
