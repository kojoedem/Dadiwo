# 🛠 Developer & Administrator Guide: Building, Hosting, and Testing a New Microservice

This guide walks administrators and developers step-by-step through creating, testing, containerizing, and registering a new microservice lab on the **Dadiwoo Cyber Range Microservices Platform**.

---

## 📋 Overview of Microservice Requirements

Every microservice in the Dadiwoo Cyber Range must follow standard architecture conventions:
1. **Directory Structure**: Reside under `labs/<service_id>/` with an `app/` subfolder containing `main.py`, `database.py`, and `templates/`.
2. **Dual-Mode Support (`cybersecurity` vs `networking`)**: Read the `ENVIRONMENT_PURPOSE` environment variable to toggle between active attack scenarios and passive networking node reachability.
3. **Live Sync Endpoint (`/api/v1/configure`)**: Support live parameter updates (`difficulty`, `environment_purpose`) sent from the central Manager Control Plane (Port `9000`).
4. **Isolated Ports**: Bind to a unique port (e.g., `8086`) and support `.lab` domain resolutions (e.g., `hr.lab`).
5. **Automated Unit Testing**: Include unit tests under `tests/test_<service_id>.py` using `pytest` and FastAPI `TestClient`.

---

## 📂 Step 1: Create the Directory Structure

For a new microservice called **HR Portal (`hr`)**:

```bash
mkdir -p labs/hr/app/templates labs/hr/tests
```

---

## 🗄️ Step 2: Create the SQLite Database Schema (`labs/hr/app/database.py`)

Create `labs/hr/app/database.py`:

```python
import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "hr.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL DEFAULT '1234',
            full_name TEXT NOT NULL,
            salary REAL NOT NULL,
            flag TEXT DEFAULT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM employees")
    if cursor.fetchone()["count"] == 0:
        sample_data = [
            ("EMP-1001", "1234", "Kwame Addo", 4500.00, None),
            ("EMP-1002", "1234", "Ama Serwaa", 5200.00, None),
            ("EMP-9000", "9999", "HR Director", 12000.00, "FLAG{HR_SALARY_IDOR_COMPROMISE_2026}")
        ]
        cursor.executemany("""
            INSERT INTO employees (emp_id, pin, full_name, salary, flag)
            VALUES (?, ?, ?, ?, ?)
        """, sample_data)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
```

---

## ⚡ Step 3: Implement the FastAPI Application (`labs/hr/app/main.py`)

Create `labs/hr/app/main.py`:

```python
import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("hr_service")

DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
ENVIRONMENT_PURPOSE = os.environ.get("ENVIRONMENT_PURPOSE", "cybersecurity").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

app = FastAPI(title="HR Portal Cyber Range Microservice", version="1.0.0")

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def get_current_employee(request: Request) -> Optional[dict]:
    session_emp = request.cookies.get("session_emp")
    if not session_emp:
        return None
    conn = database.get_db_connection()
    emp = conn.execute("SELECT * FROM employees WHERE emp_id = ?", (session_emp,)).fetchone()
    conn.close()
    return dict(emp) if emp else None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, emp_id: Optional[str] = None):
    current = get_current_employee(request)
    target = emp_id or (current["emp_id"] if current else "EMP-1001")

    if SECURE_MODE and current:
        target = current["emp_id"]

    conn = database.get_db_connection()
    employee = conn.execute("SELECT * FROM employees WHERE emp_id = ?", (target,)).fetchone()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_emp": current,
            "employee": dict(employee) if employee else None,
            "difficulty": DIFFICULTY_LEVEL,
            "purpose": ENVIRONMENT_PURPOSE,
            "secure_mode": SECURE_MODE,
            "error": request.query_params.get("error"),
            "message": request.query_params.get("message")
        }
    )

@app.post("/login")
async def login(emp_id: str = Form(...), pin: str = Form(...)):
    if ENVIRONMENT_PURPOSE == "networking":
        raise HTTPException(status_code=503, detail="Service in Networking Node Mode. Interactive Auth Suspended.")

    conn = database.get_db_connection()
    emp = conn.execute("SELECT * FROM employees WHERE emp_id = ? AND pin = ?", (emp_id, pin)).fetchone()
    conn.close()

    if not emp:
        return RedirectResponse(url="/?error=Invalid+Employee+ID+or+PIN", status_code=status.HTTP_303_SEE_OTHER)

    response = RedirectResponse(url=f"/?emp_id={emp['emp_id']}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="session_emp", value=emp["emp_id"])
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_emp")
    return response

@app.post("/api/v1/configure")
async def configure(difficulty: Optional[str] = Query(None), environment_purpose: Optional[str] = Query(None)):
    global DIFFICULTY_LEVEL, SECURE_MODE, ENVIRONMENT_PURPOSE
    if difficulty:
        DIFFICULTY_LEVEL = difficulty.lower()
        SECURE_MODE = (DIFFICULTY_LEVEL == "secure")
    if environment_purpose:
        ENVIRONMENT_PURPOSE = environment_purpose.lower()
    return {"status": "success", "difficulty": DIFFICULTY_LEVEL, "environment_purpose": ENVIRONMENT_PURPOSE}
```

