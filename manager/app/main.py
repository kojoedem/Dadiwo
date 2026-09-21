import os
import sys
import logging
import sqlite3
import subprocess
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

CURRENT_VERSION = "1.0.0"

app = FastAPI(
    title="Cyber Range Central Manager Dashboard",
    description="Control plane for deploying, configuring, and monitoring cyber range microservices.",
    version=CURRENT_VERSION
)

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

dns_server_instance = None

class ServiceConfigUpdate(BaseModel):
    configured_port: int
    local_domain: str
    difficulty: str
    environment_purpose: str = "cybersecurity"
    tags: Optional[str] = "web, security"

class DNSConfigUpdate(BaseModel):
    dns_enabled: bool
    host_ip: str = "127.0.0.1"
    dns_port: Optional[int] = 5353

def stop_service_process_or_container(service_id: str, port: int, container_name: str):
    """Terminates any process bound to port or stops Docker container if running."""
    try:
        subprocess.run(["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", f"labs/{service_id}/app"], capture_output=True)
        logger.info(f"Stopped process listening on TCP port {port} for service {service_id}")
    except Exception as e:
        logger.warning(f"Failed to kill process on port {port}: {e}")

    if container_name:
        try:
            subprocess.run(["docker", "stop", container_name], capture_output=True, timeout=3)
        except Exception:
            pass

def start_service_process_or_container(service_id: str, port: int, container_name: str):
    """Starts microservice uvicorn process or Docker container for service."""
    stop_service_process_or_container(service_id, port, container_name)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    app_dir = os.path.join(repo_root, "labs", service_id, "app")

    if os.path.exists(app_dir):
        env = os.environ.copy()
        env["PYTHONPATH"] = app_dir

        try:
            conn = database.get_db_connection()
            service = conn.execute("SELECT difficulty, environment_purpose FROM microservices WHERE id = ?", (service_id,)).fetchone()
            conn.close()
            if service:
                if service["difficulty"]:
                    env["DIFFICULTY_LEVEL"] = service["difficulty"]
                if service["environment_purpose"]:
                    env["ENVIRONMENT_PURPOSE"] = service["environment_purpose"]
        except Exception as e:
            logger.warning(f"Could not read difficulty/purpose from DB for service {service_id}: {e}")

        log_file = f"/tmp/{service_id}.log"
        with open(log_file, "a") as f:
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port), "--app-dir", app_dir],
                env=env,
                stdout=f,
                stderr=f,
                cwd=repo_root
            )
        logger.info(f"Started uvicorn process for service {service_id} on port {port}")
    else:
        if container_name:
            try:
                subprocess.run(["docker", "start", container_name], capture_output=True)
                logger.info(f"Started docker container {container_name} for service {service_id}")
            except Exception as e:
                logger.error(f"Failed to start Docker container {container_name}: {e}")

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
async def dashboard_home(request: Request, q: Optional[str] = None, page: int = Query(1, ge=1)):
    limit = 20
    offset = (page - 1) * limit

    conn = database.get_db_connection()
    # Always fetch all services for the right sidebar panel
    all_services = [dict(row) for row in conn.execute("SELECT * FROM microservices ORDER BY name ASC").fetchall()]

    if q:
        query_like = f"%{q.strip().lower()}%"
        sql = """
            SELECT * FROM microservices
            WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(tags) LIKE ? OR LOWER(category) LIKE ?
            ORDER BY name ASC
            LIMIT ? OFFSET ?
        """
        count_sql = """
            SELECT COUNT(*) as count FROM microservices
            WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(tags) LIKE ? OR LOWER(category) LIKE ?
        """
        services = [dict(row) for row in conn.execute(sql, (query_like, query_like, query_like, query_like, limit, offset)).fetchall()]
        total_count = conn.execute(count_sql, (query_like, query_like, query_like, query_like)).fetchone()["count"]
    else:
        services = [dict(row) for row in conn.execute("SELECT * FROM microservices ORDER BY name ASC LIMIT ? OFFSET ?", (limit, offset)).fetchall()]
        total_count = len(all_services)

    dns_settings = dict(conn.execute("SELECT * FROM dns_settings WHERE id = 1").fetchone())
    conn.close()

    total_pages = max(1, (total_count + limit - 1) // limit)
    hosts_line = mini_dns.generate_hosts_entry_text(dns_settings.get("host_ip", "127.0.0.1")) if DNS_AVAILABLE else ""
    hosts_cmd = mini_dns.generate_hosts_command(dns_settings.get("host_ip", "127.0.0.1")) if DNS_AVAILABLE else ""
    win_hosts_cmd = mini_dns.generate_windows_hosts_command(dns_settings.get("host_ip", "127.0.0.1")) if DNS_AVAILABLE else ""

    message = request.query_params.get("message")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "services": services,
            "all_services": all_services,
            "dns_settings": dns_settings,
            "hosts_line": hosts_line,
            "hosts_cmd": hosts_cmd,
            "win_hosts_cmd": win_hosts_cmd,
            "search_query": q or "",
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "current_version": CURRENT_VERSION,
            "message": message,
            "error": error
        }
    )

