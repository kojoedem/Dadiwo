# Cyber Range Microservices Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)

An open-source, microservice-based personal cyber range and orchestrator designed for virtualized environments (Ubuntu VM inside GNS3, EVE-NG, PNETLab, Proxmox, VMware). Features a **Central Cyber Range Manager Dashboard** for configuring microservices, mapping local domain URLs, setting individual port allocations, and adjusting difficulty profiles for security testing and red/blue team labs.

---

## 🎯 Key Features

- **🎛 Central Manager Control Plane (Port 9000)**: Unified web control interface allowing administrators to manage microservices, change individual service ports, set custom local URLs (`atm.lab`, `bank.lab`), and start/stop containers.
- **🏷 Multi-Level Difficulty Calibration**: Set target profile levels dynamically:
  - 🟢 **Beginner**: Basic access control and IDOR / BOLA flaws.
  - 🟡 **Intermediate**: Business logic anomalies and workflow bypasses.
  - 🟠 **Advanced**: Broken authentication and API authorization bypasses.
  - 🔴 **Expert**: Multi-stage chained CTF exploit paths.
  - 🛡 **Secure**: Production-hardened mode for remediation verification.
- **🌐 Local VM Domain Mapping**: Each microservice supports mapped local URLs on the Ubuntu host via `/etc/hosts` or local DNS (e.g., `http://atm.lab:8080`).
- **⚡ Lightweight Container Footprint**: Resource-optimized (512 MB – 2 GB RAM per lab container) ideal for multi-subnet GNS3/EVE-NG network topologies.

---

## 📐 Platform Architecture

```text
                        Attacker (Kali / Host)
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │   Ubuntu Cyber Range    │
                     │       Host VM           │
                     │                         │
                     │  ┌───────────────────┐  │
                     │  │  Central Manager  │  │
                     │  │   Control Plane   │  │
                     │  │   (Port 9000)     │  │
                     │  └─────────┬─────────┘  │
                     │            │            │
             ┌───────┴────────────┼────────────┴───────┐
             │                    │                    │
             ▼                    ▼                    ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ 🏧 ATM Lab       │  │ 🏦 Bank Lab      │  │ 🌐 ISP Lab       │
   │ (http://atm.lab) │  │ (http://bank.lab)│  │ (http://isp.lab) │
   │ Config Port: 8080│  │ Config Port: 8081│  │ Config Port: 8082│
   └──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 🚀 Quickstart Guide

### 1. Launch Cyber Range Platform
From the repository root:
```bash
docker compose up -d --build
```

### 2. Access the Manager Dashboard
Navigate to `http://<UBUNTU_VM_IP>:9000` in your web browser.

### 3. Local Domain Configuration (`/etc/hosts`)
To enable local domain URLs (`atm.lab`, `bank.lab`, `isp.lab`, `school.lab`) on your local machine or Kali attack container, add the following lines to `/etc/hosts`:

```text
127.0.0.1   atm.lab bank.lab isp.lab school.lab
```
*(Replace `127.0.0.1` with your Ubuntu VM IP address if accessing remotely).*

---

## 🗂 Directory Layout

```text
cyber-range/
├── README.md                 # Root Cyber Range Documentation
├── docker-compose.yml        # Orchestrates Manager & Microservices
├── manager/                  # 🛡 Central Control Plane Dashboard
│   ├── app/                  # FastAPI Application, DB, & Templates
│   ├── Dockerfile
│   └── requirements.txt
└── labs/
    ├── atm/                  # 🏧 ATM Microservice Lab
    │   ├── app/              # FastAPI Application & UI
    │   ├── database/         # SQLite DB & Models
    │   ├── tests/            # Pytest Suite
    │   └── README.md         # Lab Walkthrough & Exploit Guide
    ├── bank/                 # 🏦 Bank Portal (Planned)
    ├── isp/                  # 🌐 ISP Portal (Planned)
    └── school/               # 🎓 University Portal (Planned)
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
