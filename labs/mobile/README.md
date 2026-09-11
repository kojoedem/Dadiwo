# 📱 Mobile Phone & Bluetooth Simulator Cyber Range Lab

Simulates a smartphone device (e.g. Pixel 8 Pro) with active Bluetooth discoverability, contact exfiltration endpoints, and weak pairing security.

## Vulnerabilities & Objectives
- **Beginner / Intermediate**: Weak default Bluetooth PIN code (`0000`) and unauthenticated contact exfiltration via `/api/v1/bluetooth/exfiltrate` (BlueBorne / AT command simulation).
- **Secure**: PIN authentication enforcement and Bluetooth encryption controls.

## Flag
- Target Mobile Flag: `FLAG{BLUETOOTH_BLUEBORNE_EXFILTRATION_2026}`