@app.get("/api/v1/system/check-update")
async def check_updates():
    return {
        "status": "success",
        "current_version": CURRENT_VERSION,
        "latest_version": CURRENT_VERSION,
        "update_available": False,
        "message": f"Platform is up to date (Version v{CURRENT_VERSION}). All microservices are synchronized."
    }

@app.get("/api/v1/services")
async def list_services(q: Optional[str] = None, page: int = Query(1, ge=1), limit: int = Query(20, le=50)):
    offset = (page - 1) * limit
    conn = database.get_db_connection()
    if q:
        query_like = f"%{q.strip().lower()}%"
        sql = """
            SELECT * FROM microservices
            WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(tags) LIKE ? OR LOWER(category) LIKE ?
            LIMIT ? OFFSET ?
        """
        services = [dict(row) for row in conn.execute(sql, (query_like, query_like, query_like, query_like, limit, offset)).fetchall()]
    else:
        services = [dict(row) for row in conn.execute("SELECT * FROM microservices LIMIT ? OFFSET ?", (limit, offset)).fetchall()]
    conn.close()
    return {"status": "success", "count": len(services), "services": services, "page": page}

@app.get("/api/v1/dns/config")
async def get_dns_config():
    conn = database.get_db_connection()
    dns_settings = dict(conn.execute("SELECT * FROM dns_settings WHERE id = 1").fetchone())
    conn.close()
    hosts_line = mini_dns.generate_hosts_entry_text(dns_settings.get("host_ip", "127.0.0.1")) if DNS_AVAILABLE else ""
    hosts_cmd = mini_dns.generate_hosts_command(dns_settings.get("host_ip", "127.0.0.1")) if DNS_AVAILABLE else ""
    win_hosts_cmd = mini_dns.generate_windows_hosts_command(dns_settings.get("host_ip", "127.0.0.1")) if DNS_AVAILABLE else ""
    return {"status": "success", "dns_settings": dns_settings, "hosts_line": hosts_line, "hosts_command": hosts_cmd, "win_hosts_command": win_hosts_cmd}

@app.get("/api/v1/dns/hosts-command")
async def get_hosts_command():
    conn = database.get_db_connection()
    dns_settings = dict(conn.execute("SELECT * FROM dns_settings WHERE id = 1").fetchone())
    conn.close()
    host_ip = dns_settings.get("host_ip", "127.0.0.1")
    hosts_cmd = mini_dns.generate_hosts_command(host_ip) if DNS_AVAILABLE else ""
    win_hosts_cmd = mini_dns.generate_windows_hosts_command(host_ip) if DNS_AVAILABLE else ""
    return {"status": "success", "hosts_command": hosts_cmd, "win_hosts_command": win_hosts_cmd, "host_ip": host_ip}

@app.post("/api/v1/dns/sync-hosts")
async def api_sync_dns_hosts():
    if DNS_AVAILABLE:
        conn = database.get_db_connection()
        dns_settings = conn.execute("SELECT host_ip FROM dns_settings WHERE id = 1").fetchone()
        conn.close()
        ip = dns_settings["host_ip"] if dns_settings else "127.0.0.1"
        success = mini_dns.sync_etc_hosts(ip)
        return {"status": "success" if success else "warning", "message": "Synced to /etc/hosts" if success else "Failed to write to /etc/hosts directly"}
    return {"status": "error", "message": "DNS module not available"}

