import os
import io
import uuid
import logging
from typing import Optional, List
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from PIL import Image

import database

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("wave_service")

DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
ENVIRONMENT_PURPOSE = os.environ.get("ENVIRONMENT_PURPOSE", "cybersecurity").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Wave Chat Social Media Microservice Cyber Range", version="1.0.0")

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def get_current_user(request: Request) -> Optional[dict]:
    session_user = request.cookies.get("session_wave_user")
    if not session_user:
        return None
    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session_user,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_active_certificate() -> dict:
    conn = database.get_db_connection()
    mode_target = "secure" if SECURE_MODE else "vulnerable"
    cert = conn.execute("SELECT * FROM certificates WHERE mode_type = ?", (mode_target,)).fetchone()
    conn.close()
    return dict(cert) if cert else {}

def compress_image(file_bytes: bytes, original_filename: str) -> tuple[str, float]:
    """
    Resizes image to max 400x400 thumbnail and compresses to JPEG (~5-30 KB size).
    Returns (saved_filename, file_size_kb).
    """
    unique_id = uuid.uuid4().hex[:8]
    ext = os.path.splitext(original_filename)[1].lower()
    if not ext or ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        ext = '.jpg'

    saved_filename = f"photo_{unique_id}.jpg"
    target_filepath = os.path.join(UPLOAD_DIR, saved_filename)

    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Max dimensions 400x400 to drastically lower file size
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)

        # Save with quality=50 to guarantee small KB size for microservice storage
        img.save(target_filepath, "JPEG", optimize=True, quality=50)

        file_size_bytes = os.path.getsize(target_filepath)
        file_size_kb = round(file_size_bytes / 1024.0, 2)
        return saved_filename, file_size_kb
    except Exception as e:
        logger.warning(f"Failed image processing with Pillow for {original_filename}: {e}")
        # Fallback: Save small chunk
        with open(target_filepath, "wb") as f:
            f.write(file_bytes[:1024 * 20])
        file_size_kb = round(os.path.getsize(target_filepath) / 1024.0, 2)
        return saved_filename, file_size_kb

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, q: Optional[str] = None):
    current_user = get_current_user(request)
    cert_info = get_active_certificate()
    conn = database.get_db_connection()

    if q:
        query_like = f"%{q.strip().lower()}%"
        users_rows = conn.execute("""
            SELECT username, full_name, job_title, workplace, location, bio, profile_pic
            FROM users
            WHERE LOWER(username) LIKE ? OR LOWER(full_name) LIKE ? OR LOWER(location) LIKE ? OR LOWER(workplace) LIKE ?
        """, (query_like, query_like, query_like, query_like)).fetchall()
    else:
        users_rows = conn.execute("""
            SELECT username, full_name, job_title, workplace, location, bio, profile_pic
            FROM users ORDER BY id ASC
        """).fetchall()

    users_list = [dict(u) for u in users_rows]

    # Fetch posts with user info and photos
    posts_rows = conn.execute("""
        SELECT p.id, p.username, p.caption, p.location_tag, p.created_at,
               u.full_name, u.profile_pic, u.job_title
        FROM posts p
        JOIN users u ON p.username = u.username
        ORDER BY p.id DESC
    """).fetchall()

    posts = []
    for pr in posts_rows:
        p_dict = dict(pr)
        photo_rows = conn.execute("""
            SELECT id, filename, original_filename, file_size_kb
            FROM photos WHERE post_id = ?
        """, (p_dict["id"],)).fetchall()
        p_dict["photos"] = [dict(ph) for ph in photo_rows]
        posts.append(p_dict)

    conn.close()

    error = request.query_params.get("error")
    message = request.query_params.get("message")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_user": current_user,
            "all_users": users_list,
            "posts": posts,
            "cert_info": cert_info,
            "search_query": q or "",
            "difficulty": DIFFICULTY_LEVEL,
            "purpose": ENVIRONMENT_PURPOSE,
            "secure_mode": SECURE_MODE,
            "error": error,
            "message": message
        }
    )

