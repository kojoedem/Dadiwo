import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import database

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("mobile_service")

ENVIRONMENT_PURPOSE = os.environ.get("ENVIRONMENT_PURPOSE", "cybersecurity").lower()
DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

app = FastAPI(title="Mobile Phone & Bluetooth Simulator Cyber Range", version="1.0.0")

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = database.get_db_connection()
    device = conn.execute("SELECT * FROM device_info WHERE id = 1").fetchone()
    contacts = [dict(r) for r in conn.execute("SELECT * FROM contacts").fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "device": dict(device),
            "contacts": contacts if not SECURE_MODE else [c for c in contacts if "FLAG" not in c.get("secret_note", "")],
            "difficulty": DIFFICULTY_LEVEL,
            "environment_purpose": ENVIRONMENT_PURPOSE,
            "secure_mode": SECURE_MODE,
            "message": request.query_params.get("message")
        }
    )

@app.post("/bluetooth/pair")
async def pair_bluetooth(attacker_mac: str = Form(...), pin: str = Form(...)):
    if ENVIRONMENT_PURPOSE == "networking":
        raise HTTPException(
            status_code=503,
            detail="Service Unavailable: Node configured in General Networking Mode."
        )

    conn = database.get_db_connection()
    device = conn.execute("SELECT * FROM device_info WHERE id = 1").fetchone()

    # Vulnerable mode allows default '0000' PIN or weak bypass
    if SECURE_MODE and pin != device["pairing_code"]:
        conn.close()
        return RedirectResponse(url="/?message=Pairing+failed:+Invalid+PIN", status_code=status.HTTP_303_SEE_OTHER)

    conn.execute(
        "INSERT INTO bluetooth_logs (attacker_mac, action) VALUES (?, ?)",
        (attacker_mac, "PAIR_SUCCESS")
    )
    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/?message=Bluetooth+paired+with+{attacker_mac}.+Flag:+{device['flag']}",
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.get("/api/v1/bluetooth/exfiltrate")
async def bluetooth_exfiltrate(mac: Optional[str] = None):
    """
    Unauthenticated Bluetooth API endpoint simulating BlueBorne/Bluebugging data extraction.
    """
    if ENVIRONMENT_PURPOSE == "networking":
        raise HTTPException(
            status_code=503,
            detail="Service Unavailable: Node configured in General Networking Mode."
        )

    conn = database.get_db_connection()
    device = dict(conn.execute("SELECT * FROM device_info WHERE id = 1").fetchone())
    contacts = [dict(r) for r in conn.execute("SELECT * FROM contacts").fetchall()]
    conn.close()

    if SECURE_MODE:
        return {"status": "error", "detail": "Bluetooth encryption & authentication active."}

    return {
        "status": "vulnerable",
        "device": device,
        "contacts": contacts,
        "exploit": "BlueBorne Unauthenticated Phonebook Access (AT+CPBR)"
    }

@app.get("/api/v1/mode")
async def get_mode():
    return {"environment_purpose": ENVIRONMENT_PURPOSE, "difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE}

@app.post("/api/v1/configure")
async def configure(
    difficulty: Optional[str] = Query(None),
    environment_purpose: Optional[str] = Query(None)
):
    global DIFFICULTY_LEVEL, SECURE_MODE, ENVIRONMENT_PURPOSE
    if difficulty:
        DIFFICULTY_LEVEL = difficulty.lower()
        SECURE_MODE = (DIFFICULTY_LEVEL == "secure")
    if environment_purpose:
        ENVIRONMENT_PURPOSE = environment_purpose.lower()
    return {
        "status": "success",
        "environment_purpose": ENVIRONMENT_PURPOSE,
        "difficulty": DIFFICULTY_LEVEL,
        "secure_mode": SECURE_MODE
    }
