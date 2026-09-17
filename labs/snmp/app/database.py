import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "snmp.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mib_objects (
            oid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            value TEXT NOT NULL,
            data_type TEXT NOT NULL DEFAULT 'OCTETSTRING',
            access TEXT NOT NULL DEFAULT 'ro',
            description TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_strings (
            community TEXT PRIMARY KEY,
            permission TEXT NOT NULL DEFAULT 'ro',
            description TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usm_users (
            username TEXT PRIMARY KEY,
            sec_level TEXT NOT NULL DEFAULT 'authPriv',
            auth_protocol TEXT DEFAULT 'SHA',
            auth_pass TEXT DEFAULT NULL,
            priv_protocol TEXT DEFAULT 'AES',
            priv_pass TEXT DEFAULT NULL,
            description TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snmp_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            v1_enabled INTEGER NOT NULL DEFAULT 1,
            v2c_enabled INTEGER NOT NULL DEFAULT 1,
            v3_enabled INTEGER NOT NULL DEFAULT 1,
            vacm_enabled INTEGER NOT NULL DEFAULT 0,
            ip_acl_enabled INTEGER NOT NULL DEFAULT 0,
            allowed_ips TEXT NOT NULL DEFAULT '127.0.0.1,10.0.0.0/8,192.168.0.0/16',
            rate_limit_enabled INTEGER NOT NULL DEFAULT 0,
            snmp_port INTEGER NOT NULL DEFAULT 16161
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snmp_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            client_ip TEXT NOT NULL,
            pdu_type TEXT NOT NULL,
            version TEXT NOT NULL,
            community_or_user TEXT NOT NULL,
            oid TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT NOT NULL
        )
    """)

    # Seed MIB Objects
    cursor.execute("SELECT COUNT(*) as count FROM mib_objects")
    if cursor.fetchone()["count"] == 0:
        mib_seed = [
            (".1.3.6.1.2.1.1.1.0", "sysDescr", "Dadiwoo Enterprise Core Gateway Switch v4.1.0", "OCTETSTRING", "ro", "System description"),
            (".1.3.6.1.2.1.1.2.0", "sysObjectID", ".1.3.6.1.4.1.9999.1", "OBJECTID", "ro", "System object identifier"),
            (".1.3.6.1.2.1.1.3.0", "sysUpTime", "1482093", "TIMETICKS", "ro", "System uptime in hundredths of a second"),
            (".1.3.6.1.2.1.1.4.0", "sysContact", "Network Administrator <admin@dadiwoo.lab>", "OCTETSTRING", "rw", "System administrative contact"),
            (".1.3.6.1.2.1.1.5.0", "sysName", "GW-CORE-01", "OCTETSTRING", "rw", "System network hostname"),
            (".1.3.6.1.2.1.1.6.0", "sysLocation", "DataCenter Rack 14A, Building 3", "OCTETSTRING", "rw", "System physical location"),
            (".1.3.6.1.2.1.2.1.0", "ifNumber", "48", "INTEGER", "ro", "Number of network interfaces"),
            (".1.3.6.1.4.1.9999.1.1.0", "secretFlagV1", "FLAG{SNMP_V1_V2C_COMMUNITY_EXPLOIT_2026}", "OCTETSTRING", "ro", "CTF Flag for SNMP v1/v2c Community String Enumeration"),
            (".1.3.6.1.4.1.9999.1.2.0", "routerAdminPass", "SuperSecretRouterPass2026", "OCTETSTRING", "rw", "Stored Router Administrator Password (Vulnerable OID SET)"),
            (".1.3.6.1.4.1.9999.1.3.0", "interfaceStatus", "UP", "OCTETSTRING", "rw", "Core Uplink Interface Status (UP/DOWN)"),
            (".1.3.6.1.4.1.9999.1.4.0", "secretFlagV3", "FLAG{SNMPV3_AUTHPRIV_USM_DECRYPTED_2026}", "OCTETSTRING", "ro", "CTF Flag for SNMPv3 USM Decryption")
        ]
        cursor.executemany("""
            INSERT INTO mib_objects (oid, name, value, data_type, access, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, mib_seed)

    # Seed Community Strings
    cursor.execute("SELECT COUNT(*) as count FROM community_strings")
    if cursor.fetchone()["count"] == 0:
        comm_seed = [
            ("public", "ro", "Public read-only community string"),
            ("private", "rw", "Private read-write community string"),
            ("management123", "rw", "Secret administrative community string")
        ]
        cursor.executemany("""
            INSERT INTO community_strings (community, permission, description)
            VALUES (?, ?, ?)
        """, comm_seed)

    # Seed USM Users (v3)
    cursor.execute("SELECT COUNT(*) as count FROM usm_users")
    if cursor.fetchone()["count"] == 0:
        usm_seed = [
            ("guest_snmpv3", "noAuthNoPriv", "NONE", None, "NONE", None, "SNMPv3 User without auth or encryption"),
            ("operator_snmpv3", "authNoPriv", "MD5", "AuthPassword123", "NONE", None, "SNMPv3 User with MD5 authentication"),
            ("admin_snmpv3", "authPriv", "SHA", "AdminAuthPass123", "AES", "AdminPrivPass123", "SNMPv3 User with SHA auth and AES encryption")
        ]
        cursor.executemany("""
            INSERT INTO usm_users (username, sec_level, auth_protocol, auth_pass, priv_protocol, priv_pass, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, usm_seed)

    # Seed Settings
    cursor.execute("SELECT COUNT(*) as count FROM snmp_settings")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
            INSERT INTO snmp_settings (id, v1_enabled, v2c_enabled, v3_enabled, vacm_enabled, ip_acl_enabled, allowed_ips, rate_limit_enabled, snmp_port)
            VALUES (1, 1, 1, 1, 0, 0, '127.0.0.1,10.0.0.0/8,192.168.0.0/16', 0, 16161)
        """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
