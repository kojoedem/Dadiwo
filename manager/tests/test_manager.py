import os
import pytest
from fastapi.testclient import TestClient

os.environ["MANAGER_DB_PATH"] = "test_manager.db"

import database
from main import app

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_manager.db"):
        os.remove("test_manager.db")
    database.init_db()
    yield
    if os.path.exists("test_manager.db"):
        os.remove("test_manager.db")

def test_list_services():
    client = TestClient(app)
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] >= 4

def test_get_single_service():
    client = TestClient(app)
    response = client.get("/api/v1/services/atm")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "atm"
    assert data["configured_port"] == 8080
    assert data["local_domain"] == "atm.lab"

def test_configure_service():
    client = TestClient(app)
    payload = {
        "configured_port": 8888,
        "local_domain": "custom-atm.lab",
        "difficulty": "advanced"
    }
    response = client.post("/api/v1/services/atm/configure", json=payload)
    assert response.status_code == 200

    # Verify update in DB
    updated = client.get("/api/v1/services/atm").json()
    assert updated["configured_port"] == 8888
    assert updated["local_domain"] == "custom-atm.lab"
    assert updated["difficulty"] == "advanced"

def test_update_service_status():
    client = TestClient(app)
    response = client.post("/api/v1/services/atm/status?action=start")
    assert response.status_code == 200
    assert response.json()["current_status"] == "running"

    updated = client.get("/api/v1/services/atm").json()
    assert updated["status"] == "running"
