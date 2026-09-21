import os
import sys
import hmac
import hashlib
import json
import logging
import sqlite3
import urllib.request
import urllib.error
import time
from typing import Optional, Dict, Any, List
import jwt
from fastapi import FastAPI, Request, Form, HTTPException, status, Header, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import database

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger("api_warehouse")

database.init_db()

app = FastAPI(
    title="Dadiwoo API Warehouse Microservice",
    description="Full-spectrum API Security & Hacking lab covering REST, GraphQL, JWT, HMAC, Postman testing, and Secure Mode verification.",
    version="1.0.0"
)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Global State
DIFFICULTY_LEVEL = os.environ.get("DIFFICULTY_LEVEL", "beginner").lower()
ENVIRONMENT_PURPOSE = os.environ.get("ENVIRONMENT_PURPOSE", "cybersecurity").lower()
JWT_SECRET = "secret123"
SECURE_JWT_SECRET = "Strong_Production_Secret_Key_998877!"

# Simple in-memory rate limiting tracker: {ip: [timestamps]}
RATE_LIMIT_STORE: Dict[str, List[float]] = {}

class ConfigurePayload(BaseModel):
    difficulty: str
    environment_purpose: str = "cybersecurity"

class ItemCreatePayload(BaseModel):
    item_code: str
    name: str
    category: str
    quantity: int = 10
    price: float = 100.0
    is_restricted: int = 0
    owner_user_id: int = 1

class WebhookPayload(BaseModel):
    target_url: str
    event_type: str = "stock_update"

class TokenRequestPayload(BaseModel):
    username: str
    algorithm: str = "HS256"

class GraphQLRequestPayload(BaseModel):
    query: str
    variables: Optional[Dict[str, Any]] = None

def log_audit(endpoint: str, method: str, status_code: int, client_ip: str, auth_method: str):
    try:
        conn = database.get_db_connection()
        conn.execute("""
            INSERT INTO audit_logs (endpoint, method, status_code, client_ip, auth_method)
            VALUES (?, ?, ?, ?, ?)
        """, (endpoint, method, status_code, client_ip, auth_method))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to log audit: {e}")

def get_user_by_api_key(api_key: str):
    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE api_key = ?", (api_key,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_username(username: str):
    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(user) if user else None

def authenticate_request(request: Request, api_key: Optional[str] = None, authorization: Optional[str] = None):
    """
    Authenticates requests using API Key (query/header) or Bearer JWT Token.
    Returns (user_dict, auth_method_string).
    """
    global DIFFICULTY_LEVEL
    mode = DIFFICULTY_LEVEL.lower()

    # Query param API key (disallowed in secure mode)
    qp_key = request.query_params.get("api_key") or api_key
    hdr_key = request.headers.get("X-API-Key")

    chosen_api_key = hdr_key or (qp_key if mode != "secure" else None)
    if chosen_api_key:
        user = get_user_by_api_key(chosen_api_key)
        if user:
            return user, "api_key"

    # Bearer Token Auth
    auth_hdr = authorization or request.headers.get("Authorization")
    if auth_hdr and auth_hdr.startswith("Bearer "):
        token = auth_hdr.split(" ")[1].strip()
        try:
            if mode == "secure":
                # Strict verification in secure mode
                payload = jwt.decode(token, SECURE_JWT_SECRET, algorithms=["HS256"])
                username = payload.get("sub") or payload.get("username")
                user = get_user_by_username(username)
                if user:
                    user["role"] = payload.get("role", user["role"])
                    return user, "bearer_jwt_secure"
            else:
                # In non-secure modes, support 'none' algorithm and weak secret decoding
                header = jwt.get_unverified_header(token)
                alg = header.get("alg", "HS256")
                if alg.lower() == "none":
                    payload = jwt.decode(token, options={"verify_signature": False})
                else:
                    try:
                        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                    except jwt.InvalidSignatureError:
                        payload = jwt.decode(token, options={"verify_signature": False})

                username = payload.get("sub") or payload.get("username", "guest_user")
                user = get_user_by_username(username) or {
                    "id": payload.get("user_id", 1),
                    "username": username,
                    "role": payload.get("role", "guest"),
                    "api_key": "jwt_token_user",
                    "secret_key": JWT_SECRET,
                    "email": f"{username}@warehouse.lab"
                }
                user["role"] = payload.get("role", user.get("role", "guest"))
                return user, f"bearer_jwt_{alg}"
        except Exception as e:
            logger.warning(f"JWT decode error: {e}")

    return None, "anonymous"

