# Cyber Range Microservices Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

An open-source, microservice-based personal cyber range and orchestrator designed for virtualized environments (Ubuntu VM inside GNS3, EVE-NG, PNETLab, Proxmox, VMware). Features a **Central Cyber Range Manager Dashboard** with an embedded **UDP Mini DNS Server**, environment purpose toggles (Cybersecurity Target vs General Networking Test Node), custom port allocations, and multi-level difficulty profiles.

---

## 🎯 Platform Features & Microservices

| Service | Default Port | Local Domain | Environment Modes |
| :--- | :--- | :--- | :--- |
| **🛡 Central Manager** | `9000` | `http://localhost:9000` | Control plane, DNS management, port config, mode toggles |
| **🌐 Mini DNS Server** | `5353` (UDP) | `*.lab` / `*.lab.local` | Custom UDP DNS A-record resolver for GNS3/EVE-NG clients |
| **🏧 ATM Simulator** | `8080` | `http://atm.lab:8080` | IDOR / BOLA, negative balance withdrawal logic flaw |
| **🏦 Online Banking** | `8081` | `http://bank.lab:8081` | SQL Injection, Reflected XSS, wire transfer logic |
| **🌐 ISP Portal** | `8082` | `http://isp.lab:8082` | Command Injection in ping tool, RADIUS API |
| **🎓 Student Portal** | `8083` | `http://school.lab:8083` | Arbitrary File Upload, record IDOR |
| **🛒 E-Commerce Store** | `8084` | `http://shop.lab:8084` | Client price tampering, coupon reuse logic flaw |

---

## 🚀 Quickstart Guide

### Option 1: Direct Execution on Ubuntu Host (Recommended)
Launch all microservices, the Manager Dashboard, and the Mini DNS Server directly on your Ubuntu VM host using `start_labs.sh`:

```bash
chmod +x start_labs.sh
./start_labs.sh
```

All 5 labs and the Central Manager will be accessible immediately via your machine's IP address:
- **Manager Dashboard**: `http://<YOUR_VM_IP>:9000`
- **Mini UDP DNS Server**: `<YOUR_VM_IP>:5353`

---

## 🌐 Embedded Mini DNS Server (`dns/mini_dns.py`)

The platform includes an embedded UDP Mini DNS server (`dnslib`) that automatically resolves `*.lab` domains (e.g. `atm.lab`, `bank.lab`, `isp.lab`, `school.lab`, `shop.lab`) to your configured host IP (default: `127.0.0.1` or your Ubuntu VM IP).

### How to Enable and Configure DNS:
1. Open the Manager Dashboard at `http://<YOUR_VM_IP>:9000`.
2. Locate the **Mini DNS Resolver Server Settings** panel.
3. Toggle DNS **Enabled**, enter your Ubuntu VM Host IP address (or leave `127.0.0.1`), and set the UDP Port (default: `5353`).
4. In GNS3, EVE-NG, or your attack machine, set your DNS resolver IP to your Ubuntu VM IP address on port `5353`.

---

## ⚙️ Dual Environment Modes: Cybersecurity vs General Networking

Using the **Manager Dashboard** at `http://<YOUR_VM_IP>:9000`, administrators can toggle the **Environment Purpose** for any microservice:

1. ⚔️ **Cybersecurity Lab Target Mode**:
   - Authentication endpoints, login forms, and vulnerabilities are fully active for hacking and penetration testing.
2. 🌐 **General Networking Test Node Mode**:
   - Microservices remain 100% reachable via HTTP GET and ping for firewall/routing testing in GNS3/EVE-NG.
   - Login and state-modifying POST requests return `HTTP 503 Service Unavailable (Network Test Node)`.

---

## 🗂 Directory Layout

```text
cyber-range/
├── README.md                 # Root Cyber Range Documentation
├── start_labs.sh             # Automatic Host Launch Script
├── docker-compose.yml        # Docker Orchestration Configuration
├── dns/                      # 🌐 Mini UDP DNS Server Module (mini_dns.py)
├── manager/                  # 🛡 Central Control Plane Dashboard
└── labs/
    ├── atm/                  # 🏧 ATM Microservice Lab
    ├── bank/                 # 🏦 Online Banking Microservice Lab
    ├── isp/                  # 🌐 ISP Customer Portal Lab
    ├── school/               # 🎓 Student University Portal Lab
    └── shop/                 # 🛒 E-Commerce Platform Lab
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
