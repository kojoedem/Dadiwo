# 🌐 ISP Customer Portal & Network Diagnostics Cyber Range Lab

Simulates an ISP customer management portal integrated with RADIUS subscriber APIs and router diagnostic ping tools.

## Vulnerabilities & Objectives
- **Intermediate / Advanced**: Command Injection in Diagnostic Tool (`host = 127.0.0.1; cat /etc/passwd` or `127.0.0.1; id`).
- **Secure**: Parameterized process argument array execution (`["ping", "-c", "2", host]`).

## Flag
- Target Admin Flag: `FLAG{ISP_COMMAND_INJECTION_RADIUS_EXPLOIT_2026}`
