import os
import sys
import logging
import sqlite3
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import database

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger("ipv6shark")

database.init_db()

app = FastAPI(
    title="Dadiwoo IPv6 Shark / IPv6 Network Lab Microservice",
    description="One-page portfolio, tech blog, and interactive IPv6 security lab covering Red Team attacks (SLAAC, NDP spoofing, extension headers) and Blue Team defenses.",
    version="1.0.0"
)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Global State
DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
ENVIRONMENT_PURPOSE = os.environ.get("ENVIRONMENT_PURPOSE", "cybersecurity").lower()

class ConfigurePayload(BaseModel):
    difficulty: str
    environment_purpose: str = "cybersecurity"

class NDPNeighborPayload(BaseModel):
    ipv6_address: str
    mac_address: str
    interface: str = "eth0"
    state: str = "REACHABLE"

def log_audit(client_ip: str, action: str, details: str):
    try:
        conn = database.get_db_connection()
        conn.execute("""
            INSERT INTO audit_logs (client_ip, action, details)
            VALUES (?, ?, ?)
        """, (client_ip, action, details))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to log audit: {e}")

@app.get("/api/v1/configure")
async def get_config():
    return {
        "status": "success",
        "difficulty_level": DIFFICULTY_LEVEL,
        "environment_purpose": ENVIRONMENT_PURPOSE
    }

@app.post("/api/v1/configure")
async def set_config(payload: Optional[ConfigurePayload] = None, difficulty: Optional[str] = Query(None), environment_purpose: Optional[str] = Query(None)):
    global DIFFICULTY_LEVEL, ENVIRONMENT_PURPOSE
    if payload:
        diff = payload.difficulty
        purp = payload.environment_purpose
    else:
        diff = difficulty or "beginner"
        purp = environment_purpose or "cybersecurity"

    allowed_levels = ["beginner", "intermediate", "advanced", "expert", "secure"]
    if diff.lower() not in allowed_levels:
        raise HTTPException(status_code=400, detail=f"Invalid difficulty level. Allowed: {allowed_levels}")

    DIFFICULTY_LEVEL = diff.lower()
    ENVIRONMENT_PURPOSE = purp.lower()
    logger.info(f"IPv6 Shark configured: level={DIFFICULTY_LEVEL}, purpose={ENVIRONMENT_PURPOSE}")
    return {
        "status": "success",
        "message": f"IPv6 Shark updated to level '{DIFFICULTY_LEVEL}' in purpose '{ENVIRONMENT_PURPOSE}'"
    }

@app.get("/", response_class=HTMLResponse)
async def home_dashboard(request: Request):
    if ENVIRONMENT_PURPOSE == "networking":
        return HTMLResponse(
            content="<h1>IPv6 Shark Node - Networking Mode</h1><p>HTTP 503 Service Unavailable for Cybersecurity Target operations.</p>",
            status_code=503
        )

    conn = database.get_db_connection()
    posts = [dict(p) for p in conn.execute("SELECT * FROM blog_posts ORDER BY id DESC").fetchall()]
    scenarios = [dict(s) for s in conn.execute("SELECT * FROM scenarios ORDER BY id ASC").fetchall()]
    ndp_neighbors = [dict(n) for n in conn.execute("SELECT * FROM ndp_neighbors ORDER BY id ASC").fetchall()]
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(client_ip, "VIEW_HOME", "Accessed IPv6 Shark main portfolio dashboard")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "difficulty": DIFFICULTY_LEVEL,
            "environment_purpose": ENVIRONMENT_PURPOSE,
            "posts": posts,
            "scenarios": scenarios,
            "ndp_neighbors": ndp_neighbors,
            "host": request.headers.get("host", "localhost:8090")
        }
    )

@app.get("/api/v1/scenarios")
async def list_scenarios(type: Optional[str] = Query(None)):
    conn = database.get_db_connection()
    if type in ["red_team", "blue_team"]:
        rows = conn.execute("SELECT * FROM scenarios WHERE scenario_type = ? ORDER BY id ASC", (type,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM scenarios ORDER BY id ASC").fetchall()
    conn.close()
    return {"status": "success", "count": len(rows), "scenarios": [dict(r) for r in rows]}

@app.get("/api/v1/scenarios/{scenario_id}")
async def get_scenario(scenario_id: int):
    conn = database.get_db_connection()
    row = conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"status": "success", "scenario": dict(row)}

@app.get("/api/v1/posts")
async def list_posts():
    conn = database.get_db_connection()
    rows = conn.execute("SELECT * FROM blog_posts ORDER BY id DESC").fetchall()
    conn.close()
    return {"status": "success", "count": len(rows), "posts": [dict(r) for r in rows]}

@app.get("/api/v1/ipv6/ping")
async def ipv6_ping_diagnostic(target: str = Query("fe80::1001"), request: Request = None):
    client_ip = request.client.host if request and request.client else "127.0.0.1"

    clean_target = target.strip()
    simulated_output = (
        f"PING6(56 data bytes) {client_ip} --> {clean_target}\n"
        f"16 bytes from {clean_target}, icmp_seq=1 hlim=64 time=0.421 ms\n"
        f"16 bytes from {clean_target}, icmp_seq=2 hlim=64 time=0.389 ms\n"
        f"16 bytes from {clean_target}, icmp_seq=3 hlim=64 time=0.412 ms\n\n"
        f"--- {clean_target} ping6 statistics ---\n"
        f"3 packets transmitted, 3 received, 0% packet loss, time 2003ms\n"
        f"rtt min/avg/max/mdev = 0.389/0.407/0.421/0.013 ms"
    )

    log_audit(client_ip, "IPV6_PING", f"Pinged IPv6 target {clean_target}")

    return {
        "status": "success",
        "target": clean_target,
        "protocol": "ICMPv6",
        "output": simulated_output
    }

@app.get("/api/v1/ipv6/ndp-table")
async def get_ndp_table():
    conn = database.get_db_connection()
    rows = conn.execute("SELECT * FROM ndp_neighbors ORDER BY id ASC").fetchall()
    conn.close()
    return {"status": "success", "count": len(rows), "neighbors": [dict(r) for r in rows]}

@app.post("/api/v1/ipv6/ndp-table", status_code=status.HTTP_201_CREATED)
async def add_ndp_neighbor(payload: NDPNeighborPayload, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ndp_neighbors (ipv6_address, mac_address, interface, state)
            VALUES (?, ?, ?, ?)
        """, (payload.ipv6_address, payload.mac_address, payload.interface, payload.state))
        neighbor_id = cursor.lastrowid
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="IPv6 neighbor address already exists in NDP table.")

    log_audit(client_ip, "ADD_NDP", f"Added NDP neighbor {payload.ipv6_address} -> {payload.mac_address}")
    return {
        "status": "success",
        "message": "NDP neighbor entry added successfully",
        "neighbor_id": neighbor_id
    }
