import pytest
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "bitroot"

def test_subdomains_api():
    response = client.get("/api/v1/subdomains")
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "bitroot.lab"
    assert data["total_subdomains"] == 14
    assert data["active_subdomains"] == 10
    assert data["dead_subdomains"] == 4

def test_root_domain():
    response = client.get("/", headers={"Host": "bitroot.lab"})
    assert response.status_code == 200
    assert "Bitroot Cyber Systems Lab" in response.text
    assert "bitroot.lab" in response.text

def test_active_subdomains():
    active_subs = [
        "api", "dev", "admin", "portal", "staging",
        "auth", "vpn", "shop", "blog", "status"
    ]
    for sub in active_subs:
        fqdn = f"{sub}.bitroot.lab"
        response = client.get("/", headers={"Host": fqdn})
        assert response.status_code == 200, f"Expected 200 for {fqdn}"

def test_api_subdomain_json():
    response = client.get("/api/v1/users", headers={"Host": "api.bitroot.lab", "Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Bitroot REST API Gateway v2"

def test_dead_subdomains():
    dead_subs = ["old-api", "legacy", "sandbox"]
    for sub in dead_subs:
        fqdn = f"{sub}.bitroot.lab"
        response = client.get("/", headers={"Host": fqdn})
        assert response.status_code == 503, f"Expected 503 for dead subdomain {fqdn}"

    response = client.get("/", headers={"Host": "test-internal.bitroot.lab"})
    assert response.status_code == 404

def test_waf_headers():
    # Cloudflare WAF headers on admin.bitroot.lab
    resp_admin = client.get("/", headers={"Host": "admin.bitroot.lab"})
    assert resp_admin.status_code == 200
    assert resp_admin.headers.get("Server") == "cloudflare"
    assert "CF-RAY" in resp_admin.headers

    # ModSecurity WAF headers on vpn.bitroot.lab
    resp_vpn = client.get("/", headers={"Host": "vpn.bitroot.lab"})
    assert resp_vpn.status_code == 200
    assert "Mod-Security" in resp_vpn.headers.get("X-Mod-Security", "") or "Apache" in resp_vpn.headers.get("Server", "")

def test_waf_blocking():
    # Cloudflare WAF block on admin.bitroot.lab when probed with scanner payload
    resp_cf = client.get("/?payload=<script>alert(1)</script>", headers={
        "Host": "admin.bitroot.lab",
        "User-Agent": "wafw00f/2.1.0"
    })
    assert resp_cf.status_code == 403
    assert "Cloudflare" in resp_cf.text

    # ModSecurity WAF block on vpn.bitroot.lab
    resp_modsec = client.get("/?q=select%20*%20from%20users", headers={
        "Host": "vpn.bitroot.lab",
        "User-Agent": "wafw00f/2.1.0"
    })
    assert resp_modsec.status_code == 406
    assert "ModSecurity" in resp_modsec.text

def test_configure_endpoint():
    response = client.get("/api/v1/configure?difficulty=intermediate&environment_purpose=networking")
    assert response.status_code == 200
    data = response.json()
    assert data["difficulty"] == "intermediate"
    assert data["environment_purpose"] == "networking"
