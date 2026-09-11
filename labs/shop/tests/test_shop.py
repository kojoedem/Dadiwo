import os
import pytest
from fastapi.testclient import TestClient

os.environ["DB_PATH"] = "test_shop.db"

import database
from main import app

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_shop.db"):
        os.remove("test_shop.db")
    database.init_db()
    yield
    if os.path.exists("test_shop.db"):
        os.remove("test_shop.db")

def test_shop_checkout():
    client = TestClient(app)
    response = client.post("/checkout", data={"product_id": 1, "price": 10.00, "coupon": "DISCOUNT20"}, follow_redirects=False)
    assert response.status_code == 303

def test_order_lookup():
    client = TestClient(app)
    response = client.get("/order?order_id=ORD-9000")
    assert response.status_code == 200
    assert "FLAG{SHOP_COUPON_REUSE_PRICING_FLAW_2026}" in response.text
