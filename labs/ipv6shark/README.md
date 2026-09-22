# 🦈 Dadiwoo IPv6 Shark - IPv6 Network Security Lab

The **IPv6 Shark** microservice is a dedicated single-page blog and cybersecurity portfolio designed for learning and practicing **IPv6 network security, red team attacks, and blue team defenses**.

---

## 🎯 Overview

**IPv6 Shark** is built to operate over **IPv6 transport** and dual-stack (IPv4 / IPv6) sockets. It addresses the common enterprise risk where networks run dual-stack setups with IPv6 enabled by default but lack dedicated IPv6 firewall rules, First-Hop Security (FHS), or monitoring.

### Key Learning Objectives:
- **Red Team Scenarios**: Rogue SLAAC Router Advertisement (RA) injection, Neighbor Discovery Protocol (NDP) poisoning, Extension Header firewall bypasses, and ICMPv6 all-nodes multicast discovery.
- **Blue Team Defenses**: Router Advertisement Guard (RA Guard - RFC 6105), Secure Neighbor Discovery (SEND - RFC 3971), dual-stack `ip6tables`/`nftables` filtering, and IPv6 Bogon prefix ACLs.
- **IPv6 Connectivity**: Using IPv6 loopback addresses (`http://[::1]:8090`) and configuring local IPv6 domain mapping (`http://ipv6.lab:8090`).

---

## 🌐 Local IPv6 Access & Domain Configuration

### 1. Direct IPv6 Access
Access the microservice directly via IPv6 transport in your browser or curl:
- **Browser**: `http://[::1]:8090`
- **cURL**: `curl -g -6 "http://[::1]:8090/"`

### 2. Local IPv6 Domain Mapping (`ipv6.lab`)
To resolve `http://ipv6.lab:8090`, add the IPv6 entry to your system's `hosts` file:

#### Linux / macOS (`/etc/hosts`):
```bash
echo "::1 ipv6.lab" | sudo tee -a /etc/hosts
echo "127.0.0.1 ipv6.lab" | sudo tee -a /etc/hosts
```

#### Windows (`C:\Windows\System32\drivers\etc\hosts` in Admin PowerShell):
```powershell
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "::1 ipv6.lab"
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "127.0.0.1 ipv6.lab"
```

---

## 🛠 API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Single-page portfolio & tech blog UI |
| `/api/v1/scenarios` | `GET` | List all IPv6 Red/Blue team scenarios (`?type=red_team` or `blue_team`) |
| `/api/v1/scenarios/{id}` | `GET` | Get details for a specific scenario |
| `/api/v1/posts` | `GET` | Fetch tech blog research articles |
| `/api/v1/ipv6/ping` | `GET` | Execute diagnostic ICMPv6 ping (`?target=fe80::1001`) |
| `/api/v1/ipv6/ndp-table` | `GET` / `POST` | Inspect and add Neighbor Discovery Protocol (NDP) entries |
| `/api/v1/configure` | `GET` / `POST` | Get/Set difficulty level and environment purpose |

---

## 🚀 Running Direct Host Execution

```bash
PYTHONPATH=labs/ipv6shark/app python3 -m uvicorn main:app --host :: --port 8090 --app-dir labs/ipv6shark/app
```
