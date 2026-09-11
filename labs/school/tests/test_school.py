import os
import pytest
from fastapi.testclient import TestClient

os.environ["DB_PATH"] = "test_school.db"

import database
from main import app

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_school.db"):
        os.remove("test_school.db")
    database.init_db()
    yield
    if os.path.exists("test_school.db"):
        os.remove("test_school.db")

def test_student_lookup():
    client = TestClient(app)
    response = client.get("/api/v1/students/STD-1001")
    assert response.status_code == 200
    assert response.json()["full_name"] == "Kofi Mensah"

def test_file_upload():
    client = TestClient(app)
    files = {"file": ("test.pdf", b"Dummy PDF content", "application/pdf")}
    response = client.post("/upload", files=files, follow_redirects=False)
    assert response.status_code == 303
