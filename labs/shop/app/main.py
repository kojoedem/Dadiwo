import os
import logging
import uuid
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database

logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "message": "%(message)s"}')
logger = logging.getLogger("shop_service")

DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "intermediate").lower()
SECURE_MODE = (os.environ.get("SECURE_MODE", "false").lower() in ("true", "1", "t", "yes") or DIFFICULTY_LEVEL == "secure")

app = FastAPI(title="E-Commerce Store Microservice Cyber Range", version="1.0.0")

database.init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = database.get_db_connection()
    products = [dict(r) for r in conn.execute("SELECT * FROM products").fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"products": products, "order": None, "difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE, "message": request.query_params.get("message")}
    )

@app.post("/checkout")
async def checkout(product_id: int = Form(...), price: float = Form(...), coupon: str = Form("")):
    conn = database.get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return RedirectResponse(url="/?message=Product+not+found", status_code=status.HTTP_303_SEE_OTHER)

    actual_price = product["price"] if SECURE_MODE else price  # Vulnerable to client-side price tampering in non-secure mode

    discount = 0.0
    if coupon:
        c_row = conn.execute("SELECT * FROM coupons WHERE code = ?", (coupon,)).fetchone()
        if c_row:
            if SECURE_MODE and c_row["is_used"]:
                conn.close()
                return RedirectResponse(url="/?message=Coupon+already+used", status_code=status.HTTP_303_SEE_OTHER)

            discount = c_row["discount_percent"]
            if SECURE_MODE:
                conn.execute("UPDATE coupons SET is_used = 1 WHERE code = ?", (coupon,))

    final_price = max(0.0, actual_price * (1 - discount / 100.0))
    order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"

    conn.execute(
        "INSERT INTO orders (order_id, customer_name, total_price, items) VALUES (?, ?, ?, ?)",
        (order_id, "Guest Customer", final_price, product["name"])
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/?message=Order+placed:+{order_id}+Total:+${final_price:.2f}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/order", response_class=HTMLResponse)
async def view_order(request: Request, order_id: str):
    conn = database.get_db_connection()
    order_row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    products = [dict(r) for r in conn.execute("SELECT * FROM products").fetchall()]
    conn.close()

    order_dict = None
    if order_row:
        order_dict = dict(order_row)
        # Rename 'items' key to 'item_names' so Jinja2 dot notation doesn't call dict.items() method
        order_dict["item_names"] = order_dict.get("items", "")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"products": products, "order": order_dict, "difficulty": DIFFICULTY_LEVEL, "secure_mode": SECURE_MODE}
    )

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