---

## 🎨 Step 4: Add the User Interface Template (`labs/hr/app/templates/index.html`)

Create `labs/hr/app/templates/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>💼 HR Portal Microservice</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; }
        .card { background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; max-width: 600px; margin: 0 auto; }
        input { width: 100%; padding: 10px; margin: 6px 0 16px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 6px; box-sizing: border-box; }
        .btn { background: #3b82f6; color: white; border: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%; }
    </style>
</head>
<body>
    <div class="card">
        <h1>💼 HR Portal</h1>
        {% if not current_emp %}
            <form action="/login" method="POST">
                <label>Employee ID</label>
                <input type="text" name="emp_id" placeholder="EMP-1001" required>
                <label>PIN</label>
                <input type="password" name="pin" placeholder="1234" required>
                <button type="submit" class="btn">Login</button>
            </form>
        {% else %}
            <h2>Welcome, {{ current_emp.full_name }}</h2>
            <p>ID: <strong>{{ current_emp.emp_id }}</strong></p>
            <p>Salary: <strong>${{ "%.2f"|format(employee.salary if employee else current_emp.salary) }}</strong></p>
            <a href="/logout" style="color: #ef4444;">Logout</a>
        {% endif %}
    </div>
</body>
</html>
```

---

## 🧪 Step 5: Write Automated Tests (`labs/hr/tests/test_hr.py`)

Create `labs/hr/tests/test_hr.py`:

```python
import pytest
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "HR Portal" in response.text

def test_login_success():
    response = client.post("/login", data={"emp_id": "EMP-1001", "pin": "1234"}, follow_redirects=False)
    assert response.status_code == 303
```

Execute your test suite:
```bash
PYTHONPATH=labs/hr/app python3 -m pytest labs/hr/tests/
```

---

## ⚙️ Step 6: Register Microservice in the Central Control Plane

Register the new microservice in `manager/app/database.py` or execute an HTTP POST request to the Manager API:

```python
# Add entry to manager/app/database.py initial_labs list:
("hr", "💼 Dadiwoo HR Employee Portal", "Enterprise", "Corporate HR portal with salary lookup IDOR and staff directory access.", 8086, 8086, "hr.lab", "beginner", "cybersecurity", "web, hr, idor, enterprise", "stopped", "hr-lab-container")
```

---

## 🚀 Step 7: Update Direct Execution Script (`start_labs.sh`)

Add the service port and uvicorn process execution line to `start_labs.sh`:

```bash
# In start_labs.sh:
HR_PORT=8086
echo "Starting 💼 HR Lab (Port ${HR_PORT})..."
PYTHONPATH=labs/hr/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${HR_PORT} --app-dir labs/hr/app > /tmp/hr.log 2>&1 &
```

---

## 🐳 Step 8: Containerize via Docker Compose (`docker-compose.yml`)

Append the service block to `docker-compose.yml`:

```yaml
  hr-lab:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hr-lab-container
    environment:
      - DIFFICULTY_LEVEL=beginner
      - ENVIRONMENT_PURPOSE=cybersecurity
    ports:
      - "8086:8086"
    command: python3 -m uvicorn main:app --host 0.0.0.0 --port 8086 --app-dir labs/hr/app
```

Rebuild and start containers:
```bash
docker compose up -d --build hr-lab
```

---

## ✅ Verification & Summary

1. Access the Manager Dashboard at `http://localhost:9000`.
2. Confirm the new **💼 Dadiwoo HR Employee Portal** card appears.
3. Test starting, stopping, search filtering (`#hr`, `#idor`), and navigating to `http://hr.lab:8086`.
