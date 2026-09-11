# 🛒 E-Commerce Platform Cyber Range Lab

Simulates an e-commerce shopping platform with catalog browsing, coupon applications, and order receipts.

## Vulnerabilities & Objectives
- **Beginner / Intermediate**: Client-Side Price Tampering (submitting custom `price` form parameter) and Reusable Coupon Logic Flaw.
- **Advanced / Expert**: Order Lookup IDOR to inspect admin order `ORD-9000`.
- **Secure**: Server-side price validation, one-time coupon usage tracking, and authorization checks.

## Flag
- Target Admin Flag: `FLAG{SHOP_COUPON_REUSE_PRICING_FLAW_2026}`
