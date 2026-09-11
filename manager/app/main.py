import os
import sys
import logging
import sqlite3
import urllib.request
import urllib.parse
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import database

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dns")))
try:
    import mini_dns
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    mini_dns = None

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger("cyber_range_manager")

app = FastAPI(
    title="Cyber Range Central Manager Dashboard",
    description="Control plane for deploying, configuring, and monitoring cyber range microservices.",
    version="1.2.0"
)

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

dns_server_instance = None

class ServiceConfigUpdate(BaseModel):
    configured_port: int
    local_domain: str
    difficulty: str
    environment_purpose: str = "cybersecurity"

class DNSConfigUpdate(BaseModel):
    dns_enabled: bool
    host_ip: str = "127.0.0.1"
    dns_port: int = 5353

def notify_microservice_config(service_id: str, configured_port: int, difficulty: str, environment_purpose: str):
    target_url = (
        f"http://localhost:{configured_port}/api/v1/configure?"
        f"difficulty={urllib.parse.quote(difficulty)}&"
        f"environment_purpose={urllib.parse.quote(environment_purpose)}"
    )
    try:
        req = urllib.request.Request(target_url, method="POST")
        with urllib.request.urlopen(req, timeout=2) as response:
            logger.info(f"Sync response from {service_id} on port {configured_port}: {response.status}")
    except Exception as e:
        logger.warning(f"Could not sync live config with service {service_id} on port {configured_port}: {e}")

@app.on_event("startup")
async def startup_event():
    global dns_server_instance
    if DNS_AVAILABLE:
        try:
            conn = database.get_db_connection()
            dns_settings = conn.execute("SELECT * FROM dns_settings WHERE id = 1").fetchone()
            conn.close()
            if dns_settings and dns_settings["dns_enabled"]:
                dns_server_instance = mini_dns.MiniDNSServer(
                    host="0.0.0.0",
                    port=dns_settings["dns_port"]
                )
                dns_server_instance.start()
                logger.info(f"Auto-started Mini DNS Server on UDP port {dns_settings['dns_port']}")
        except Exception as e:
            logger.error(f"Failed to auto-start Mini DNS Server: {e}")

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    conn = database.get_db_connection()
    services = [dict(row) for row in conn.execute("SELECT * FROM microservices").fetchall()]
    dns_settings = dict(conn.execute("SELECT * FROM dns_settings WHERE id = 1").fetchone())
    conn.close()

    message = request.query_params.get("message")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "services": services,
            "dns_settings": dns_settings,
            "message": message,
            "error": error
        }
    )

@app.get("/api/v1/services")
async def list_services():
    conn = database.get_db_connection()
    services = [dict(row) for row in conn.execute("SELECT * FROM microservices").fetchall()]
    conn.close()
    return {"status": "success", "count": len(services), "services": services}

@app.get("/api/v1/dns/config")
async def get_dns_config():
    conn = database.get_db_connection()
    dns_settings = dict(conn.execute("SELECT * FROM dns_settings WHERE id = 1").fetchone())
    conn.close()
    return {"status": "success", "dns_settings": dns_settings}

@app.post("/api/v1/dns/configure")
async def configure_dns_api(config: DNSConfigUpdate):
    global dns_server_instance
    conn = database.get_db_connection()
    conn.execute("""
        UPDATE dns_settings
        SET dns_enabled = ?, host_ip = ?, dns_port = ?
        WHERE id = 1
    """, (1 if config.dns_enabled else 0, config.host_ip, config.dns_port))
    conn.commit()
    conn.close()

    if config.dns_enabled and DNS_AVAILABLE:
        if dns_server_instance is None:
            dns_server_instance = mini_dns.MiniDNSServer(host="0.0.0.0", port=config.dns_port)
            dns_server_instance.start()
            logger.info(f"Started Mini DNS Server on UDP port {config.dns_port}")
    elif not config.dns_enabled and dns_server_instance:
        dns_server_instance.stop()
        dns_server_instance = None

    return {"status": "success", "message": "DNS settings updated successfully."}

