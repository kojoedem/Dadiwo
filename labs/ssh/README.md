# 🔑 SSH Microservice (Secure Shell Hacking & Defense)

The **Dadiwoo SSH Microservice** provides a complete interactive SSH server environment (TCP 2222) and web management dashboard (HTTP 8088) for learning SSH brute-forcing with Hydra/Medusa, weak key authentication, restricted shell breakouts, sudo privilege escalation, and fail2ban rate limiting.

---

## 🎯 Key Capabilities & Cyber Range Scenarios

1. **Direct Terminal SSH Connection**:
   - Access from Kali VM using `ssh user@<IP> -p 2222` or `ssh admin@<IP> -p 2222`.
2. **Password Brute-Force Attacks (Hydra / Medusa)**:
   - Perform automated credential cracking against port 2222.
3. **Leaked RSA Private Key Authentication**:
   - Download leaked PEM keys (`id_rsa_user.pem`) from Web UI to authenticate passwordlessly.
4. **Privilege Escalation**:
   - Test `sudo -l` for NOPASSWD root execution.
5. **Fail2Ban Auto-Block Defense**:
   - Automatically ban IPs with > 3 failed login attempts.

---

## 🚀 Port Allocations

- **Web UI & Control Dashboard**: `http://ssh.lab:8088` (or `http://<IP>:8088`)
- **Interactive SSH Server**: TCP Port `2222`

---

## 🧪 Testing

Run unit tests:
```bash
PYTHONPATH=labs/ssh/app pytest labs/ssh/tests/
```
