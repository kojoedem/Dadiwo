import os
import pytest
from fastapi.testclient import TestClient

os.environ["DB_PATH"] = "test_bank.db"

import database
from main import app

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_bank.db"):
        os.remove("test_bank.db")
    database.init_db()
    yield
    if os.path.exists("test_bank.db"):
        os.remove("test_bank.db")

def test_bank_login():
    client = TestClient(app)
    response = client.post("/login", data={"username": "user1", "password": "bankpass123"}, follow_redirects=False)
    assert response.status_code == 303
    assert "session_user=user1" in response.headers.get("set-cookie")

def test_bank_transfer():
    client = TestClient(app)
    response = client.post(
        "/transfer",
        data={"recipient_account": "ACC-BANK-102", "amount": 100.0, "memo": "Test Transfer"},
        headers={"cookie": "session_user=user1"},
        follow_redirects=False
    )
    assert response.status_code == 303
