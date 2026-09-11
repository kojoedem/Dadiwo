import os
import pytest

os.environ["MANAGER_DB_PATH"] = "test_manager.db"

import database
from main import app
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_manager.db"):
        os.remove("test_manager.db")
    database.init_db()
    yield
    if os.path.exists("test_manager.db"):
        os.remove("test_manager.db")

def test_list_services_and_search():
    client = TestClient(app)
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] >= 5

    # Search by tag
    res_search = client.get("/api/v1/services?q=sqli")
    assert res_search.status_code == 200
    assert len(res_search.json()["services"]) >= 1

def test_get_single_service():
    client = TestClient(app)
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    services = response.json()["services"]
    atm_service = next(s for s in services if s["id"] == "atm")
    assert atm_service["id"] == "atm"
    assert atm_service["configured_port"] == 8080

def test_check_updates():
    client = TestClient(app)
    response = client.get("/api/v1/system/check-update")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "current_version" in data

def test_get_dns_config():
    client = TestClient(app)
    response = client.get("/api/v1/dns/config")
    assert response.status_code == 200
    assert response.json()["dns_settings"]["dns_port"] == 5353

def test_configure_dns():
    client = TestClient(app)
    payload = {
        "dns_enabled": True,
        "host_ip": "192.168.1.100",
        "dns_port": 5353
    }
    response = client.post("/api/v1/dns/configure", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_configure_service():
    client = TestClient(app)
    payload = {
        "configured_port": 8888,
        "local_domain": "custom-atm.lab",
        "difficulty": "advanced",
        "environment_purpose": "networking",
        "tags": "web, custom"
    }
    response = client.post("/api/v1/services/atm/configure", json=payload)
    assert response.status_code == 200

    updated = client.get("/api/v1/services").json()["services"]
    atm_service = next(s for s in updated if s["id"] == "atm")
    assert atm_service["configured_port"] == 8888
    assert atm_service["local_domain"] == "custom-atm.lab"
    assert atm_service["environment_purpose"] == "networking"

def test_update_service_status():
    client = TestClient(app)
    response = client.post("/api/v1/services/atm/status?action=start")
    assert response.status_code == 200
    assert response.json()["current_status"] == "running"

    updated = client.get("/api/v1/services").json()["services"]
    atm_service = next(s for s in updated if s["id"] == "atm")
    assert atm_service["status"] == "running"
