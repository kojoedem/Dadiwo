import pytest
from fastapi.testclient import TestClient
import main
import database

client = TestClient(main.app)

@pytest.fixture(autouse=True)
def reset_snmp_settings():
    client.post("/api/v1/configure?difficulty=beginner&environment_purpose=cybersecurity")

def test_snmp_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "SNMP Microservice" in response.text

def test_snmp_get_request():
    response = client.post("/api/v1/snmp/execute", json={
        "version": "v2c",
        "community_or_user": "public",
        "pdu_type": "GET",
        "oid": ".1.3.6.1.2.1.1.1.0"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Dadiwoo Enterprise" in data["value"]

def test_snmp_walk_request():
    response = client.post("/api/v1/snmp/execute", json={
        "version": "v2c",
        "community_or_user": "public",
        "pdu_type": "WALK",
        "oid": ".1.3.6.1.4.1.9999"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] > 0

def test_snmp_set_request():
    response = client.post("/api/v1/snmp/execute", json={
        "version": "v2c",
        "community_or_user": "private",
        "pdu_type": "SET",
        "oid": ".1.3.6.1.2.1.1.5.0",
        "set_value": "NEW-CORE-GW-01"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["new_value"] == "NEW-CORE-GW-01"

def test_snmpv3_authpriv_request():
    response = client.post("/api/v1/snmp/execute", json={
        "version": "v3",
        "community_or_user": "admin_snmpv3",
        "pdu_type": "GET",
        "oid": ".1.3.6.1.4.1.9999.1.4.0",
        "auth_pass": "AdminAuthPass123",
        "priv_pass": "AdminPrivPass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "FLAG{SNMPV3_AUTHPRIV_USM_DECRYPTED_2026}" in data["value"]

def test_snmp_configure_endpoint():
    response = client.post("/api/v1/configure?difficulty=secure&environment_purpose=cybersecurity")
    assert response.status_code == 200
    data = response.json()
    assert data["difficulty"] == "secure"
