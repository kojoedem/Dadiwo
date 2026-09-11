import os
import pytest
from fastapi.testclient import TestClient

os.environ["DB_PATH"] = "test_mobile.db"

import database
from main import app

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_mobile.db"):
        os.remove("test_mobile.db")
    database.init_db()
    yield
    if os.path.exists("test_mobile.db"):
        os.remove("test_mobile.db")

def test_bluetooth_pairing():
    client = TestClient(app)
    response = client.post(
        "/bluetooth/pair",
        data={"attacker_mac": "00:11:22:33:44:55", "pin": "0000"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "FLAG" in response.headers.get("location")

def test_bluetooth_exfiltration_api():
    client = TestClient(app)
    response = client.get("/api/v1/bluetooth/exfiltrate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "vulnerable"
    assert "contacts" in data
