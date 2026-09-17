import os
import logging
from typing import Optional, List
from fastapi import FastAPI, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import database
from snmp_engine import snmp_engine_instance

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("snmp_service")

DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
ENVIRONMENT_PURPOSE = os.environ.get("ENVIRONMENT_PURPOSE", "cybersecurity").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

app = FastAPI(
    title="📡 Dadiwoo SNMP Network Management & Security Microservice",
    description="SNMP v1, v2c, and v3 network management lab microservice for hacking, MIB walking, community string brute-forcing, OID SET exploits, and VACM defense.",
    version="1.0.0"
)

database.init_db()

# Auto-start SNMP UDP engine in background
snmp_engine_instance.start_udp_listener()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

class SNMPQueryRequest(BaseModel):
    version: str = "v2c"
    community_or_user: str = "public"
    pdu_type: str = "GET"
    oid: str = ".1.3.6.1.2.1.1.1.0"
    set_value: Optional[str] = None
    auth_pass: Optional[str] = None
    priv_pass: Optional[str] = None

class CommunityStringCreate(BaseModel):
    community: str
    permission: str = "ro"
    description: str = "Custom community string"

class USMUserCreate(BaseModel):
    username: str
    sec_level: str = "authPriv"
    auth_protocol: Optional[str] = "SHA"
    auth_pass: Optional[str] = None
    priv_protocol: Optional[str] = "AES"
    priv_pass: Optional[str] = None
    description: str = "Custom USM user"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = database.get_db_connection()
    mib_objects = [dict(row) for row in conn.execute("SELECT * FROM mib_objects ORDER BY oid ASC").fetchall()]
    community_strings = [dict(row) for row in conn.execute("SELECT * FROM community_strings ORDER BY community ASC").fetchall()]
    usm_users = [dict(row) for row in conn.execute("SELECT * FROM usm_users ORDER BY username ASC").fetchall()]
    settings = dict(conn.execute("SELECT * FROM snmp_settings WHERE id = 1").fetchone())
    audit_logs = [dict(row) for row in conn.execute("SELECT * FROM snmp_audit_logs ORDER BY timestamp DESC LIMIT 25").fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "mib_objects": mib_objects,
            "community_strings": community_strings,
            "usm_users": usm_users,
            "settings": settings,
            "audit_logs": audit_logs,
            "difficulty": DIFFICULTY_LEVEL,
            "purpose": ENVIRONMENT_PURPOSE,
            "secure_mode": SECURE_MODE,
            "message": request.query_params.get("message"),
            "error": request.query_params.get("error")
        }
    )

@app.post("/api/v1/snmp/execute")
async def execute_snmp_request(req: SNMPQueryRequest, request: Request):
    if ENVIRONMENT_PURPOSE == "networking" and req.pdu_type.upper() == "SET":
        raise HTTPException(status_code=533, detail="Service in Networking Mode. Interactive SET operations suspended.")

    client_ip = request.client.host if request.client else "127.0.0.1"
    res = snmp_engine_instance.process_snmp_request(
        version=req.version,
        community_or_user=req.community_or_user,
        pdu_type=req.pdu_type,
        oid=req.oid,
        set_value=req.set_value,
        client_ip=client_ip,
        auth_pass=req.auth_pass,
        priv_pass=req.priv_pass
    )
    return res

@app.get("/api/v1/snmp/mib")
async def list_mib_objects(oid: Optional[str] = None):
    conn = database.get_db_connection()
    if oid:
        objs = [dict(row) for row in conn.execute("SELECT * FROM mib_objects WHERE oid LIKE ? OR name LIKE ? ORDER BY oid ASC", (f"%{oid}%", f"%{oid}%")).fetchall()]
    else:
        objs = [dict(row) for row in conn.execute("SELECT * FROM mib_objects ORDER BY oid ASC").fetchall()]
    conn.close()
    return {"status": "success", "count": len(objs), "mib_objects": objs}

