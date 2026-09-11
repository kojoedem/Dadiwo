import os
import pytest
from fastapi.testclient import TestClient

os.environ["DB_PATH"] = "test_isp.db"

import database
from main import app

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_isp.db"):
        os.remove("test_isp.db")
    database.init_db()
    yield
    if os.path.exists("test_isp.db"):
        os.remove("test_isp.db")

def test_radius_subscribers():
    client = TestClient(app)
    response = client.get("/api/v1/radius/subscribers")
    assert response.status_code == 200
    data = response.json()
    assert len(data["subscribers"]) >= 3

def test_diagnostics_ping():
    client = TestClient(app)
    response = client.post("/diagnostics", data={"host": "127.0.0.1"})
    assert response.status_code == 200
    assert "ping" in response.text.lower() or "ping" in response.content.decode().lower()
