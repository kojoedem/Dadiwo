import os
import subprocess
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("isp_service")

DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "advanced").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

app = FastAPI(title="ISP Customer Portal Microservice Cyber Range", version="1.0.0")

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE, "diag_output": None}
    )

@app.post("/diagnostics", response_class=HTMLResponse)
async def run_diagnostics(request: Request, host: str = Form(...)):
    output = ""
    if SECURE_MODE or DIFFICULTY_LEVEL == "beginner":
        # Secure execution without shell injection
        try:
            res = subprocess.run(["ping", "-c", "2", host], capture_output=True, text=True, timeout=5)
            output = res.stdout or res.stderr
        except Exception as e:
            output = f"Execution error: {e}"
    else:
        # Command injection vulnerability in intermediate/advanced/expert modes
        cmd = f"ping -c 2 {host}"
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            output = res.stdout + "\n" + res.stderr
        except Exception as e:
            output = f"Command error: {e}"

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE, "diag_output": output}
    )

@app.get("/api/v1/radius/subscribers")
async def radius_subscribers():
    conn = database.get_db_connection()
    customers = [dict(row) for row in conn.execute("SELECT account_id, customer_name, package_speed, router_ip, status FROM customers").fetchall()]
    conn.close()
    return {"status": "active", "subscribers": customers}

@app.get("/api/v1/mode")
async def get_mode():
    return {"difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE}

@app.post("/api/v1/configure")
async def configure(difficulty: Optional[str] = Query(None)):
    global DIFFICULTY_LEVEL, SECURE_MODE
    if difficulty:
        DIFFICULTY_LEVEL = difficulty.lower()
        SECURE_MODE = (DIFFICULTY_LEVEL == "secure")
    return {"status": "success", "difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE}
