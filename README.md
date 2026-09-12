# Cyber Range Microservices Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Docs-success.svg)](https://kojoedem.github.io/cyber-range/)

An open-source, microservice-based personal cyber range and orchestrator designed for virtualized environments (Ubuntu VM inside GNS3, EVE-NG, PNETLab, Proxmox, VMware). Features the **🛡 Dadiwoo Central Cyber Range Control Plane** with search filtering (`osint`, `wifi`, `sqli`, `idor`, `bluetooth`), 20-per-page pagination, settings modal popups, Wireshark packet capture guides, and Kali Linux penetration testing walkthroughs.

🌐 **Live Documentation Site**: [**https://kojoedem.github.io/cyber-range/**](https://kojoedem.github.io/cyber-range/)

---

## 📸 Central Manager Control Plane

![Manager Dashboard](docs/images/manager_dashboard.png)

---

## 🎯 Cyber Range Microservices Summary

| Service | Port | Local Domain | Search Tags | Primary Vulnerabilities |
| :--- | :--- | :--- | :--- | :--- |
| **🛡 Dadiwoo Manager** | `9000` | `http://localhost:9000` | `manager`, `control-plane` | Control plane, DNS, Port config, Update checks |
| **🌐 Mini DNS Server** | `5353` (UDP) | `*.lab` / `*.lab.local` | `dns`, `networking` | Custom UDP DNS A-record resolver for GNS3/EVE-NG |
| **🏧 Dadiwoo ATM Simulator** | `8080` | `http://atm.lab:8080` | `web`, `financial`, `idor` | IDOR / BOLA, negative balance withdrawal logic flaw |
| **🏦 Dadiwoo Online Banking** | `8081` | `http://bank.lab:8081` | `web`, `financial`, `sqli` | SQL Injection, Reflected XSS, wire transfer logic |
| **🌐 Dadiwoo ISP Portal** | `8082` | `http://isp.lab:8082` | `wifi`, `network`, `telecom` | Command Injection in ping tool, RADIUS API |
| **🎓 Dadiwoo Student Portal** | `8083` | `http://school.lab:8083` | `web`, `education`, `osint` | Arbitrary File Upload, record IDOR |
| **🛒 Dadiwoo E-Commerce Store** | `8084` | `http://shop.lab:8084` | `web`, `retail`, `logic-flaw` | Client price tampering, coupon reuse logic flaw |
| **📱 Dadiwoo Smartphone Lab** | `8085` | `http://mobile.lab:8085` | `bluetooth`, `mobile`, `phone` | Bluetooth exfiltration (BlueBorne), weak PIN pairing |

---

## 🚀 Quickstart Guide

```bash
chmod +x start_labs.sh
./start_labs.sh
```

All microservices run on distinct individual ports accessible directly via your machine IP:
- **Dadiwoo Manager Dashboard**: `http://<YOUR_VM_IP>:9000`
- **Mini UDP DNS Server**: `<YOUR_VM_IP>:5353`

---

## 📖 Comprehensive User, Wireshark & Kali Guide

For full instructions including:
1. **Wireshark Packet Capture Filters**: Capturing unencrypted HTTP/DNS microservice traffic.
2. **Kali Linux Penetration Testing**: Nmap scanning, sqlmap exploitation, Bluetooth exfiltration, and command injection attacks.
3. **Settings Modal & Dashboard Search**: Navigating settings popups and keyword search.

Consult the [**Complete User & Administration Guide (`USAGE_GUIDE.md`)**](USAGE_GUIDE.md) or visit the live [**GitHub Pages Profile Site**](https://kojoedem.github.io/cyber-range/).

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
