import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import database

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("school_service")

DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="University Student Portal Microservice Cyber Range", version="1.0.0")

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, student_id: str = "STD-1001"):
    conn = database.get_db_connection()
    if SECURE_MODE:
        # Secure: restrict to STD-1001 unless authenticated
        student_id = "STD-1001"

    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()

    if not student:
        student = {"student_id": "N/A", "full_name": "Unknown Student", "program": "N/A", "gpa": 0.0, "flag": None}

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"student": dict(student), "difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE, "message": request.query_params.get("message")}
    )

@app.get("/api/v1/students/{student_id}")
async def get_student_api(student_id: str):
    conn = database.get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    student_dict = dict(student)
    if SECURE_MODE:
        student_dict.pop("flag", None)
    return student_dict

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename
    if SECURE_MODE:
        # Extension validation
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".pdf", ".docx", ".png", ".jpg"]:
            return RedirectResponse(url="/?message=Error:+Invalid+file+type", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return RedirectResponse(url=f"/?message=File+uploaded+successfully:+{filename}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/api/v1/mode")
async def get_mode():
    return {"difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE}

@app.post("/api/v1/configure")
async def configure(difficulty: Optional[str] = Query(None)):
    global DIFFICULTY_LEVEL, SECURE_MODE
    if difficulty:
        DIFFICULTY_LEVEL = difficulty.lower()
        SECURE_MODE = (DIFFICULTY_LEVEL == "secure")
    return {"status": "success", "difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE}