@app.post("/web/dns/sync-hosts")
async def web_sync_dns_hosts():
    if DNS_AVAILABLE:
        conn = database.get_db_connection()
        dns_settings = conn.execute("SELECT host_ip FROM dns_settings WHERE id = 1").fetchone()
        conn.close()
        ip = dns_settings["host_ip"] if dns_settings else "127.0.0.1"
        success = mini_dns.sync_etc_hosts(ip)
        msg = "Successfully+synced+lab+domains+to+/etc/hosts" if success else "Attempted+hosts+sync.+If+permissions+failed,+run+the+sudo+command."
    else:
        msg = "DNS+module+unavailable"
    return RedirectResponse(
        url=f"/?message={msg}",
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.post("/api/v1/dns/configure")
async def configure_dns_api(config: DNSConfigUpdate):
    global dns_server_instance
    dns_port_val = config.dns_port if config.dns_port is not None else 5353
    conn = database.get_db_connection()
    conn.execute("""
        UPDATE dns_settings
        SET dns_enabled = ?, host_ip = ?, dns_port = ?
        WHERE id = 1
    """, (1 if config.dns_enabled else 0, config.host_ip, dns_port_val))
    conn.commit()
    conn.close()

    if DNS_AVAILABLE:
        mini_dns.sync_etc_hosts(config.host_ip)

    if config.dns_enabled and DNS_AVAILABLE:
        if dns_server_instance is None:
            dns_server_instance = mini_dns.MiniDNSServer(host="0.0.0.0", port=dns_port_val)
            dns_server_instance.start()
            logger.info(f"Started Mini DNS Server on UDP port {dns_port_val}")
    elif not config.dns_enabled and dns_server_instance:
        dns_server_instance.stop()
        dns_server_instance = None

    return {"status": "success", "message": "DNS settings updated successfully."}

@app.post("/web/dns/configure")
async def web_configure_dns(
    dns_enabled: Optional[str] = Form(None),
    host_ip: str = Form("127.0.0.1")
):
    enabled_bool = (dns_enabled is not None and dns_enabled.lower() in ["on", "true", "1", "yes"])
    config = DNSConfigUpdate(dns_enabled=enabled_bool, host_ip=host_ip)
    await configure_dns_api(config)
    return RedirectResponse(
        url=f"/?message=DNS+Settings+Updated.+Host+IP={host_ip}",
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

    tags_val = config.tags or service["tags"]
    conn.execute("""
        UPDATE microservices
        SET configured_port = ?, local_domain = ?, difficulty = ?, environment_purpose = ?, tags = ?
        WHERE id = ?
    """, (config.configured_port, config.local_domain, config.difficulty.lower(), config.environment_purpose.lower(), tags_val, service_id))
    conn.commit()
    conn.close()

    if DNS_AVAILABLE:
        mini_dns.sync_etc_hosts()

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

    port = service["configured_port"]
    container_name = service["container_name"]

    if action in ["stop"]:
        stop_service_process_or_container(service_id, port, container_name)
        new_status = "stopped"
    elif action in ["start", "restart"]:
        start_service_process_or_container(service_id, port, container_name)
        new_status = "running"

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
    tags: Optional[str] = Form(None),
    action: Optional[str] = Form(None)
):
    try:
        config = ServiceConfigUpdate(
            configured_port=configured_port,
            local_domain=local_domain,
            difficulty=difficulty,
            environment_purpose=environment_purpose,
            tags=tags
        )
        await configure_service_api(service_id, config)

        if action in ["start", "stop", "restart"]:
            await update_service_status_api(service_id, action)

        return RedirectResponse(
            url=f"/?message=Configuration+updated+for+{service_id}.+Port:+{configured_port}+|+Mode:+{environment_purpose.upper()}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except HTTPException as e:
        return RedirectResponse(
            url=f"/?error={e.detail}",
            status_code=status.HTTP_303_SEE_OTHER
        )
