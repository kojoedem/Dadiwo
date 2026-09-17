import pytest
from fastapi.testclient import TestClient
import main
import database

client = TestClient(main.app)

@pytest.fixture(autouse=True)
def reset_ssh_settings():
    client.post("/api/v1/configure?difficulty=beginner&environment_purpose=cybersecurity")

def test_ssh_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "SSH Microservice" in response.text

def test_simulate_login_success():
    response = client.post("/api/v1/ssh/simulate-login", json={
        "username": "user",
        "password": "user123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["role"] == "user"

def test_simulate_login_failure():
    response = client.post("/api/v1/ssh/simulate-login", json={
        "username": "admin",
        "password": "WrongPassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"

def test_download_ssh_key():
    response = client.get("/ssh/keys/download/id_rsa_user")
    assert response.status_code == 200
    assert "BEGIN RSA PRIVATE KEY" in response.text or "BEGIN PRIVATE KEY" in response.text

def test_unban_ip_endpoint():
    response = client.post("/api/v1/ssh/unban", data={"ip_address": "192.168.1.100"})
    assert response.status_code in [200, 303]

def test_ssh_configure_endpoint():
    response = client.post("/api/v1/configure?difficulty=secure&environment_purpose=cybersecurity")
    assert response.status_code == 200
    data = response.json()
    assert data["difficulty"] == "secure"
