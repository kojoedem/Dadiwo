import os
import re
import logging
from typing import Optional
from fastapi import FastAPI, Request, Response, HTTPException, Query, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import database

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("bitroot_service")

DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
ENVIRONMENT_PURPOSE = os.environ.get("ENVIRONMENT_PURPOSE", "cybersecurity").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

app = FastAPI(
    title="Bitroot Subdomain Reconnaissance & Security Lab",
    description="Simulated Bitroot Enterprise Infrastructure for DNS, Subdomain Enumeration, WAF, and HTTP Reconnaissance",
    version="1.0.0"
)

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def log_recon_request(request: Request, status_code: int):
    try:
        conn = database.get_db_connection()
        host = request.headers.get("host", "unknown")
        ua = request.headers.get("user-agent", "unknown")
        client_ip = request.client.host if request.client else "127.0.0.1"
        conn.execute(
            "INSERT INTO recon_logs (client_ip, requested_host, user_agent, status_code) VALUES (?, ?, ?, ?)",
            (client_ip, host, ua, status_code)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log recon request: {e}")

def detect_waf_block(request: Request, waf_type: str) -> Optional[Response]:
    """
    Simulates WAF triggers for tool detection (e.g., wafw00f, sqlmap, nikto, XSS/SQLi payload probing).
    """
    ua = request.headers.get("user-agent", "").lower()
    raw_url = str(request.url).lower()
    query_str = str(request.query_params).lower()

    # Suspicious payload patterns often used by security scanners & wafw00f
    is_attack_or_scanner = any(pattern in raw_url or pattern in query_str for pattern in [
        "<script", "select%20", "union%20", "../", "etc/passwd", "wafw00f", "eval(", "%27", "1=1"
    ]) or "wafw00f" in ua or "nikto" in ua or "sqlmap" in ua

    if is_attack_or_scanner and waf_type == "cloudflare":
        content = """<!DOCTYPE html>
<html>
<head>
    <title>Attention Required! | Cloudflare</title>
    <meta charset="UTF-8" />
</head>
<body>
    <h1>Access denied</h1>
    <p>You are unable to access bitroot.lab. The site owner may have set restrictions that prevent you from accessing the site.</p>
    <p>Cloudflare Ray ID: <strong>88123abcdef4567-LHR</strong></p>
    <p><em>CLOUDFLARE_ERROR_1006_Ray</em></p>
</body>
</html>"""
        headers = {
            "Server": "cloudflare",
            "CF-RAY": "88123abcdef4567-LHR",
            "expect-ct": 'max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"',
            "X-CDN": "Cloudflare",
            "Set-Cookie": "__cfduid=d8a0c2394b219e2f; expires=Sat, 20-Mar-2027 12:00:00 GMT; path=/; domain=.bitroot.lab"
        }
        return HTMLResponse(content=content, status_code=403, headers=headers)

    if is_attack_or_scanner and waf_type == "modsecurity":
        content = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>406 Not Acceptable</title>
</head><body>
<h1>Not Acceptable</h1>
<p>An appropriate representation of the requested resource could not be found on this server.</p>
<p>ModSecurity: Access denied with code 403 (phase 2). Pattern match "([\\s\\S]*)" at REQUEST_URI.</p>
<hr>
<address>Apache/2.4.52 (Ubuntu) Server at staging.bitroot.lab Port 8091</address>
</body></html>"""
        headers = {
            "Server": "Apache/2.4.52 (Ubuntu)",
            "X-Mod-Security": "2.9.3",
            "X-Security-Policy": "ModSecurity-OWASP-CRS"
        }
        return HTMLResponse(content=content, status_code=406, headers=headers)

    return None

@app.get("/api/v1/configure", tags=["Management"])
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
        "difficulty": DIFFICULTY_LEVEL,
        "environment_purpose": ENVIRONMENT_PURPOSE,
        "secure_mode": SECURE_MODE
    }

@app.get("/api/v1/subdomains", tags=["Reconnaissance"])
async def list_subdomains_api():
    """
    REST API endpoint providing inventory of configured subdomains for verification.
    """
    conn = database.get_db_connection()
    subdomains = conn.execute("SELECT * FROM subdomains ORDER BY status ASC, id ASC").fetchall()
    conn.close()
    return {
        "domain": "bitroot.lab",
        "total_subdomains": len(subdomains),
        "active_subdomains": len([s for s in subdomains if s["status"] == "alive"]),
        "dead_subdomains": len([s for s in subdomains if s["status"] == "dead"]),
        "subdomains": [dict(s) for s in subdomains]
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "bitroot",
        "domain": "bitroot.lab",
        "purpose": ENVIRONMENT_PURPOSE,
        "difficulty": DIFFICULTY_LEVEL
    }

@app.get("/{path:path}", response_class=HTMLResponse)
async def route_by_host(request: Request, path: str = ""):
    raw_host = request.headers.get("host", "bitroot.lab").split(":")[0].lower()

    # Extract subdomain prefix if applicable
    subdomain_name = ""
    if raw_host.endswith(".bitroot.lab"):
        subdomain_name = raw_host.replace(".bitroot.lab", "")
    elif raw_host != "bitroot.lab" and raw_host != "localhost" and raw_host != "127.0.0.1":
        # Handle cases where subdomain is requested directly without domain suffix
        subdomain_name = raw_host.split(".")[0]

    conn = database.get_db_connection()
    subdomain_entry = None
    if subdomain_name:
        subdomain_entry = conn.execute(
            "SELECT * FROM subdomains WHERE subdomain = ?", (subdomain_name,)
        ).fetchone()

    conn.close()

    # Check for dead subdomain
    if subdomain_entry and subdomain_entry["status"] == "dead":
        log_recon_request(request, 503 if subdomain_entry["subdomain"] != "test-internal" else 404)
        if subdomain_entry["subdomain"] == "test-internal":
            return templates.TemplateResponse(
                request=request,
                name="dead.html",
                context={
                    "subdomain": dict(subdomain_entry),
                    "error_code": 404,
                    "error_message": "404 Not Found - QA Internal Node Unreachable",
                    "purpose": ENVIRONMENT_PURPOSE,
                    "difficulty": DIFFICULTY_LEVEL
                },
                status_code=404
            )
        return templates.TemplateResponse(
            request=request,
            name="dead.html",
            context={
                "subdomain": dict(subdomain_entry),
                "error_code": 503,
                "error_message": "503 Service Unavailable - System Decommissioned or Offline",
                "purpose": ENVIRONMENT_PURPOSE,
                "difficulty": DIFFICULTY_LEVEL
            },
            status_code=503
        )

    # Check WAF blocks if applicable
    waf_type = subdomain_entry["waf_type"] if subdomain_entry else "none"
    waf_response = detect_waf_block(request, waf_type)
    if waf_response:
        log_recon_request(request, waf_response.status_code)
        return waf_response

    # Prepare response headers based on WAF type / service
    extra_headers = {}
    if waf_type == "cloudflare":
        extra_headers = {
            "Server": "cloudflare",
            "CF-RAY": "88123abcdef4567-LHR",
            "expect-ct": 'max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"',
            "X-CDN": "Cloudflare"
        }
    elif waf_type == "modsecurity":
        extra_headers = {
            "Server": "Apache/2.4.52 (Ubuntu)",
            "X-Mod-Security": "2.9.3",
            "X-Security-Policy": "ModSecurity-OWASP-CRS"
        }
    else:
        extra_headers = {
            "Server": "nginx/1.24.0 (Bitroot Edge)",
            "X-Powered-By": "Bitroot-Framework/2.4"
        }

    log_recon_request(request, 200)

    # Handle Subdomain specific response
    if subdomain_entry and subdomain_entry["status"] == "alive":
        sub_dict = dict(subdomain_entry)
        # Handle API JSON endpoint explicitly for api.bitroot.lab
        if sub_dict["subdomain"] == "api" and (path.startswith("api") or request.headers.get("accept") == "application/json"):
            return JSONResponse(
                content={
                    "service": "Bitroot REST API Gateway v2",
                    "version": "2.4.0",
                    "status": "operational",
                    "endpoints": [
                        "/api/v1/auth",
                        "/api/v1/users",
                        "/api/v1/system/status",
                        "/api/v1/metrics"
                    ],
                    "security": "OAuth2 / Bearer JWT / Cloudflare WAF Protected"
                },
                headers=extra_headers
            )

        return templates.TemplateResponse(
            request=request,
            name="subdomain.html",
            context={
                "subdomain": sub_dict,
                "purpose": ENVIRONMENT_PURPOSE,
                "difficulty": DIFFICULTY_LEVEL,
                "secure_mode": SECURE_MODE,
                "request_host": raw_host
            },
            headers=extra_headers
        )

    # Default root domain (bitroot.lab) page
    conn = database.get_db_connection()
    all_subdomains = conn.execute("SELECT * FROM subdomains ORDER BY id ASC").fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "subdomains": [dict(s) for s in all_subdomains],
            "purpose": ENVIRONMENT_PURPOSE,
            "difficulty": DIFFICULTY_LEVEL,
            "secure_mode": SECURE_MODE,
            "request_host": raw_host
        },
        headers=extra_headers
    )
