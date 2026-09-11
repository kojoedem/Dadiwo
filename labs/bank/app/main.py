import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("bank_service")

DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "intermediate").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

app = FastAPI(title="Online Banking Microservice Cyber Range", version="1.0.0")

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def get_current_user(request: Request) -> Optional[dict]:
    session_user = request.cookies.get("session_user")
    if not session_user:
        return None
    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session_user,)).fetchone()
    conn.close()
    return dict(user) if user else None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, q: Optional[str] = None):
    user = get_current_user(request)
    transactions = []

    if user:
        conn = database.get_db_connection()
        if q and not SECURE_MODE and DIFFICULTY_LEVEL != "beginner":
            # Intentional SQLi vulnerability in search parameter for intermediate/advanced/expert modes
            query = f"SELECT * FROM wire_transfers WHERE (sender_account = '{user['account_number']}' OR recipient_account = '{user['account_number']}') AND memo LIKE '%{q}%'"
            try:
                tx_rows = conn.execute(query).fetchall()
                transactions = [dict(tx) for tx in tx_rows]
            except Exception as e:
                logger.error(f"SQL error in search: {e}")
        else:
            tx_rows = conn.execute(
                "SELECT * FROM wire_transfers WHERE sender_account = ? OR recipient_account = ?",
                (user["account_number"], user["account_number"])
            ).fetchall()
            transactions = [dict(tx) for tx in tx_rows]
        conn.close()

    error = request.query_params.get("error")
    message = request.query_params.get("message")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_user": user,
            "transactions": transactions,
            "search_query": q,
            "difficulty": DIFFICULTY_LEVEL,
            "secure_mode": SECURE_MODE,
            "error": error,
            "message": message
        }
    )

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    conn = database.get_db_connection()
    if not SECURE_MODE and DIFFICULTY_LEVEL in ["intermediate", "advanced"]:
        # SQL Injection in authentication
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        try:
            user = conn.execute(query).fetchone()
        except Exception:
            user = None
    else:
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()

    if not user:
        return RedirectResponse(url="/?error=Invalid+credentials", status_code=status.HTTP_303_SEE_OTHER)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="session_user", value=user["username"])
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_user")
    return response

@app.post("/transfer")
async def transfer(request: Request, recipient_account: str = Form(...), amount: float = Form(...), memo: str = Form("")):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/?error=Authentication+required", status_code=status.HTTP_303_SEE_OTHER)

    if SECURE_MODE and amount <= 0:
        return RedirectResponse(url="/?error=Amount+must+be+positive", status_code=status.HTTP_303_SEE_OTHER)

    conn = database.get_db_connection()
    sender_bal = user["balance"]
    if SECURE_MODE and sender_bal < amount:
        conn.close()
        return RedirectResponse(url="/?error=Insufficient+balance", status_code=status.HTTP_303_SEE_OTHER)

    conn.execute("UPDATE users SET balance = balance - ? WHERE account_number = ?", (amount, user["account_number"]))
    conn.execute("UPDATE users SET balance = balance + ? WHERE account_number = ?", (amount, recipient_account))
    conn.execute(
        "INSERT INTO wire_transfers (sender_account, recipient_account, amount, memo) VALUES (?, ?, ?, ?)",
        (user["account_number"], recipient_account, amount, memo)
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url="/?message=Wire+transfer+executed", status_code=status.HTTP_303_SEE_OTHER)

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
