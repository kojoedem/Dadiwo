# Cyber Range Microservices Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

An open-source, microservice-based personal cyber range and orchestrator designed for virtualized environments (Ubuntu VM inside GNS3, EVE-NG, PNETLab, Proxmox, VMware). Features a **Central Cyber Range Manager Dashboard** for configuring microservices, mapping local domain URLs, setting individual port allocations, and adjusting difficulty profiles for security testing and red/blue team labs.

---

## 🎯 Available Cyber Range Microservices

| Service | Port | Local URL | Target Vulnerabilities |
| :--- | :--- | :--- | :--- |
| **🛡 Central Manager** | `9000` | `http://localhost:9000` | Control plane, port config, difficulty toggles |
| **🏧 ATM Simulator** | `8080` | `http://atm.lab:8080` | IDOR / BOLA, negative balance withdrawal logic flaw |
| **🏦 Online Banking** | `8081` | `http://bank.lab:8081` | SQL Injection, Reflected XSS, wire transfer logic |
| **🌐 ISP Portal** | `8082` | `http://isp.lab:8082` | Command Injection in ping tool, RADIUS API |
| **🎓 Student Portal** | `8083` | `http://school.lab:8083` | Arbitrary File Upload, record IDOR |
| **🛒 E-Commerce Store** | `8084` | `http://shop.lab:8084` | Client price tampering, coupon reuse logic flaw |

---

## 🚀 Quickstart Guide

### Option 1: Direct Execution on Ubuntu Host (Recommended)
You can run all microservices and the manager directly on your Ubuntu VM host using `start_labs.sh`:

```bash
chmod +x start_labs.sh
./start_labs.sh
```

All 5 labs and the Central Manager will be accessible immediately via your machine's IP address:
- **Manager**: `http://<YOUR_VM_IP>:9000`
- **ATM**: `http://<YOUR_VM_IP>:8080`
- **Bank**: `http://<YOUR_VM_IP>:8081`
- **ISP**: `http://<YOUR_VM_IP>:8082`
- **School**: `http://<YOUR_VM_IP>:8083`
- **Shop**: `http://<YOUR_VM_IP>:8084`

---

### Option 2: Docker Compose Orchestration
If you prefer running via Docker containers:
```bash
docker compose up -d
```

---

## 🌐 Setting Up Local Lab Domain Names (`*.lab`)

If you want to use domain names like `http://atm.lab:8080` or `http://bank.lab:8081` instead of IP addresses:

Add the following line to your local machine or Kali attack machine's `/etc/hosts` file:

```text
<YOUR_UBUNTU_VM_IP>   atm.lab bank.lab isp.lab school.lab shop.lab
```

*(For Windows attack machines, edit `C:\Windows\System32\drivers\etc\hosts`).*

---

## 🏷 Multi-Level Difficulty Calibration

Using the **Manager Dashboard** at `http://<YOUR_VM_IP>:9000`, you can change the difficulty profile of any service dynamically:

- 🟢 **Beginner**: Basic access control and IDOR / BOLA flaws.
- 🟡 **Intermediate**: Business logic anomalies and workflow bypasses.
- 🟠 **Advanced**: Command injection and broken authentication.
- 🔴 **Expert**: Multi-stage chained CTF exploit paths.
- 🛡 **Secure**: Production-hardened mode for remediation verification.

---

## 🗂 Directory Layout

```text
cyber-range/
├── README.md                 # Root Cyber Range Documentation
├── start_labs.sh             # Automatic Host Launch Script
├── docker-compose.yml        # Docker Orchestration Configuration
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
