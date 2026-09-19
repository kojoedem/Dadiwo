import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Response, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import database

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger("atm_service")

# SECURE_MODE & DIFFICULTY_LEVEL configuration
DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
ENVIRONMENT_PURPOSE = os.environ.get("ENVIRONMENT_PURPOSE", "cybersecurity").lower()
SECURE_MODE = (
    os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes")
    or DIFFICULTY_LEVEL == "secure"
)

app = FastAPI(
    title="ATM Microservice Cyber Range",
    description="Intentionally vulnerable ATM simulator API with multi-level difficulty profiles.",
    version="1.1.0"
)

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

class LoginRequest(BaseModel):
    card_number: str
    pin: str

def get_current_user_from_session(request: Request) -> Optional[dict]:
    session_account = request.cookies.get("session_account")
    if not session_account:
        return None
    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM accounts WHERE account_number = ?", (session_account,)).fetchone()
    conn.close()
    return dict(user) if user else None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user_from_session(request)
    transactions = []
    if user:
        conn = database.get_db_connection()
        tx_rows = conn.execute(
            "SELECT * FROM transactions WHERE account_number = ? ORDER BY timestamp DESC",
            (user["account_number"],)
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
            "secure_mode": SECURE_MODE,
            "difficulty": DIFFICULTY_LEVEL,
            "error": error,
            "message": message
        }
    )

@app.post("/register")
async def register_account(
    holder_name: str = Form(...),
    card_number: str = Form(...),
    pin: str = Form(...),
    initial_balance: float = Form(1000.0)
):
    conn = database.get_db_connection()
    existing = conn.execute("SELECT id FROM accounts WHERE card_number = ?", (card_number,)).fetchone()
    if existing:
        conn.close()
        return RedirectResponse(url="/?error=Card+number+already+exists", status_code=status.HTTP_303_SEE_OTHER)

    # Generate next account number ACC-1003+
    count = conn.execute("SELECT COUNT(*) as count FROM accounts").fetchone()["count"]
    account_number = f"ACC-{1000 + count + 1}"

    conn.execute(
        "INSERT INTO accounts (account_number, card_number, pin, holder_name, balance) VALUES (?, ?, ?, ?, ?)",
        (account_number, card_number, pin, holder_name, initial_balance)
    )
    conn.commit()
    conn.close()

    logger.info(f"Created new ATM account: {holder_name} ({account_number}, Card: {card_number})")
    return RedirectResponse(url=f"/?message=ATM+card+created:+{holder_name}+({account_number})", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/login")
async def web_login(card_number: str = Form(...), pin: str = Form(...)):
    conn = database.get_db_connection()
    user = conn.execute(
        "SELECT * FROM accounts WHERE card_number = ? AND pin = ?",
        (card_number, pin)
    ).fetchone()
    conn.close()

    if not user:
        logger.warning(f"Failed login attempt for card {card_number}")
        return RedirectResponse(url="/?error=Invalid+Card+Number+or+PIN", status_code=status.HTTP_303_SEE_OTHER)

    logger.info(f"Successful login for user {user['holder_name']} ({user['account_number']})")
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="session_account", value=user["account_number"])
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_account")
    return response

@app.get("/api/v1/mode")
async def get_lab_mode():
    return {
        "difficulty_level": DIFFICULTY_LEVEL,
        "secure_mode": SECURE_MODE,
        "lab_name": "ATM Microservice Range",
        "active_vulnerabilities": {
            "beginner": ["IDOR / BOLA on /api/v1/accounts/{account_number}"],
            "intermediate": ["IDOR / BOLA", "Business Logic negative withdrawal balance inflation"],
            "advanced": ["IDOR / BOLA", "Business Logic negative withdrawal", "Broken Admin Authentication on /api/v1/admin/stats"],
            "expert": ["Multi-stage chained attack (IDOR + Admin Auth Bypass + Transfer Logic Exploit)"],
            "secure": ["None - All controls hardened"]
        }.get(DIFFICULTY_LEVEL, [])
    }

