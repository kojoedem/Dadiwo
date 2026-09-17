import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import main

client = TestClient(main.app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Wave Chat" in response.text
    assert "alex_ceo" in response.text

import uuid

def test_user_registration():
    rand_id = uuid.uuid4().hex[:6]
    username = f"agent_{rand_id}"
    response = client.post(
        "/register",
        data={
            "username": username,
            "pin": "1234",
            "full_name": "Test Agent Zero",
            "email": "agent0@wavechat.lab",
            "phone": "+1-555-010-0000",
            "location": "Quantico, VA",
            "workplace": "Cyber Division",
            "job_title": "Field Agent",
            "bio": "Special OSINT Agent testing Wave Chat.",
            "relationship_status": "Single"
        },
        follow_redirects=False
    )
    assert response.status_code == 303
    assert f"/profile/{username}" in response.headers["location"]

def test_login_logout():
    login_resp = client.post(
        "/login",
        data={"username": "alex_ceo", "pin": "1234"},
        follow_redirects=False
    )
    assert login_resp.status_code == 303
    assert "session_wave_user=alex_ceo" in login_resp.headers.get("set-cookie", "")

    logout_resp = client.get("/logout", follow_redirects=False)
    assert logout_resp.status_code == 303

def test_post_creation_and_10_photos_compression():
    # Login first
    client.post("/login", data={"username": "alex_ceo", "pin": "1234"})

    # Create 10 test images in memory (e.g. 500x500 PNG)
    files = []
    for i in range(10):
        img = Image.new("RGB", (500, 500), color=(i * 20, 100, 200))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        files.append(("photos", (f"test_photo_{i}.png", img_byte_arr.getvalue(), "image/png")))

    response = client.post(
        "/posts/create",
        data={"caption": "Batch upload of 10 test photos for compression analysis", "location_tag": "Lab Test Grid"},
        files=files,
        follow_redirects=False
    )
    assert response.status_code == 303

    # Check that post and photos were created in database
    posts_resp = client.get("/api/v1/posts")
    assert posts_resp.status_code == 200
    data = posts_resp.json()
    assert data["count"] >= 1

    latest_post = data["posts"][0]
    assert len(latest_post["photos"]) == 10
    for photo in latest_post["photos"]:
        # Verify picture file size is reduced to small KB size (< 50 KB)
        assert photo["file_size_kb"] < 50.0

def test_osint_api_endpoints():
    users_resp = client.get("/api/v1/users")
    assert users_resp.status_code == 200
    users_data = users_resp.json()
    assert users_data["count"] >= 5

    user_detail_resp = client.get("/api/v1/users/alex_ceo")
    assert user_detail_resp.status_code == 200
    detail_data = user_detail_resp.json()
    assert detail_data["username"] == "alex_ceo"
    assert "FLAG{" in detail_data["flag"]

def test_configure_endpoint():
    config_resp = client.post("/api/v1/configure?difficulty=secure&environment_purpose=cybersecurity")
    assert config_resp.status_code == 200
    res = config_resp.json()
    assert res["difficulty"] == "secure"
    assert res["secure_mode"] is True
