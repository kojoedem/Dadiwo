# 🏬 Dadiwoo API Warehouse Lab

Part of the **🛡 Dadiwoo Cyber Range Microservices Platform**.

The **API Warehouse Lab** is an interactive, progressive API security testing environment designed to simulate real-world REST, GraphQL, JWT, HMAC, and Webhook API vulnerabilities ranging from beginner to expert side, along with secure mode compliance auditing.

---

## 🎯 Target Overview & Specifications

- **Default Port**: `8089`
- **Local Domain**: `apiwarehouse.lab`
- **Category**: `API / Cloud`
- **Search Tags**: `api`, `postman`, `jwt`, `bearer-token`, `api-key`, `rate-limit`, `idor`, `graphql`, `oauth`, `secure`

---

## 🚀 Key Features

1. **Multi-Form Authentication**: Supports API Key (`X-API-Key` or query string), Bearer JWT Token (`Authorization: Bearer <token>`), HMAC SHA256 signatures, and Security Auditor Diagnostic keys.
2. **Postman Collection JSON Export**: Click "📥 Download Postman Collection" on the console or query `/api/v1/postman-collection` to import pre-configured Postman requests directly into Postman!
3. **OpenAPI & Interactive Console**: Interactive Swagger UI at `/docs` and in-browser HTTP testing client.
4. **Progressive Difficulty Levels**:
   - `beginner`: API key leakage (`/api/v1/debug/keys`), query param API keys, simple IDOR.
   - `intermediate`: JWT algorithm `none` flaw, weak secret signing (`secret123`), BOLA/IDOR on inventory updates.
   - `advanced`: GraphQL introspection (`/api/v1/graphql`), Mass Assignment (`POST /api/v1/inventory`), rate limit header spoofing.
   - `expert`: Webhook SSRF (`POST /api/v1/webhooks`), HMAC signature bypass, Broken Function Level Authorization (`/api/v1/admin/export`).
   - `secure`: Strict JWT verification, RBAC, rate limiting, HMAC enforcement, webhook domain whitelisting, and auditor token verification (`ak_auditor_31415926`).