@app.post("/api/v1/configure")
async def update_lab_config(
    difficulty: Optional[str] = Query(None),
    secure: Optional[bool] = Query(None),
    environment_purpose: Optional[str] = Query(None)
):
    global DIFFICULTY_LEVEL, SECURE_MODE, ENVIRONMENT_PURPOSE
    if difficulty:
        DIFFICULTY_LEVEL = difficulty.lower()
        SECURE_MODE = (DIFFICULTY_LEVEL == "secure")
    if environment_purpose:
        ENVIRONMENT_PURPOSE = environment_purpose.lower()
    if secure is not None:
        SECURE_MODE = secure
    logger.info(f"Microservice reconfigured: DIFFICULTY_LEVEL={DIFFICULTY_LEVEL}, SECURE_MODE={SECURE_MODE}, ENVIRONMENT_PURPOSE={ENVIRONMENT_PURPOSE}")
    return {
        "status": "success",
        "difficulty": DIFFICULTY_LEVEL,
        "difficulty_level": DIFFICULTY_LEVEL,
        "secure_mode": SECURE_MODE,
        "environment_purpose": ENVIRONMENT_PURPOSE
    }

@app.get("/api/v1/accounts/{account_number}")
async def get_account_api(account_number: str, request: Request):
    logger.info(f"API Access: Fetch account details for {account_number} (Difficulty: {DIFFICULTY_LEVEL})")

    if SECURE_MODE:
        user = get_current_user_from_session(request)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        if user["account_number"] != account_number and not user.get("is_admin"):
            raise HTTPException(status_code=403, detail="Forbidden: You cannot access other customer accounts.")

    conn = database.get_db_connection()
    user_row = conn.execute("SELECT * FROM accounts WHERE account_number = ?", (account_number,)).fetchone()
    conn.close()

    if not user_row:
        raise HTTPException(status_code=404, detail="Account not found")

    user_dict = dict(user_row)
    if SECURE_MODE:
        user_dict.pop("pin", None)
        user_dict.pop("flag", None)

    return user_dict