def check_rate_limit(client_ip: str, limit: int = 10, window_sec: int = 60):
    now = time.time()
    timestamps = RATE_LIMIT_STORE.get(client_ip, [])
    timestamps = [ts for ts in timestamps if now - ts < window_sec]
    RATE_LIMIT_STORE[client_ip] = timestamps
    if len(timestamps) >= limit:
        return False
    RATE_LIMIT_STORE[client_ip].append(now)
    return True

@app.get("/api/v1/configure")
async def get_config():
    return {
        "status": "success",
        "difficulty_level": DIFFICULTY_LEVEL,
        "environment_purpose": ENVIRONMENT_PURPOSE
    }

@app.post("/api/v1/configure")
async def set_config(payload: Optional[ConfigurePayload] = None, difficulty: Optional[str] = Query(None), environment_purpose: Optional[str] = Query(None)):
    global DIFFICULTY_LEVEL, ENVIRONMENT_PURPOSE
    if payload:
        diff = payload.difficulty
        purp = payload.environment_purpose
    else:
        diff = difficulty or "beginner"
        purp = environment_purpose or "cybersecurity"

    allowed_levels = ["beginner", "intermediate", "advanced", "expert", "secure"]
    if diff.lower() not in allowed_levels:
        raise HTTPException(status_code=400, detail=f"Invalid difficulty level. Allowed: {allowed_levels}")

    DIFFICULTY_LEVEL = diff.lower()
    ENVIRONMENT_PURPOSE = purp.lower()
    logger.info(f"API Warehouse configured: level={DIFFICULTY_LEVEL}, purpose={ENVIRONMENT_PURPOSE}")
    return {
        "status": "success",
        "message": f"API Warehouse updated to level '{DIFFICULTY_LEVEL}' in purpose '{ENVIRONMENT_PURPOSE}'"
    }

@app.get("/", response_class=HTMLResponse)
async def home_dashboard(request: Request):
    if ENVIRONMENT_PURPOSE == "networking":
        return HTMLResponse(
            content="<h1>API Warehouse Node - Networking Mode</h1><p>HTTP 503 Service Unavailable for Cybersecurity Target operations.</p>",
            status_code=503
        )

    conn = database.get_db_connection()
    users = [dict(u) for u in conn.execute("SELECT id, username, role, api_key, email FROM users").fetchall()]
    inventory = [dict(i) for i in conn.execute("SELECT * FROM inventory ORDER BY id ASC").fetchall()]
    recent_logs = [dict(l) for l in conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 15").fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "difficulty": DIFFICULTY_LEVEL,
            "environment_purpose": ENVIRONMENT_PURPOSE,
            "users": users,
            "inventory": inventory,
            "recent_logs": recent_logs,
            "jwt_secret": JWT_SECRET if DIFFICULTY_LEVEL != "secure" else "HIDDEN",
            "host": request.headers.get("host", "localhost:8089")
        }
    )

@app.get("/api/v1/debug/keys")
async def debug_keys_leak():
    if DIFFICULTY_LEVEL == "secure":
        raise HTTPException(status_code=403, detail="Debug key leak endpoint disabled in Secure Mode.")
    conn = database.get_db_connection()
    users = [dict(u) for u in conn.execute("SELECT id, username, role, api_key, email FROM users").fetchall()]
    conn.close()
    return {
        "status": "success",
        "warning": "API Debug Endpoint: Publicly exposed keys active!",
        "keys": users
    }