@app.get("/api/v1/snmp/audit")
async def get_audit_logs(limit: int = Query(50, le=200)):
    conn = database.get_db_connection()
    logs = [dict(row) for row in conn.execute("SELECT * FROM snmp_audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()]
    conn.close()
    return {"status": "success", "count": len(logs), "logs": logs}

@app.post("/api/v1/snmp/settings")
async def update_snmp_settings(
    v1_enabled: Optional[bool] = Form(None),
    v2c_enabled: Optional[bool] = Form(None),
    v3_enabled: Optional[bool] = Form(None),
    vacm_enabled: Optional[bool] = Form(None),
    ip_acl_enabled: Optional[bool] = Form(None),
    allowed_ips: Optional[str] = Form(None),
    rate_limit_enabled: Optional[bool] = Form(None)
):
    conn = database.get_db_connection()
    curr = dict(conn.execute("SELECT * FROM snmp_settings WHERE id = 1").fetchone())

    v1_val = (1 if v1_enabled else 0) if v1_enabled is not None else curr["v1_enabled"]
    v2c_val = (1 if v2c_enabled else 0) if v2c_enabled is not None else curr["v2c_enabled"]
    v3_val = (1 if v3_enabled else 0) if v3_enabled is not None else curr["v3_enabled"]
    vacm_val = (1 if vacm_enabled else 0) if vacm_enabled is not None else curr["vacm_enabled"]
    ip_acl_val = (1 if ip_acl_enabled else 0) if ip_acl_enabled is not None else curr["ip_acl_enabled"]
    allowed_ips_val = allowed_ips if allowed_ips is not None else curr["allowed_ips"]
    rate_limit_val = (1 if rate_limit_enabled else 0) if rate_limit_enabled is not None else curr["rate_limit_enabled"]

    conn.execute("""
        UPDATE snmp_settings
        SET v1_enabled = ?, v2c_enabled = ?, v3_enabled = ?, vacm_enabled = ?, ip_acl_enabled = ?, allowed_ips = ?, rate_limit_enabled = ?
        WHERE id = 1
    """, (v1_val, v2c_val, v3_val, vacm_val, ip_acl_val, allowed_ips_val, rate_limit_val))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/?message=SNMP+Security+Settings+Updated+Successfully", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/web/snmp/set")
async def web_snmp_set(
    version: str = Form("v2c"),
    community_or_user: str = Form("private"),
    oid: str = Form(...),
    set_value: str = Form(...)
):
    res = snmp_engine_instance.process_snmp_request(
        version=version,
        community_or_user=community_or_user,
        pdu_type="SET",
        oid=oid,
        set_value=set_value,
        client_ip="127.0.0.1"
    )

    if res.get("status") == "success":
        return RedirectResponse(url=f"/?message={res['message']}", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url=f"/?error={res['message']}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/api/v1/configure")
async def configure(
    difficulty: Optional[str] = Query(None),
    environment_purpose: Optional[str] = Query(None)
):
    global DIFFICULTY_LEVEL, SECURE_MODE, ENVIRONMENT_PURPOSE
    if difficulty:
        DIFFICULTY_LEVEL = difficulty.lower()
        SECURE_MODE = (DIFFICULTY_LEVEL == "secure")
        conn = database.get_db_connection()
        if SECURE_MODE:
            conn.execute("UPDATE snmp_settings SET v1_enabled = 0, v2c_enabled = 0, v3_enabled = 1, vacm_enabled = 1, ip_acl_enabled = 1 WHERE id = 1")
        else:
            conn.execute("UPDATE snmp_settings SET v1_enabled = 1, v2c_enabled = 1, v3_enabled = 1, vacm_enabled = 0, ip_acl_enabled = 0 WHERE id = 1")
        conn.commit()
        conn.close()

    if environment_purpose:
        ENVIRONMENT_PURPOSE = environment_purpose.lower()

    return {
        "status": "success",
        "difficulty": DIFFICULTY_LEVEL,
        "environment_purpose": ENVIRONMENT_PURPOSE,
        "secure_mode": SECURE_MODE
    }