@app.get("/profile/{username}", response_class=HTMLResponse)
async def user_profile(request: Request, username: str):
    current_user = get_current_user(request)
    cert_info = get_active_certificate()
    conn = database.get_db_connection()

    profile_user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not profile_user:
        conn.close()
        return RedirectResponse(url="/?error=User+profile+not+found", status_code=status.HTTP_303_SEE_OTHER)

    user_dict = dict(profile_user)
    if SECURE_MODE and (not current_user or current_user["username"] != username):
        # In secure mode, censor sensitive OSINT fields / flags
        user_dict.pop("flag", None)
        user_dict.pop("pin", None)

    posts_rows = conn.execute("""
        SELECT p.id, p.username, p.caption, p.location_tag, p.created_at
        FROM posts p WHERE p.username = ? ORDER BY p.id DESC
    """, (username,)).fetchall()

    user_posts = []
    for pr in posts_rows:
        p_dict = dict(pr)
        photo_rows = conn.execute("""
            SELECT id, filename, original_filename, file_size_kb
            FROM photos WHERE post_id = ?
        """, (p_dict["id"],)).fetchall()
        p_dict["photos"] = [dict(ph) for ph in photo_rows]
        user_posts.append(p_dict)

    all_photos = conn.execute("""
        SELECT filename, file_size_kb, uploaded_at FROM photos WHERE username = ? ORDER BY id DESC
    """, (username,)).fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "current_user": current_user,
            "profile_user": user_dict,
            "user_posts": user_posts,
            "all_photos": [dict(ph) for ph in all_photos],
            "cert_info": cert_info,
            "difficulty": DIFFICULTY_LEVEL,
            "purpose": ENVIRONMENT_PURPOSE,
            "secure_mode": SECURE_MODE
        }
    )

@app.get("/certificate", response_class=HTMLResponse)
async def certificate_page(request: Request):
    current_user = get_current_user(request)
    cert_info = get_active_certificate()

    return templates.TemplateResponse(
        request=request,
        name="certificate.html",
        context={
            "current_user": current_user,
            "cert": cert_info,
            "difficulty": DIFFICULTY_LEVEL,
            "purpose": ENVIRONMENT_PURPOSE,
            "secure_mode": SECURE_MODE
        }
    )

@app.get("/certificate/download/cert.pem")
async def download_public_cert():
    cert = get_active_certificate()
    if not cert or not cert.get("public_cert_pem"):
        raise HTTPException(status_code=404, detail="Certificate not found")
    return PlainTextResponse(
        content=cert["public_cert_pem"],
        media_type="application/x-pem-file",
        headers={"Content-Disposition": "attachment; filename=wave_lab_cert.pem"}
    )

@app.get("/certificate/download/key.pem")
async def download_private_key():
    cert = get_active_certificate()
    if not cert or not cert.get("private_key_pem") or not cert.get("private_key_leaked"):
        raise HTTPException(status_code=403, detail="Private key is secure and non-exportable")
    return PlainTextResponse(
        content=cert["private_key_pem"],
        media_type="application/x-pem-file",
        headers={"Content-Disposition": "attachment; filename=wave_lab_private_key.pem"}
    )

@app.post("/login")
async def login(username: str = Form(...), pin: str = Form(...)):
    if ENVIRONMENT_PURPOSE == "networking":
        raise HTTPException(status_code=503, detail="Service in Networking Node Mode. Interactive Auth Suspended.")

    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND pin = ?", (username, pin)).fetchone()
    conn.close()

    if not user:
        return RedirectResponse(url="/?error=Invalid+username+or+PIN", status_code=status.HTTP_303_SEE_OTHER)

    response = RedirectResponse(url=f"/profile/{user['username']}?message=Welcome+back+{user['full_name']}!", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="session_wave_user", value=user["username"])
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_wave_user")
    return response

