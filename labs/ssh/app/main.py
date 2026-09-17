import os
import logging
from typing import Optional, List
from fastapi import FastAPI, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import database
from ssh_server import ssh_server_instance

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("ssh_service")

DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
ENVIRONMENT_PURPOSE = os.environ.get("ENVIRONMENT_PURPOSE", "cybersecurity").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

app = FastAPI(
    title="🔑 Dadiwoo SSH Hacking & Defense Microservice",
    description="Interactive SSH server lab microservice supporting real SSH client connections, password brute-forcing (Hydra), weak private key exfiltration, fail2ban rate limiting, and sudo privilege escalation.",
    version="1.0.0"
)

database.init_db()

# Auto-start interactive SSH server on TCP port 2222
ssh_server_instance.start_server()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

class SSHSimulateLogin(BaseModel):
    username: str
    password: Optional[str] = None
    use_pubkey: bool = False

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = database.get_db_connection()
    users = [dict(row) for row in conn.execute("SELECT username, role, home_dir, shell, ctf_flag, public_key IS NOT NULL as has_pubkey FROM ssh_users").fetchall()]
    keys = [dict(row) for row in conn.execute("SELECT id, key_name, username, description FROM ssh_keys").fetchall()]
    sessions = [dict(row) for row in conn.execute("SELECT * FROM ssh_sessions ORDER BY login_time DESC LIMIT 20").fetchall()]
    banned_ips = [dict(row) for row in conn.execute("SELECT * FROM ssh_fail2ban ORDER BY last_attempt DESC").fetchall()]
    settings = dict(conn.execute("SELECT * FROM ssh_settings WHERE id = 1").fetchone())
    audit_logs = [dict(row) for row in conn.execute("SELECT * FROM ssh_audit_logs ORDER BY timestamp DESC LIMIT 25").fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "users": users,
            "keys": keys,
            "sessions": sessions,
            "banned_ips": banned_ips,
            "settings": settings,
            "audit_logs": audit_logs,
            "difficulty": DIFFICULTY_LEVEL,
            "purpose": ENVIRONMENT_PURPOSE,
            "secure_mode": SECURE_MODE,
            "message": request.query_params.get("message"),
            "error": request.query_params.get("error")
        }
    )

@app.get("/ssh/keys/download/{key_name}")
async def download_ssh_key(key_name: str):
    conn = database.get_db_connection()
    key_row = conn.execute("SELECT * FROM ssh_keys WHERE key_name = ?", (key_name,)).fetchone()
    conn.close()

    if not key_row:
        raise HTTPException(status_code=404, detail="SSH Key not found")

    if SECURE_MODE and key_name == "id_rsa_user":
        raise HTTPException(status_code=403, detail="Key downloading disabled in Secure Mode.")

    return PlainTextResponse(
        content=key_row["private_key_pem"],
        headers={"Content-Disposition": f"attachment; filename={key_name}.pem"}
    )

@app.get("/api/v1/ssh/sessions")
async def list_active_sessions():
    conn = database.get_db_connection()
    sessions = [dict(row) for row in conn.execute("SELECT * FROM ssh_sessions WHERE status = 'active'").fetchall()]
    conn.close()
    return {"status": "success", "count": len(sessions), "sessions": sessions}

@app.get("/api/v1/ssh/audit")
async def get_audit_logs(limit: int = Query(50, le=200)):
    conn = database.get_db_connection()
    logs = [dict(row) for row in conn.execute("SELECT * FROM ssh_audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()]
    conn.close()
    return {"status": "success", "count": len(logs), "logs": logs}

@app.post("/api/v1/ssh/simulate-login")
async def simulate_login(req: SSHSimulateLogin, request: Request):
    if ENVIRONMENT_PURPOSE == "networking":
        raise HTTPException(status_code=503, detail="Service in Networking Mode. Interactive Auth Suspended.")

    client_ip = request.client.host if request.client else "127.0.0.1"
    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM ssh_users WHERE username = ?", (req.username,)).fetchone()

    if user and (user["password"] == req.password or req.use_pubkey):
        conn.execute("""
            INSERT INTO ssh_audit_logs (client_ip, username, auth_method, status, details)
            VALUES (?, ?, ?, 'SUCCESS', 'Simulated API Authentication Successful')
        """, (client_ip, req.username, "pubkey" if req.use_pubkey else "password"))
        conn.commit()
        conn.close()
        return {
            "status": "success",
            "message": f"Authentication successful for user {req.username}",
            "username": req.username,
            "role": user["role"],
            "ctf_flag": user["ctf_flag"]
        }
    else:
        conn.execute("""
            INSERT INTO ssh_audit_logs (client_ip, username, auth_method, status, details)
            VALUES (?, ?, 'password', 'FAILED', 'Simulated API Authentication Failed')
        """, (client_ip, req.username))
        conn.commit()
        conn.close()
        return {
            "status": "error",
            "message": "Authentication failed: Invalid credentials or username.",
            "code": "AUTH_FAILED"
        }

@app.post("/api/v1/ssh/unban")
async def unban_ip(ip_address: str = Form(...)):
    conn = database.get_db_connection()
    conn.execute("DELETE FROM ssh_fail2ban WHERE ip_address = ?", (ip_address,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/?message=IP+{ip_address}+Unbanned+Successfully", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/api/v1/ssh/settings")
async def update_ssh_settings(
    password_auth_enabled: Optional[bool] = Form(None),
    pubkey_auth_enabled: Optional[bool] = Form(None),
    fail2ban_enabled: Optional[bool] = Form(None),
    max_failed_attempts: Optional[int] = Form(None),
    restricted_shell_enabled: Optional[bool] = Form(None),
    custom_banner: Optional[str] = Form(None)
):
    conn = database.get_db_connection()
    curr = dict(conn.execute("SELECT * FROM ssh_settings WHERE id = 1").fetchone())

    pass_auth_val = (1 if password_auth_enabled else 0) if password_auth_enabled is not None else curr["password_auth_enabled"]
    pub_auth_val = (1 if pubkey_auth_enabled else 0) if pubkey_auth_enabled is not None else curr["pubkey_auth_enabled"]
    f2b_val = (1 if fail2ban_enabled else 0) if fail2ban_enabled is not None else curr["fail2ban_enabled"]
    max_att_val = max_failed_attempts if max_failed_attempts is not None else curr["max_failed_attempts"]
    r_shell_val = (1 if restricted_shell_enabled else 0) if restricted_shell_enabled is not None else curr["restricted_shell_enabled"]
    banner_val = custom_banner if custom_banner is not None else curr["custom_banner"]

    conn.execute("""
        UPDATE ssh_settings
        SET password_auth_enabled = ?, pubkey_auth_enabled = ?, fail2ban_enabled = ?, max_failed_attempts = ?, restricted_shell_enabled = ?, custom_banner = ?
        WHERE id = 1
    """, (pass_auth_val, pub_auth_val, f2b_val, max_att_val, r_shell_val, banner_val))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/?message=SSH+Security+Settings+Updated+Successfully", status_code=status.HTTP_303_SEE_OTHER)

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
            conn.execute("UPDATE ssh_settings SET password_auth_enabled = 0, pubkey_auth_enabled = 1, fail2ban_enabled = 1, max_failed_attempts = 2 WHERE id = 1")
        else:
            conn.execute("UPDATE ssh_settings SET password_auth_enabled = 1, pubkey_auth_enabled = 1, fail2ban_enabled = 1, max_failed_attempts = 3 WHERE id = 1")
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