@app.get("/api/v1/postman-collection")
async def get_postman_collection(request: Request):
    base_url = f"http://{request.headers.get('host', 'localhost:8089')}"
    collection = {
        "info": {
            "name": "Dadiwoo API Warehouse Hacking Collection",
            "description": "Comprehensive Postman collection for testing API keys, Bearer JWT tokens, BOLA/IDOR, Mass Assignment, GraphQL, HMAC, Webhook SSRF, and Secure API verification.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "1. Authentication & Tokens",
                "item": [
                    {
                        "name": "Get Bearer JWT Token (Standard)",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({"username": "guest_user", "algorithm": "HS256"})
                            },
                            "url": {"raw": f"{base_url}/api/v1/auth/token"}
                        }
                    },
                    {
                        "name": "Get Bearer JWT Token (JWT 'none' Flaw)",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({"username": "admin_boss", "algorithm": "none"})
                            },
                            "url": {"raw": f"{base_url}/api/v1/auth/token"}
                        }
                    }
                ]
            },
            {
                "name": "2. Inventory & IDOR / BOLA",
                "item": [
                    {
                        "name": "List Inventory Items",
                        "request": {
                            "method": "GET",
                            "header": [{"key": "X-API-Key", "value": "ak_guest_88291029"}],
                            "url": {"raw": f"{base_url}/api/v1/inventory"}
                        }
                    },
                    {
                        "name": "Get Inventory Item by ID (IDOR)",
                        "request": {
                            "method": "GET",
                            "header": [{"key": "X-API-Key", "value": "ak_guest_88291029"}],
                            "url": {"raw": f"{base_url}/api/v1/inventory/3"}
                        }
                    },
                    {
                        "name": "Create Inventory Item (Mass Assignment)",
                        "request": {
                            "method": "POST",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "X-API-Key", "value": "ak_guest_88291029"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "item_code": "SKU-HACK-99",
                                    "name": "Unauthorized Gold Shipment",
                                    "category": "Precious Materials",
                                    "quantity": 1000,
                                    "price": 0.0,
                                    "is_restricted": 0,
                                    "owner_user_id": 1
                                })
                            },
                            "url": {"raw": f"{base_url}/api/v1/inventory"}
                        }
                    }
                ]
            },
            {
                "name": "3. GraphQL API Testing",
                "item": [
                    {
                        "name": "GraphQL Introspection Query",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({"query": "{ __schema { types { name } } }"})
                            },
                            "url": {"raw": f"{base_url}/api/v1/graphql"}
                        }
                    },
                    {
                        "name": "GraphQL Fetch All Users & Secrets",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({"query": "{ users { id username role apiKey secretKey email } }"})
                            },
                            "url": {"raw": f"{base_url}/api/v1/graphql"}
                        }
                    }
                ]
            },
            {
                "name": "4. Webhooks & SSRF / HMAC",
                "item": [
                    {
                        "name": "Register Webhook (SSRF Probe)",
                        "request": {
                            "method": "POST",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "X-API-Key", "value": "ak_guest_88291029"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "target_url": "http://127.0.0.1:9000/api/v1/services",
                                    "event_type": "ssrf_test"
                                })
                            },
                            "url": {"raw": f"{base_url}/api/v1/webhooks"}
                        }
                    },
                    {
                        "name": "Verify Order HMAC Signature",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "order_id": 1001,
                                    "amount": 12500.0,
                                    "signature": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
                                })
                            },
                            "url": {"raw": f"{base_url}/api/v1/orders/verify-hmac"}
                        }
                    }
                ]
            },
            {
                "name": "5. Admin & Security Auditing",
                "item": [
                    {
                        "name": "Export Full Warehouse Database",
                        "request": {
                            "method": "GET",
                            "header": [{"key": "X-API-Key", "value": "ak_auditor_31415926"}],
                            "url": {"raw": f"{base_url}/api/v1/admin/export"}
                        }
                    }
                ]
            }
        ]
    }
    return JSONResponse(content=collection, headers={"Content-Disposition": "attachment; filename=api_warehouse_postman_collection.json"})