@app.post("/web/dns/configure")
async def web_configure_dns(
    dns_enabled: Optional[str] = Form(None),
    host_ip: str = Form("127.0.0.1"),
    dns_port: int = Form(5353)
):
    enabled_bool = (dns_enabled is not None and dns_enabled.lower() in ["on", "true", "1", "yes"])
    config = DNSConfigUpdate(dns_enabled=enabled_bool, host_ip=host_ip, dns_port=dns_port)
    await configure_dns_api(config)
    return RedirectResponse(
        url=f"/?message=DNS+Settings+Updated. Enabled={enabled_bool}, Host IP={host_ip}, Port={dns_port}",
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.post("/api/v1/services/{service_id}/configure")
async def configure_service_api(service_id: str, config: ServiceConfigUpdate):
    if config.configured_port < 1024 or config.configured_port > 65535:
        raise HTTPException(status_code=400, detail="Port must be between 1024 and 65535")

    allowed_levels = ["beginner", "intermediate", "advanced", "expert", "secure"]
    if config.difficulty.lower() not in allowed_levels:
        raise HTTPException(status_code=400, detail=f"Invalid difficulty. Allowed: {allowed_levels}")

    allowed_purposes = ["cybersecurity", "networking"]
    if config.environment_purpose.lower() not in allowed_purposes:
        raise HTTPException(status_code=400, detail=f"Invalid environment purpose. Allowed: {allowed_purposes}")

    conn = database.get_db_connection()
    service = conn.execute("SELECT * FROM microservices WHERE id = ?", (service_id,)).fetchone()
    if not service:
        conn.close()
        raise HTTPException(status_code=404, detail="Microservice not found")

    conn.execute("""
        UPDATE microservices
        SET configured_port = ?, local_domain = ?, difficulty = ?, environment_purpose = ?
        WHERE id = ?
    """, (config.configured_port, config.local_domain, config.difficulty.lower(), config.environment_purpose.lower(), service_id))
    conn.commit()
    conn.close()

    notify_microservice_config(service_id, config.configured_port, config.difficulty, config.environment_purpose)

    logger.info(f"Updated microservice {service_id}: port={config.configured_port}, domain={config.local_domain}, difficulty={config.difficulty}, purpose={config.environment_purpose}")
    return {"status": "success", "message": f"Updated settings for {service_id}"}

@app.post("/api/v1/services/{service_id}/status")
async def update_service_status_api(service_id: str, action: str = Query(...)):
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Action must be start, stop, or restart")

    conn = database.get_db_connection()
    service = conn.execute("SELECT * FROM microservices WHERE id = ?", (service_id,)).fetchone()
    if not service:
        conn.close()
        raise HTTPException(status_code=404, detail="Microservice not found")

    new_status = "running" if action in ["start", "restart"] else "stopped"
    conn.execute("UPDATE microservices SET status = ? WHERE id = ?", (new_status, service_id))
    conn.commit()
    conn.close()

    logger.info(f"Microservice {service_id} actionExecuted={action}, new_status={new_status}")
    return {"status": "success", "service_id": service_id, "action": action, "current_status": new_status}

@app.post("/web/configure")
async def web_configure_service(
    service_id: str = Form(...),
    configured_port: int = Form(...),
    local_domain: str = Form(...),
    difficulty: str = Form(...),
    environment_purpose: str = Form(...),
    action: Optional[str] = Form(None)
):
    try:
        config = ServiceConfigUpdate(
            configured_port=configured_port,
            local_domain=local_domain,
            difficulty=difficulty,
            environment_purpose=environment_purpose
        )
        await configure_service_api(service_id, config)

        if action in ["start", "stop", "restart"]:
            await update_service_status_api(service_id, action)

        return RedirectResponse(
            url=f"/?message=Configuration+updated+for+{service_id}.+Mode:+{environment_purpose.upper()}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except HTTPException as e:
        return RedirectResponse(
            url=f"/?error={e.detail}",
            status_code=status.HTTP_303_SEE_OTHER
        )
