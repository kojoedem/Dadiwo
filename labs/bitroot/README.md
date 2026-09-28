# ⚡ Bitroot Subdomain Reconnaissance & Security Lab (`bitroot.lab`)

The **Bitroot Recon Lab** is a microservice designed specifically for practicing DNS enumeration, subdomain discovery, HTTP/HTTPS probing, and Web Application Firewall (WAF) identification without generating network noise or slowing down real-world websites.

---

## 🎯 Target Overview

- **Root Domain**: `bitroot.lab`
- **Default Port**: `8091` (HTTPS with SSL/TLS certificate)
- **Total Subdomains**: 14
  - **Active Subdomains (10)**:
    1. `api.bitroot.lab` (REST API Gateway)
    2. `dev.bitroot.lab` (Developer Portal & API Sandbox)
    3. `admin.bitroot.lab` (Executive Admin Suite - Cloudflare WAF)
    4. `portal.bitroot.lab` (Customer Support Dashboard)
    5. `staging.bitroot.lab` (Pre-production Testing - ModSecurity WAF)
    6. `auth.bitroot.lab` (Single Sign-On Authority)
    7. `vpn.bitroot.lab` (Enterprise SSL-VPN Gateway - ModSecurity WAF)
    8. `shop.bitroot.lab` (Software Licensing & Store)
    9. `blog.bitroot.lab` (Tech Blog & Security Advisories)
    10. `status.bitroot.lab` (System Health & Uptime Monitor)
  - **Dead / Decommissioned Subdomains (4)**:
    1. `old-api.bitroot.lab` (HTTP 503 Service Unavailable)
    2. `legacy.bitroot.lab` (HTTP 503 Service Unavailable)
    3. `test-internal.bitroot.lab` (HTTP 404 Not Found)
    4. `sandbox.bitroot.lab` (HTTP 503 Service Unavailable)

---

## 📝 Adding Subdomains to `/etc/hosts`

### Linux / Kali Linux / macOS Command:
```bash
HOST_IP="127.0.0.1"
echo "${HOST_IP} bitroot.lab api.bitroot.lab dev.bitroot.lab admin.bitroot.lab portal.bitroot.lab staging.bitroot.lab auth.bitroot.lab vpn.bitroot.lab shop.bitroot.lab blog.bitroot.lab status.bitroot.lab old-api.bitroot.lab legacy.bitroot.lab test-internal.bitroot.lab sandbox.bitroot.lab" | sudo tee -a /etc/hosts
```

### Windows PowerShell Command (Run as Administrator):
```powershell
$HOST_IP = "127.0.0.1"
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "$HOST_IP bitroot.lab api.bitroot.lab dev.bitroot.lab admin.bitroot.lab portal.bitroot.lab staging.bitroot.lab auth.bitroot.lab vpn.bitroot.lab shop.bitroot.lab blog.bitroot.lab status.bitroot.lab old-api.bitroot.lab legacy.bitroot.lab test-internal.bitroot.lab sandbox.bitroot.lab"
```

---

## 🛠 Reconnaissance Tools Supported

You can run standard security tools against `bitroot.lab`:

### 1. DNS & Subdomain Enumeration
```bash
# Subfinder
subfinder -d bitroot.lab

# Assetfinder
assetfinder --subs-only bitroot.lab

# DNSEnum via local Mini DNS (UDP port 5353)
dnsenum bitroot.lab --dnsserver 127.0.0.1 -p 5353
```

### 2. HTTP/HTTPS Probing (`httpx`)
```bash
httpx -l subdomains.txt -title -status-code -tech-detect -web-server -no-color
```

### 3. WAF Detection (`wafw00f`)
```bash
# Detect Cloudflare WAF on admin portal
wafw00f https://admin.bitroot.lab:8091

# Detect ModSecurity WAF on VPN gateway
wafw00f https://vpn.bitroot.lab:8091
```

---

## ⚙️ Configuration & Live Sync API

The lab supports live parameter updates from the central Cyber Range Manager:

```bash
# Update difficulty or purpose
curl -k -X POST "https://localhost:8091/api/v1/configure?difficulty=intermediate&environment_purpose=cybersecurity"
```
