# 🏦 Online Banking Microservice Cyber Range Lab

Simulates an enterprise online banking portal with customer login, wire transfers, and transaction history search.

## Vulnerabilities & Objectives
- **Intermediate / Advanced**: SQL Injection in login (`username`) and transaction search parameter (`q`).
- **Expert**: Reflected XSS in search query output (`search_query|safe`).
- **Secure**: Parameterized SQL queries and HTML sanitization.

## Flag
- Target Admin Flag: `FLAG{BANK_SQLI_XSS_IDOR_COMPROMISE_2026}`
