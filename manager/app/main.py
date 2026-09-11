import os
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

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger("cyber_range_manager")

app = FastAPI(
    title="Cyber Range Central Manager Dashboard",
    description="Control plane for deploying, configuring, and monitoring cyber range microservices.",
    version="1.0.0"
)

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

class ServiceConfigUpdate(BaseModel):
    configured_port: int
    local_domain: str
    difficulty: str

def notify_microservice_config(service_id: str, configured_port: int, difficulty: str):
    """
    Notifies the running microservice instance to dynamically sync its active difficulty configuration.
    """
    target_url = f"http://localhost:{configured_port}/api/v1/configure?difficulty={urllib.parse.quote(difficulty)}"
    try:
        req = urllib.request.Request(target_url, method="POST")
        with urllib.request.urlopen(req, timeout=2) as response:
            logger.info(f"Sync response from {service_id} on port {configured_port}: {response.status}")
    except Exception as e:
        logger.warning(f"Could not sync live config with service {service_id} on port {configured_port}: {e}")

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    conn = database.get_db_connection()
    services = [dict(row) for row in conn.execute("SELECT * FROM microservices").fetchall()]
    conn.close()

    message = request.query_params.get("message")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "services": services,
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

@app.get("/api/v1/services/{service_id}")
async def get_service(service_id: str):
    conn = database.get_db_connection()
    service = conn.execute("SELECT * FROM microservices WHERE id = ?", (service_id,)).fetchone()
    conn.close()
    if not service:
        raise HTTPException(status_code=404, detail="Microservice not found")
    return dict(service)

@app.post("/api/v1/services/{service_id}/configure")
async def configure_service_api(service_id: str, config: ServiceConfigUpdate):
    if config.configured_port < 1024 or config.configured_port > 65535:
        raise HTTPException(status_code=400, detail="Port must be between 1024 and 65535")

    allowed_levels = ["beginner", "intermediate", "advanced", "expert", "secure"]
    if config.difficulty.lower() not in allowed_levels:
        raise HTTPException(status_code=400, detail=f"Invalid difficulty. Allowed: {allowed_levels}")

    conn = database.get_db_connection()
    service = conn.execute("SELECT * FROM microservices WHERE id = ?", (service_id,)).fetchone()
    if not service:
        conn.close()
        raise HTTPException(status_code=404, detail="Microservice not found")

    conn.execute("""
        UPDATE microservices
        SET configured_port = ?, local_domain = ?, difficulty = ?
        WHERE id = ?
    """, (config.configured_port, config.local_domain, config.difficulty.lower(), service_id))
    conn.commit()
    conn.close()

    # Synchronize configuration change with live microservice
    notify_microservice_config(service_id, config.configured_port, config.difficulty)

    logger.info(f"Updated microservice {service_id}: port={config.configured_port}, domain={config.local_domain}, difficulty={config.difficulty}")
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
    action: Optional[str] = Form(None)
):
    try:
        config = ServiceConfigUpdate(
            configured_port=configured_port,
            local_domain=local_domain,
            difficulty=difficulty
        )
        await configure_service_api(service_id, config)

        if action in ["start", "stop", "restart"]:
            await update_service_status_api(service_id, action)

        return RedirectResponse(
            url=f"/?message=Configuration+updated+for+{service_id}.+Local+URL:+http://{local_domain}:{configured_port}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except HTTPException as e:
        return RedirectResponse(
            url=f"/?error={e.detail}",
            status_code=status.HTTP_303_SEE_OTHER
        )