@app.post("/register")
async def register(
    username: str = Form(...),
    pin: str = Form("1234"),
    full_name: str = Form(...),
    bio: Optional[str] = Form(""),
    email: Optional[str] = Form(""),
    phone: Optional[str] = Form(""),
    location: Optional[str] = Form(""),
    workplace: Optional[str] = Form(""),
    job_title: Optional[str] = Form(""),
    relationship_status: Optional[str] = Form("Single"),
    profile_pic_file: Optional[UploadFile] = File(None)
):
    if ENVIRONMENT_PURPOSE == "networking":
        raise HTTPException(status_code=503, detail="Service in Networking Node Mode. Registration Suspended.")

    conn = database.get_db_connection()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username.strip(),)).fetchone()
    if existing:
        conn.close()
        return RedirectResponse(url="/?error=Username+already+taken.+Please+choose+another.", status_code=status.HTTP_303_SEE_OTHER)

    profile_pic_name = "default_avatar.jpg"
    if profile_pic_file and profile_pic_file.filename:
        content = await profile_pic_file.read()
        if content:
            profile_pic_name, _ = compress_image(content, profile_pic_file.filename)

    conn.execute("""
        INSERT INTO users (username, pin, full_name, bio, email, phone, location, workplace, job_title, relationship_status, profile_pic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username.strip(), pin, full_name, bio, email, phone, location, workplace, job_title, relationship_status, profile_pic_name))

    conn.commit()
    conn.close()

    logger.info(f"Registered new Wave Chat user: {username} ({full_name})")
    response = RedirectResponse(url=f"/profile/{username.strip()}?message=Account+created+successfully!", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="session_wave_user", value=username.strip())
    return response

@app.post("/posts/create")
async def create_post(
    request: Request,
    caption: str = Form(...),
    location_tag: Optional[str] = Form(""),
    photos: List[UploadFile] = File(...)
):
    if ENVIRONMENT_PURPOSE == "networking":
        raise HTTPException(status_code=503, detail="Service in Networking Node Mode. Post Creation Suspended.")

    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/?error=Please+login+to+create+a+post", status_code=status.HTTP_303_SEE_OTHER)

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (username, caption, location_tag)
        VALUES (?, ?, ?)
    """, (current_user["username"], caption, location_tag))
    post_id = cursor.lastrowid

    uploaded_count = 0
    total_kb_saved = 0.0

    for photo_file in photos:
        if photo_file and photo_file.filename:
            content = await photo_file.read()
            if content:
                saved_filename, size_kb = compress_image(content, photo_file.filename)
                cursor.execute("""
                    INSERT INTO photos (post_id, username, filename, original_filename, file_size_kb)
                    VALUES (?, ?, ?, ?, ?)
                """, (post_id, current_user["username"], saved_filename, photo_file.filename, size_kb))
                uploaded_count += 1
                total_kb_saved += size_kb

    conn.commit()
    conn.close()

    logger.info(f"User {current_user['username']} created post ID {post_id} with {uploaded_count} photos (total {total_kb_saved:.1f} KB)")
    return RedirectResponse(url=f"/?message=Post+published!+{uploaded_count}+photos+compressed+and+uploaded.", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/uploads/{filename}")
async def serve_upload(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

@app.get("/api/v1/users")
async def list_users_api():
    conn = database.get_db_connection()
    users = [dict(u) for u in conn.execute("SELECT id, username, full_name, email, phone, location, workplace, job_title, profile_pic FROM users").fetchall()]
    conn.close()
    return {"status": "success", "count": len(users), "users": users}

@app.get("/api/v1/users/{username}")
async def get_user_api(username: str):
    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User profile not found")

    user_dict = dict(user)
    if SECURE_MODE:
        user_dict.pop("flag", None)
        user_dict.pop("pin", None)

    posts_rows = conn.execute("SELECT * FROM posts WHERE username = ?", (username,)).fetchall()
    user_dict["posts"] = [dict(p) for p in posts_rows]
    conn.close()
    return user_dict

@app.get("/api/v1/posts")
async def list_posts_api():
    conn = database.get_db_connection()
    posts_rows = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    posts = []
    for pr in posts_rows:
        p_dict = dict(pr)
        photo_rows = conn.execute("SELECT filename, file_size_kb FROM photos WHERE post_id = ?", (p_dict["id"],)).fetchall()
        p_dict["photos"] = [dict(ph) for ph in photo_rows]
        posts.append(p_dict)
    conn.close()
    return {"status": "success", "count": len(posts), "posts": posts}

@app.get("/api/v1/certificate")
async def get_certificate_api():
    cert = get_active_certificate()
    if SECURE_MODE and cert:
        cert.pop("flag", None)
        cert.pop("private_key_pem", None)
    return {"status": "success", "secure_mode": SECURE_MODE, "certificate": cert}

@app.get("/api/v1/mode")
async def get_mode():
    return {"difficulty": DIFFICULTY_LEVEL, "environment_purpose": ENVIRONMENT_PURPOSE, "secure_mode": SECURE_MODE}

@app.post("/api/v1/configure")
async def configure(difficulty: Optional[str] = Query(None), environment_purpose: Optional[str] = Query(None)):
    global DIFFICULTY_LEVEL, SECURE_MODE, ENVIRONMENT_PURPOSE
    if difficulty:
        DIFFICULTY_LEVEL = difficulty.lower()
        SECURE_MODE = (DIFFICULTY_LEVEL == "secure")
    if environment_purpose:
        ENVIRONMENT_PURPOSE = environment_purpose.lower()
    return {"status": "success", "difficulty": DIFFICULTY_LEVEL, "environment_purpose": ENVIRONMENT_PURPOSE, "secure_mode": SECURE_MODE}