@app.post("/api/v1/auth/token")
async def generate_token(payload: TokenRequestPayload):
    user = get_user_by_username(payload.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    secret = JWT_SECRET if DIFFICULTY_LEVEL != "secure" else SECURE_JWT_SECRET
    alg = payload.algorithm.upper()

    claims = {
        "sub": user["username"],
        "user_id": user["id"],
        "role": user["role"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }

    if DIFFICULTY_LEVEL != "secure" and alg == "NONE":
        # Unsigned JWT token for hacking exercise
        header_b64 = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0"
        claims_b64 = jwt.utils.base64url_encode(json.dumps(claims).encode('utf-8')).decode('utf-8')
        token_str = f"{header_b64}.{claims_b64}."
    else:
        token_str = jwt.encode(claims, secret, algorithm="HS256")

    return {
        "status": "success",
        "token_type": "Bearer",
        "algorithm": alg if DIFFICULTY_LEVEL != "secure" else "HS256",
        "access_token": token_str,
        "claims": claims
    }

@app.get("/api/v1/inventory")
async def list_inventory(
    request: Request,
    api_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    user, auth_method = authenticate_request(request, api_key, authorization)
    client_ip = request.client.host if request.client else "127.0.0.1"

    if DIFFICULTY_LEVEL == "secure":
        # Rate limit check
        if not check_rate_limit(client_ip, limit=20, window_sec=60):
            log_audit("/api/v1/inventory", "GET", 429, client_ip, auth_method)
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

        if not user:
            log_audit("/api/v1/inventory", "GET", 401, client_ip, auth_method)
            raise HTTPException(status_code=401, detail="Authentication required. Provide valid X-API-Key header or Bearer token.")

    conn = database.get_db_connection()
    if user and user.get("role") in ["warehouse_admin", "security_auditor"]:
        items = [dict(i) for i in conn.execute("SELECT * FROM inventory ORDER BY id ASC").fetchall()]
    elif DIFFICULTY_LEVEL in ["beginner", "intermediate", "advanced", "expert"] and not user:
        # In beginner mode, unauthenticated users get non-restricted items
        items = [dict(i) for i in conn.execute("SELECT * FROM inventory WHERE is_restricted = 0 ORDER BY id ASC").fetchall()]
    else:
        items = [dict(i) for i in conn.execute("SELECT * FROM inventory WHERE is_restricted = 0 ORDER BY id ASC").fetchall()]
    conn.close()

    log_audit("/api/v1/inventory", "GET", 200, client_ip, auth_method)
    return {
        "status": "success",
        "count": len(items),
        "auth_user": user["username"] if user else "anonymous",
        "auth_role": user["role"] if user else "guest",
        "inventory": items
    }

@app.get("/api/v1/inventory/{item_id}")
async def get_inventory_item(
    item_id: int,
    request: Request,
    api_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    user, auth_method = authenticate_request(request, api_key, authorization)
    client_ip = request.client.host if request.client else "127.0.0.1"

    conn = database.get_db_connection()
    item = conn.execute("SELECT * FROM inventory WHERE id = ?", (item_id,)).fetchone()
    conn.close()

    if not item:
        log_audit(f"/api/v1/inventory/{item_id}", "GET", 404, client_ip, auth_method)
        raise HTTPException(status_code=404, detail="Item not found")

    item_dict = dict(item)

    if DIFFICULTY_LEVEL == "secure":
        if not user:
            log_audit(f"/api/v1/inventory/{item_id}", "GET", 401, client_ip, auth_method)
            raise HTTPException(status_code=401, detail="Authentication required.")
        if item_dict["is_restricted"] and user["role"] not in ["warehouse_admin", "security_auditor"]:
            log_audit(f"/api/v1/inventory/{item_id}", "GET", 403, client_ip, auth_method)
            raise HTTPException(status_code=403, detail="Access denied. Restricted warehouse item.")

    log_audit(f"/api/v1/inventory/{item_id}", "GET", 200, client_ip, auth_method)
    return {
        "status": "success",
        "item": item_dict
    }

@app.post("/api/v1/inventory", status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    payload: ItemCreatePayload,
    request: Request,
    api_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    user, auth_method = authenticate_request(request, api_key, authorization)
    client_ip = request.client.host if request.client else "127.0.0.1"

    if DIFFICULTY_LEVEL == "secure":
        if not user or user["role"] not in ["warehouse_admin", "security_auditor"]:
            log_audit("/api/v1/inventory", "POST", 403, client_ip, auth_method)
            raise HTTPException(status_code=403, detail="Forbidden. Only warehouse admins can create inventory.")
        # Prevent Mass Assignment in secure mode
        owner_id = user["id"]
        is_restr = 0
    else:
        # Mass Assignment flaw active in non-secure mode!
        owner_id = payload.owner_user_id
        is_restr = payload.is_restricted

    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inventory (item_code, name, category, quantity, price, is_restricted, owner_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (payload.item_code, payload.name, payload.category, payload.quantity, payload.price, is_restr, owner_id))
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Item code already exists.")

    log_audit("/api/v1/inventory", "POST", 201, client_ip, auth_method)
    return {
        "status": "success",
        "message": "Inventory item created successfully",
        "item_id": item_id,
        "item": {
            "id": item_id,
            "item_code": payload.item_code,
            "name": payload.name,
            "category": payload.category,
            "quantity": payload.quantity,
            "price": payload.price,
            "is_restricted": is_restr,
            "owner_user_id": owner_id
        }
    }

@app.get("/api/v1/webhooks")
async def list_webhooks():
    conn = database.get_db_connection()
    webhooks = [dict(w) for w in conn.execute("SELECT * FROM webhooks").fetchall()]
    conn.close()
    return {"status": "success", "webhooks": webhooks}

@app.post("/api/v1/webhooks")
async def register_and_trigger_webhook(
    payload: WebhookPayload,
    request: Request,
    api_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    user, auth_method = authenticate_request(request, api_key, authorization)
    client_ip = request.client.host if request.client else "127.0.0.1"

    target_url = payload.target_url

    if DIFFICULTY_LEVEL == "secure":
        # Strict URL Whitelisting to prevent SSRF
        if not (target_url.startswith("https://") or target_url.startswith("http://webhook.warehouse.lab")):
            log_audit("/api/v1/webhooks", "POST", 400, client_ip, auth_method)
            raise HTTPException(status_code=400, detail="Forbidden target_url domain. Only whitelisted webhook domains allowed in Secure Mode.")

    # Save to database
    conn = database.get_db_connection()
    user_id = user["id"] if user else 1
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO webhooks (user_id, target_url, event_type, secret_token)
        VALUES (?, ?, ?, ?)
    """, (user_id, target_url, payload.event_type, "whsec_token_9988"))
    conn.commit()
    conn.close()

    # Trigger webhook request (SSRF opportunity in non-secure mode)
    ssrf_response = None
    try:
        req = urllib.request.Request(target_url, headers={"User-Agent": "Warehouse-Webhook-Poller/1.0"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            ssrf_response = {
                "status_code": resp.status,
                "body": resp.read().decode("utf-8", errors="ignore")[:500]
            }
    except Exception as e:
        ssrf_response = {"error": str(e)}

    log_audit("/api/v1/webhooks", "POST", 200, client_ip, auth_method)
    return {
        "status": "success",
        "message": "Webhook registered and triggered successfully",
        "target_url": target_url,
        "webhook_dispatch_result": ssrf_response
    }

@app.post("/api/v1/orders/verify-hmac")
async def verify_hmac_signature(
    request: Request,
    payload: Dict[str, Any]
):
    order_id = payload.get("order_id")
    amount = payload.get("amount")
    provided_sig = payload.get("signature", "")

    msg = f"{order_id}:{amount}".encode('utf-8')
    expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), msg, hashlib.sha256).hexdigest()

    if DIFFICULTY_LEVEL == "secure":
        valid = hmac.compare_digest(provided_sig, expected_sig)
    else:
        # In non-secure modes, accepts signature or missing signature if debug header set
        valid = (provided_sig == expected_sig or provided_sig == "bypass_hmac")

    return {
        "status": "success" if valid else "invalid_signature",
        "valid": valid,
        "expected_signature": expected_sig if DIFFICULTY_LEVEL != "secure" else "HIDDEN",
        "order_id": order_id,
        "amount": amount
    }

@app.get("/api/v1/admin/export")
async def export_admin_database(
    request: Request,
    api_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    user, auth_method = authenticate_request(request, api_key, authorization)
    client_ip = request.client.host if request.client else "127.0.0.1"

    if DIFFICULTY_LEVEL == "secure":
        if not user or user["role"] not in ["warehouse_admin", "security_auditor"]:
            log_audit("/api/v1/admin/export", "GET", 403, client_ip, auth_method)
            raise HTTPException(status_code=403, detail="Forbidden. Admin or Security Auditor credentials required.")

    conn = database.get_db_connection()
    users = [dict(u) for u in conn.execute("SELECT * FROM users").fetchall()]
    inventory = [dict(i) for i in conn.execute("SELECT * FROM inventory").fetchall()]
    webhooks = [dict(w) for w in conn.execute("SELECT * FROM webhooks").fetchall()]
    conn.close()

    log_audit("/api/v1/admin/export", "GET", 200, client_ip, auth_method)
    return {
        "status": "success",
        "system": "API Warehouse Master Export",
        "users": users,
        "inventory": inventory,
        "webhooks": webhooks
    }

@app.post("/api/v1/graphql")
@app.post("/graphql")
async def graphql_handler(payload: GraphQLRequestPayload, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    q = payload.query or ""

    if DIFFICULTY_LEVEL == "secure" and ("__schema" in q or "__type" in q):
        log_audit("/graphql", "POST", 400, client_ip, "graphql")
        return JSONResponse(
            status_code=400,
            content={"errors": [{"message": "GraphQL Introspection is disabled in Secure Mode."}]}
        )

    conn = database.get_db_connection()
    data = {}

    if "__schema" in q or "__type" in q:
        data["__schema"] = {
            "types": [
                {"name": "InventoryItem", "fields": ["id", "item_code", "name", "category", "quantity", "price", "is_restricted"]},
                {"name": "User", "fields": ["id", "username", "role", "apiKey", "secretKey", "email"]},
                {"name": "SystemConfig", "fields": ["difficulty", "jwtSecret", "adminExportUrl"]}
            ]
        }

    if "users" in q:
        users = [
            {
                "id": u["id"],
                "username": u["username"],
                "role": u["role"],
                "apiKey": u["api_key"],
                "secretKey": u["secret_key"] if DIFFICULTY_LEVEL != "secure" else "[PROTECTED]",
                "email": u["email"]
            }
            for u in conn.execute("SELECT * FROM users").fetchall()
        ]
        data["users"] = users

    if "inventory" in q or "items" in q:
        items = [dict(i) for i in conn.execute("SELECT * FROM inventory").fetchall()]
        data["inventory"] = items

    if "systemConfig" in q:
        data["systemConfig"] = {
            "difficulty": DIFFICULTY_LEVEL,
            "jwtSecret": JWT_SECRET if DIFFICULTY_LEVEL != "secure" else "[PROTECTED]",
            "adminExportUrl": "/api/v1/admin/export"
        }

    conn.close()
    log_audit("/graphql", "POST", 200, client_ip, "graphql")
    return {"data": data}
