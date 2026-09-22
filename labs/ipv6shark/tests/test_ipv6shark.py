import pytest
import os
from fastapi.testclient import TestClient

# Ensure test DB path is isolated
os.environ["IPV6SHARK_DB_PATH"] = "test_ipv6shark.db"

from main import app, database

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_ipv6shark.db"):
        os.remove("test_ipv6shark.db")
    database.init_db()
    yield
    if os.path.exists("test_ipv6shark.db"):
        os.remove("test_ipv6shark.db")

client = TestClient(app)

def test_home_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "IPv6 Shark" in response.text
    assert "http://ipv6.lab:8090" in response.text

def test_configure_api():
    get_res = client.get("/api/v1/configure")
    assert get_res.status_code == 200
    assert get_res.json()["difficulty_level"] == "beginner"

    post_res = client.post("/api/v1/configure", json={"difficulty": "advanced", "environment_purpose": "cybersecurity"})
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "success"

    get_res2 = client.get("/api/v1/configure")
    assert get_res2.json()["difficulty_level"] == "advanced"

def test_list_scenarios():
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] >= 5

    red_response = client.get("/api/v1/scenarios?type=red_team")
    assert red_response.status_code == 200
    for sc in red_response.json()["scenarios"]:
        assert sc["scenario_type"] == "red_team"

def test_get_scenario_by_id():
    response = client.get("/api/v1/scenarios/1")
    assert response.status_code == 200
    assert response.json()["scenario"]["id"] == 1

    not_found = client.get("/api/v1/scenarios/999")
    assert not_found.status_code == 404

def test_list_posts():
    response = client.get("/api/v1/posts")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["posts"]) >= 2

def test_ipv6_ping():
    response = client.get("/api/v1/ipv6/ping?target=2001:db8::1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "2001:db8::1" in data["output"]

def test_ndp_table_operations():
    get_res = client.get("/api/v1/ipv6/ndp-table")
    assert get_res.status_code == 200
    initial_count = get_res.json()["count"]

    add_res = client.post("/api/v1/ipv6/ndp-table", json={
        "ipv6_address": "2001:db8:cyber:1::999",
        "mac_address": "00:aa:bb:cc:dd:ee",
        "interface": "eth0",
        "state": "REACHABLE"
    })
    assert add_res.status_code == 201
    assert add_res.json()["status"] == "success"

    get_res2 = client.get("/api/v1/ipv6/ndp-table")
    assert get_res2.json()["count"] == initial_count + 1