@app.post("/transaction")
async def process_transaction(
    request: Request,
    account_number: str = Form(...),
    action: str = Form(...),
    amount: float = Form(...)
):
    user = get_current_user_from_session(request)

    if SECURE_MODE or DIFFICULTY_LEVEL == "beginner":
        if amount <= 0:
            return RedirectResponse(url="/?error=Amount+must+be+greater+than+zero", status_code=status.HTTP_303_SEE_OTHER)

    if SECURE_MODE:
        if not user:
            return RedirectResponse(url="/?error=Authentication+required", status_code=status.HTTP_303_SEE_OTHER)
        if user["account_number"] != account_number:
            logger.warning(f"UNAUTHORIZED TRANSACTION ATTEMPT: {user['account_number']} tried to transact on {account_number}")
            return RedirectResponse(url="/?error=Unauthorized+transaction+target", status_code=status.HTTP_303_SEE_OTHER)

    conn = database.get_db_connection()
    target = conn.execute("SELECT balance FROM accounts WHERE account_number = ?", (account_number,)).fetchone()
    if not target:
        conn.close()
        return RedirectResponse(url="/?error=Account+not+found", status_code=status.HTTP_303_SEE_OTHER)

    current_balance = target["balance"]

    if action == "WITHDRAW":
        if SECURE_MODE and current_balance < amount:
            conn.close()
            return RedirectResponse(url="/?error=Insufficient+funds", status_code=status.HTTP_303_SEE_OTHER)
        new_balance = current_balance - amount
    elif action == "DEPOSIT":
        if amount <= 0:
            conn.close()
            return RedirectResponse(url="/?error=Invalid+deposit+amount", status_code=status.HTTP_303_SEE_OTHER)
        new_balance = current_balance + amount
    else:
        conn.close()
        return RedirectResponse(url="/?error=Invalid+action", status_code=status.HTTP_303_SEE_OTHER)

    conn.execute("UPDATE accounts SET balance = ? WHERE account_number = ?", (new_balance, account_number))
    conn.execute(
        "INSERT INTO transactions (account_number, transaction_type, amount) VALUES (?, ?, ?)",
        (account_number, action, amount)
    )
    conn.commit()
    conn.close()

    logger.info(f"Transaction completed for {account_number}: {action} ${amount}")
    return RedirectResponse(url=f"/?message=Transaction+{action}+of+${amount:.2f}+successful", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/transfer")
async def process_transfer(
    request: Request,
    from_account: str = Form(...),
    to_account: str = Form(...),
    amount: float = Form(...)
):
    user = get_current_user_from_session(request)

    if SECURE_MODE or DIFFICULTY_LEVEL in ["beginner", "intermediate"]:
        if amount <= 0:
            return RedirectResponse(url="/?error=Transfer+amount+must+be+positive", status_code=status.HTTP_303_SEE_OTHER)

    if SECURE_MODE:
        if not user:
            return RedirectResponse(url="/?error=Authentication+required", status_code=status.HTTP_303_SEE_OTHER)
        if user["account_number"] != from_account:
            return RedirectResponse(url="/?error=Unauthorized+transfer+sender", status_code=status.HTTP_303_SEE_OTHER)

    conn = database.get_db_connection()
    sender = conn.execute("SELECT balance FROM accounts WHERE account_number = ?", (from_account,)).fetchone()
    recipient = conn.execute("SELECT balance FROM accounts WHERE account_number = ?", (to_account,)).fetchone()

    if not sender or not recipient:
        conn.close()
        return RedirectResponse(url="/?error=Invalid+sender+or+recipient+account", status_code=status.HTTP_303_SEE_OTHER)

    if SECURE_MODE and sender["balance"] < amount:
        conn.close()
        return RedirectResponse(url="/?error=Insufficient+balance", status_code=status.HTTP_303_SEE_OTHER)

    new_sender_bal = sender["balance"] - amount
    new_recipient_bal = recipient["balance"] + amount

    conn.execute("UPDATE accounts SET balance = ? WHERE account_number = ?", (new_sender_bal, from_account))
    conn.execute("UPDATE accounts SET balance = ? WHERE account_number = ?", (new_recipient_bal, to_account))

    conn.execute(
        "INSERT INTO transactions (account_number, transaction_type, amount, recipient_account) VALUES (?, ?, ?, ?)",
        (from_account, "TRANSFER_OUT", amount, to_account)
    )
    conn.execute(
        "INSERT INTO transactions (account_number, transaction_type, amount, recipient_account) VALUES (?, ?, ?, ?)",
        (to_account, "TRANSFER_IN", amount, from_account)
    )

    conn.commit()
    conn.close()

    logger.info(f"Transfer executed: {from_account} -> {to_account} (${amount})")
    return RedirectResponse(url=f"/?message=Transferred+${amount:.2f}+to+{to_account}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/api/v1/admin/stats")
async def get_admin_stats(request: Request, key: Optional[str] = Query(None)):
    if SECURE_MODE or DIFFICULTY_LEVEL in ["beginner", "intermediate"]:
        user = get_current_user_from_session(request)
        if not user or not user.get("is_admin"):
            raise HTTPException(status_code=403, detail="Forbidden: Admin privileges required")

    conn = database.get_db_connection()
    total_accounts = conn.execute("SELECT COUNT(*) as count FROM accounts").fetchone()["count"]
    total_reserve = conn.execute("SELECT SUM(balance) as total FROM accounts").fetchone()["total"]
    admin_acc = conn.execute("SELECT account_number, holder_name, flag FROM accounts WHERE is_admin = 1").fetchone()
    conn.close()

    return {
        "status": "active",
        "difficulty": DIFFICULTY_LEVEL,
        "total_accounts": total_accounts,
        "total_reserve_usd": total_reserve,
        "master_admin": dict(admin_acc) if admin_acc else None,
    }
