# 📡 SNMP Microservice (Simple Network Management Protocol v1 - v3)

The **Dadiwoo SNMP Microservice** is a lightweight network management server designed for testing SNMP security, community string brute-forcing, OID walking, unauthorized SET exploits, SNMPv3 USM decryption, and VACM / IP ACL hardening.

---

## 🎯 Key Capabilities & Cyber Range Scenarios

1. **SNMP v1 / v2c Community String Enumeration**:
   - Attackers use tools like `onesixtyone`, `snmpcheck`, or `hydra` to discover community strings (`public`, `private`, `management123`).
2. **MIB OID Tree Walking & Flag Exfiltration**:
   - Walk OID trees (`.1.3.6.1.2.1.1` and `.1.3.6.1.4.1.9999`) to discover system details and CTF flags (`secretFlagV1`, `secretFlagV3`).
3. **Unauthorized Configuration SET Exploits**:
   - Use `snmpset` with write community strings (`private`) to alter system hostnames (`sysName`), interface states (`interfaceStatus`), or administrative credentials (`routerAdminPass`).
4. **SNMPv3 USM Authentication & Encryption**:
   - Tests `noAuthNoPriv`, `authNoPriv` (MD5/SHA), and `authPriv` (SHA/AES) user security models.
5. **Defensive Hardening Controls**:
   - View-based Access Control Model (VACM) filtering.
   - Disabling unencrypted legacy SNMP versions (v1/v2c).
   - Enforcing IP Access Control Lists (ACLs) and rate-limiting.

---

## 🚀 Port & Access Allocations

- **Web UI & Management Dashboard**: `http://snmp.lab:8087` (or `http://<IP>:8087`)
- **SNMP UDP Service Engine**: UDP Port `16161` (and UDP `161`)

---

## 🧪 Testing

Run unit tests:
```bash
PYTHONPATH=labs/snmp/app pytest labs/snmp/tests/
```
