import os
import time
import socket
import threading
import logging
from typing import Dict, Any, List, Optional, Tuple

import database

logger = logging.getLogger("snmp_engine")

class SNMPEngine:
    def __init__(self, host: str = "0.0.0.0", port: int = 16161):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None

    def log_audit(self, client_ip: str, pdu_type: str, version: str, community_or_user: str, oid: str, status: str, details: str):
        conn = database.get_db_connection()
        conn.execute("""
            INSERT INTO snmp_audit_logs (client_ip, pdu_type, version, community_or_user, oid, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (client_ip, pdu_type, version, community_or_user, oid, status, details))
        conn.commit()
        conn.close()

    def process_snmp_request(self, version: str, community_or_user: str, pdu_type: str, oid: str, set_value: Optional[str] = None, client_ip: str = "127.0.0.1", auth_pass: Optional[str] = None, priv_pass: Optional[str] = None) -> Dict[str, Any]:
        """
        Core SNMP processor logic handling v1, v2c, v3 requests.
        """
        conn = database.get_db_connection()
        settings = dict(conn.execute("SELECT * FROM snmp_settings WHERE id = 1").fetchone())

        # Check Version Allowed
        if version in ["v1", "1"] and not settings["v1_enabled"]:
            conn.close()
            self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "REJECTED", "SNMPv1 is disabled in security settings")
            return {"status": "error", "message": "SNMPv1 is disabled on server.", "code": "VERSION_DISABLED"}

        if version in ["v2c", "2c", "2"] and not settings["v2c_enabled"]:
            conn.close()
            self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "REJECTED", "SNMPv2c is disabled in security settings")
            return {"status": "error", "message": "SNMPv2c is disabled on server.", "code": "VERSION_DISABLED"}

        if version in ["v3", "3"] and not settings["v3_enabled"]:
            conn.close()
            self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "REJECTED", "SNMPv3 is disabled in security settings")
            return {"status": "error", "message": "SNMPv3 is disabled on server.", "code": "VERSION_DISABLED"}

        # Check IP ACL
        if settings["ip_acl_enabled"]:
            allowed = [ip.strip() for ip in settings["allowed_ips"].split(",") if ip.strip()]
            ip_allowed = False
            for rule in allowed:
                if rule == client_ip or rule == "127.0.0.1" or client_ip.startswith(rule.split("/")[0].rsplit(".", 1)[0]):
                    ip_allowed = True
                    break
            if not ip_allowed:
                conn.close()
                self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "REJECTED", f"IP {client_ip} blocked by ACL rules")
                return {"status": "error", "message": f"Client IP {client_ip} blocked by IP ACL.", "code": "ACL_BLOCKED"}

        # Authenticate Version 1 / 2c
        comm_perm = None
        usm_user = None

        if version in ["v1", "1", "v2c", "2c", "2"]:
            comm_row = conn.execute("SELECT * FROM community_strings WHERE community = ?", (community_or_user,)).fetchone()
            if not comm_row:
                conn.close()
                self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "AUTH_FAILED", f"Invalid community string '{community_or_user}'")
                return {"status": "error", "message": f"Authentication failed: Unknown community string '{community_or_user}'", "code": "BAD_COMMUNITY"}
            comm_perm = comm_row["permission"]

        # Authenticate Version 3
        elif version in ["v3", "3"]:
            usm_user = conn.execute("SELECT * FROM usm_users WHERE username = ?", (community_or_user,)).fetchone()
            if not usm_user:
                conn.close()
                self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "AUTH_FAILED", f"Unknown SNMPv3 USM user '{community_or_user}'")
                return {"status": "error", "message": f"SNMPv3 USM Authentication failed: Unknown user '{community_or_user}'", "code": "BAD_USER"}

            # Validate Auth Pass if authNoPriv or authPriv
            sec_level = usm_user["sec_level"]
            if sec_level in ["authNoPriv", "authPriv"]:
                if usm_user["auth_pass"] and auth_pass != usm_user["auth_pass"]:
                    conn.close()
                    self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "AUTH_FAILED", "SNMPv3 Auth Password mismatch")
                    return {"status": "error", "message": "SNMPv3 Authentication failed: Incorrect authentication password.", "code": "BAD_AUTH_PASS"}

            if sec_level == "authPriv":
                if usm_user["priv_pass"] and priv_pass != usm_user["priv_pass"]:
                    conn.close()
                    self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "AUTH_FAILED", "SNMPv3 Privacy Password mismatch")
                    return {"status": "error", "message": "SNMPv3 Privacy failed: Incorrect privacy/encryption key.", "code": "BAD_PRIV_PASS"}

            comm_perm = "rw" if community_or_user == "admin_snmpv3" else "ro"

        # Check VACM (View-based Access Control Model)
        if settings["vacm_enabled"]:
            if oid.startswith(".1.3.6.1.4.1.9999.1.1") or oid.startswith(".1.3.6.1.4.1.9999.1.4"):
                if community_or_user not in ["management123", "admin_snmpv3"]:
                    conn.close()
                    self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "VACM_BLOCKED", "OID restricted by View-based Access Control Model")
                    return {"status": "error", "message": f"VACM Restriction: OID {oid} is excluded from current view context for {community_or_user}.", "code": "VACM_RESTRICTED"}

        pdu_upper = pdu_type.upper()

        # Handle GET Request
        if pdu_upper in ["GET", "GETREQUEST"]:
            obj = conn.execute("SELECT * FROM mib_objects WHERE oid = ? OR name = ?", (oid, oid)).fetchone()
            conn.close()
            if not obj:
                self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "NOT_FOUND", "OID or Object name not found")
                return {"status": "error", "message": f"NoSuchName: OID {oid} does not exist in MIB.", "code": "NO_SUCH_NAME"}

            self.log_audit(client_ip, pdu_type, version, community_or_user, obj["oid"], "SUCCESS", f"GET -> {obj['value']}")
            return {
                "status": "success",
                "oid": obj["oid"],
                "name": obj["name"],
                "value": obj["value"],
                "data_type": obj["data_type"],
                "access": obj["access"],
                "version": version
            }

        # Handle WALK or GETNEXT Request
        elif pdu_upper in ["WALK", "GETNEXT", "GETBULK"]:
            objs = conn.execute("SELECT * FROM mib_objects ORDER BY oid ASC").fetchall()
            conn.close()

            result_list = []
            matching = False
            for o in objs:
                if not oid or oid == "." or oid == ".1" or o["oid"].startswith(oid) or o["name"].lower() == oid.lower():
                    # VACM filter if enabled
                    if settings["vacm_enabled"] and (o["oid"].startswith(".1.3.6.1.4.1.9999.1.1") or o["oid"].startswith(".1.3.6.1.4.1.9999.1.4")):
                        if community_or_user not in ["management123", "admin_snmpv3"]:
                            continue
                    result_list.append({
                        "oid": o["oid"],
                        "name": o["name"],
                        "value": o["value"],
                        "data_type": o["data_type"],
                        "access": o["access"]
                    })

            self.log_audit(client_ip, pdu_type, version, community_or_user, oid or ".1.3.6.1", "SUCCESS", f"WALK returned {len(result_list)} OIDs")
            return {
                "status": "success",
                "count": len(result_list),
                "results": result_list,
                "version": version
            }

        # Handle SET Request
        elif pdu_upper in ["SET", "SETREQUEST"]:
            if comm_perm != "rw":
                conn.close()
                self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "READONLY", f"Permission denied for SET on community/user '{community_or_user}'")
                return {"status": "error", "message": f"ReadOnly: Community string or user '{community_or_user}' has Read-Only permissions.", "code": "READ_ONLY"}

            obj = conn.execute("SELECT * FROM mib_objects WHERE oid = ? OR name = ?", (oid, oid)).fetchone()
            if not obj:
                conn.close()
                self.log_audit(client_ip, pdu_type, version, community_or_user, oid, "NOT_FOUND", "OID not found for SET")
                return {"status": "error", "message": f"NoSuchName: OID {oid} does not exist.", "code": "NO_SUCH_NAME"}

            if obj["access"] != "rw":
                conn.close()
                self.log_audit(client_ip, pdu_type, version, community_or_user, obj["oid"], "NOT_WRITABLE", f"OID {obj['oid']} is read-only")
                return {"status": "error", "message": f"NotWritable: Object {obj['name']} ({obj['oid']}) is configured as Read-Only.", "code": "NOT_WRITABLE"}

            new_val = set_value if set_value is not None else ""
            conn.execute("UPDATE mib_objects SET value = ? WHERE oid = ?", (new_val, obj["oid"]))
            conn.commit()
            conn.close()

            self.log_audit(client_ip, pdu_type, version, community_or_user, obj["oid"], "SUCCESS", f"SET {obj['name']} = '{new_val}'")
            return {
                "status": "success",
                "message": f"Successfully updated {obj['name']} ({obj['oid']}) = '{new_val}'",
                "oid": obj["oid"],
                "name": obj["name"],
                "new_value": new_val
            }

        else:
            conn.close()
            return {"status": "error", "message": f"Unsupported PDU type: {pdu_type}"}

    def start_udp_listener(self):
        """Simple background UDP listener for real network packets on port 16161/161."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.is_running = True
            logger.info(f"SNMP UDP Engine listening on {self.host}:{self.port}")

            def listen_loop():
                while self.is_running:
                    try:
                        data, addr = self.socket.recvfrom(2048)
                        # Process raw datagram if needed or log packet ping
                        self.log_audit(addr[0], "UDP_RAW", "v1/v2c/v3", "public", ".1.3.6.1.2.1.1.1.0", "SUCCESS", f"Received {len(data)} bytes raw UDP SNMP packet")
                    except Exception:
                        if not self.is_running:
                            break

            self.thread = threading.Thread(target=listen_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            logger.warning(f"Could not bind SNMP UDP socket on port {self.port}: {e}")

    def stop_udp_listener(self):
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass

snmp_engine_instance = SNMPEngine()
