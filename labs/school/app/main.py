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

app = FastAPI(title="University Student Portal Microservice Cyber Range", version="1.1.0")

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def get_current_student(request: Request) -> Optional[dict]:
    session_student = request.cookies.get("session_student")
    if not session_student:
        return None
    conn = database.get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (session_student,)).fetchone()
    conn.close()
    return dict(student) if student else None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, student_id: Optional[str] = None):
    current_student = get_current_student(request)
    target_id = student_id or (current_student["student_id"] if current_student else "STD-1001")

    if SECURE_MODE and current_student:
        # Secure mode restricts transcript viewing strictly to authenticated student
        target_id = current_student["student_id"]

    conn = database.get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (target_id,)).fetchone()

    courses = []
    if student:
        course_rows = conn.execute("SELECT * FROM courses WHERE student_id = ?", (target_id,)).fetchall()
        courses = [dict(c) for c in course_rows]

    all_students = [dict(s) for s in conn.execute("SELECT student_id, full_name, program FROM students").fetchall()]
    conn.close()

    error = request.query_params.get("error")
    message = request.query_params.get("message")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_student": current_student,
            "student": dict(student) if student else None,
            "courses": courses,
            "all_students": all_students,
            "difficulty": DIFFICULTY_LEVEL,
            "secure_mode": SECURE_MODE,
            "error": error,
            "message": message
        }
    )

@app.post("/login")
async def login(student_id: str = Form(...), pin: str = Form(...)):
    conn = database.get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ? AND pin = ?", (student_id, pin)).fetchone()
    conn.close()

    if not student:
        return RedirectResponse(url="/?error=Invalid+Student+ID+or+PIN", status_code=status.HTTP_303_SEE_OTHER)

    logger.info(f"Student logged in: {student['full_name']} ({student['student_id']})")
    response = RedirectResponse(url=f"/?student_id={student['student_id']}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="session_student", value=student["student_id"])
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_student")
    return response

@app.post("/register")
async def register_student(
    student_id: str = Form(...),
    pin: str = Form("1234"),
    full_name: str = Form(...),
    program: str = Form("BSc Information Technology"),
    gpa: float = Form(3.5)
):
    conn = database.get_db_connection()
    count = conn.execute("SELECT COUNT(*) as count FROM students").fetchone()["count"]

    if count >= 3:
        conn.close()
        return RedirectResponse(url="/?error=Registration+Closed:+Maximum+3+students+allowed+on+portal", status_code=status.HTTP_303_SEE_OTHER)

    existing = conn.execute("SELECT id FROM students WHERE student_id = ?", (student_id,)).fetchone()
    if existing:
        conn.close()
        return RedirectResponse(url="/?error=Student+ID+already+exists", status_code=status.HTTP_303_SEE_OTHER)

    conn.execute(
        "INSERT INTO students (student_id, pin, full_name, program, gpa) VALUES (?, ?, ?, ?, ?)",
        (student_id, pin, full_name, program, gpa)
    )

    # Seed 4 default courses
    default_courses = [
        (student_id, "CS101", "Introduction to Computing", 3, "A"),
        (student_id, "NET201", "Data Communications", 3, "A"),
        (student_id, "SEC301", "Systems Security", 3, "A-"),
        (student_id, "MAT102", "Discrete Mathematics", 3, "B+")
    ]
    conn.executemany("INSERT INTO courses (student_id, course_code, course_name, credits, grade) VALUES (?, ?, ?, ?, ?)", default_courses)

    conn.commit()
    conn.close()

    logger.info(f"Registered new student: {full_name} ({student_id})")
    return RedirectResponse(url=f"/?student_id={student_id}&message=Student+registered+successfully", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/update-records")
async def update_records(
    request: Request,
    target_student_id: str = Form(...),
    gpa: float = Form(...),
    course_code: str = Form(...),
    new_grade: str = Form(...)
):
    current_student = get_current_student(request)
    if SECURE_MODE:
        if not current_student or current_student["student_id"] != target_student_id:
            return RedirectResponse(url="/?error=Unauthorized:+You+cannot+modify+other+student+records", status_code=status.HTTP_303_SEE_OTHER)

    conn = database.get_db_connection()
    conn.execute("UPDATE students SET gpa = ? WHERE student_id = ?", (gpa, target_student_id))
    conn.execute("UPDATE courses SET grade = ? WHERE student_id = ? AND course_code = ?", (new_grade, target_student_id, course_code))
    conn.commit()
    conn.close()

    logger.info(f"Academic records modified for {target_student_id}: GPA={gpa}, {course_code}={new_grade}")
    return RedirectResponse(url=f"/?student_id={target_student_id}&message=Academic+records+updated+successfully", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/api/v1/students/{student_id}")
async def get_student_api(student_id: str):
    conn = database.get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()

    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="Student record not found")

    course_rows = conn.execute("SELECT * FROM courses WHERE student_id = ?", (student_id,)).fetchall()
    conn.close()

    student_dict = dict(student)
    student_dict["courses"] = [dict(c) for c in course_rows]

    if SECURE_MODE:
        student_dict.pop("flag", None)
        student_dict.pop("pin", None)

    return student_dict

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename
    if SECURE_MODE:
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
