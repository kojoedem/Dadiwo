import os
import pytest
from fastapi.testclient import TestClient

# Set DB_PATH to test db before importing app
os.environ["DB_PATH"] = "test_atm.db"

import database
from main import app

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_atm.db"):
        os.remove("test_atm.db")
    database.init_db()
    yield
    if os.path.exists("test_atm.db"):
        os.remove("test_atm.db")

def test_health_and_mode():
    client = TestClient(app)
    response = client.get("/api/v1/mode")
    assert response.status_code == 200
    data = response.json()
    assert "secure_mode" in data

def test_login_success():
    client = TestClient(app)
    response = client.post("/login", data={"card_number": "4000123456781001", "pin": "1234"}, follow_redirects=False)
    assert response.status_code == 303
    assert "session_account=ACC-1001" in response.headers.get("set-cookie")

def test_vulnerable_mode_idor():
    import main
    main.SECURE_MODE = False
    main.DIFFICULTY_LEVEL = "beginner"
    client = TestClient(app)

    # In vulnerable mode, unauthenticated request to admin account succeeds and reveals flag
    response = client.get("/api/v1/accounts/ACC-9000")
    assert response.status_code == 200
    data = response.json()
    assert data["account_number"] == "ACC-9000"
    assert "FLAG{" in data["flag"]

def test_vulnerable_mode_negative_withdrawal_logic_flaw():
    import main
    main.SECURE_MODE = False
    main.DIFFICULTY_LEVEL = "intermediate"
    client = TestClient(app)

    # Get initial balance
    res1 = client.get("/api/v1/accounts/ACC-1001")
    init_bal = res1.json()["balance"]

    # Negative withdrawal adds balance in intermediate difficulty mode
    client.post(
        "/transaction",
        data={"account_number": "ACC-1001", "action": "WITHDRAW", "amount": -1000},
        headers={"cookie": "session_account=ACC-1001"}
    )

    res2 = client.get("/api/v1/accounts/ACC-1001")
    new_bal = res2.json()["balance"]
    assert new_bal == init_bal - (-1000)

def test_secure_mode_idor_blocked():
    import main
    main.SECURE_MODE = True
    main.DIFFICULTY_LEVEL = "secure"
    client = TestClient(app)

    # Unauthenticated request fails in secure mode (401)
    response = client.get("/api/v1/accounts/ACC-9000")
    assert response.status_code == 401

    # Authenticated user requesting another user's account fails in secure mode (403)
    response_auth = client.get(
        "/api/v1/accounts/ACC-9000",
        headers={"cookie": "session_account=ACC-1001"}
    )
    assert response_auth.status_code == 403

def test_secure_mode_negative_amount_blocked():
    import main
    main.SECURE_MODE = True
    main.DIFFICULTY_LEVEL = "secure"
    client = TestClient(app)

    response = client.post(
        "/transaction",
        data={"account_number": "ACC-1001", "action": "WITHDRAW", "amount": -500},
        headers={"cookie": "session_account=ACC-1001"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "error=Amount+must+be+greater+than+zero" in response.headers.get("location")
