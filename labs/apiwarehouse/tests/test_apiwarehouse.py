import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

import database
from main import app

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_apiwarehouse.db"
    monkeypatch.setenv("DB_PATH", str(db_file))
    database.DB_PATH = str(db_file)
    database.init_db()
    yield

def test_debug_keys_leak():
    client = TestClient(app)
    response = client.get("/api/v1/debug/keys")
    assert response.status_code == 200
    data = response.json()
    assert "keys" in data
    assert len(data["keys"]) >= 4

def test_postman_collection_export():
    client = TestClient(app)
    response = client.get("/api/v1/postman-collection")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["name"] == "Dadiwoo API Warehouse Hacking Collection"
    assert len(data["item"]) >= 5

def test_auth_token_generation_hs256_and_none():
    client = TestClient(app)
    # HS256 token
    res1 = client.post("/api/v1/auth/token", json={"username": "guest_user", "algorithm": "HS256"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["token_type"] == "Bearer"
    assert "access_token" in data1

    # JWT none flaw token
    res2 = client.post("/api/v1/auth/token", json={"username": "admin_boss", "algorithm": "none"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["access_token"].startswith("eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0")

def test_inventory_list_and_idor():
    client = TestClient(app)
    # List items with API key
    res = client.get("/api/v1/inventory", headers={"X-API-Key": "ak_guest_88291029"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["count"] >= 4

    # Get restricted item ID 3
    res_item = client.get("/api/v1/inventory/3", headers={"X-API-Key": "ak_guest_88291029"})
    assert res_item.status_code == 200
    assert res_item.json()["item"]["id"] == 3

def test_graphql_introspection():
    client = TestClient(app)
    query = {"query": "{ __schema { types { name } } }"}
    res = client.post("/api/v1/graphql", json=query)
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    assert "__schema" in data["data"]

def test_mass_assignment_inventory_create():
    client = TestClient(app)
    payload = {
        "item_code": "SKU-MASS-01",
        "name": "Mass Assignment Secret Box",
        "category": "Defense",
        "quantity": 100,
        "price": 0.0,
        "is_restricted": 1,
        "owner_user_id": 3
    }
    res = client.post("/api/v1/inventory", json=payload, headers={"X-API-Key": "ak_guest_88291029"})
    assert res.status_code == 201
    assert res.json()["item"]["is_restricted"] == 1

def test_webhook_and_admin_export():
    client = TestClient(app)
    webhook_payload = {"target_url": "http://127.0.0.1:9000/api/v1/services", "event_type": "ssrf_test"}
    res_wh = client.post("/api/v1/webhooks", json=webhook_payload, headers={"X-API-Key": "ak_guest_88291029"})
    assert res_wh.status_code == 200
    assert res_wh.json()["status"] == "success"

    res_exp = client.get("/api/v1/admin/export", headers={"X-API-Key": "ak_auditor_31415926"})
    assert res_exp.status_code == 200
    assert "users" in res_exp.json()

def test_secure_mode_enforcement():
    client = TestClient(app)
    # Switch to secure mode
    conf_res = client.post("/api/v1/configure", json={"difficulty": "secure", "environment_purpose": "cybersecurity"})
    assert conf_res.status_code == 200

    # Debug keys should be disabled
    dbg_res = client.get("/api/v1/debug/keys")
    assert dbg_res.status_code == 403

    # GraphQL introspection should be disabled
    gql_res = client.post("/api/v1/graphql", json={"query": "{ __schema { types { name } } }"})
    assert gql_res.status_code == 400

    # Unauthenticated inventory access should fail
    inv_res = client.get("/api/v1/inventory")
    assert inv_res.status_code == 401

    # Security auditor key should work for auditing
    aud_res = client.get("/api/v1/inventory", headers={"X-API-Key": "ak_auditor_31415926"})
    assert aud_res.status_code == 200
