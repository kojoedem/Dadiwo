# 🌊 Wave Chat Social Media Platform Lab

Simulates a modern social media platform microservice (**Wave Chat**) designed for studying Open Source Intelligence (OSINT) gathering, social profile reconnaissance, and image compression asset analysis.

## Features & Capabilities
- **User Registration**: Create social profiles with detailed personal metadata (Full Name, Bio, Email, Phone Number, Location, Workplace, Job Title, Relationship Status, Profile Picture). Supports pre-seeded target accounts and user account creation (at least 5 accounts).
- **Multi-Photo Upload & Asset Compression**: Upload up to 10+ photos per post. Images are automatically processed and compressed down to small KB sizes (e.g., 5 KB - 30 KB) using Pillow for optimized microservice storage.
- **OSINT Target Directory & Search**: Look up target accounts, workplaces, and locations to harvest reconnaissance intelligence.
- **Dual-Mode Architecture**: Supports `cybersecurity` (active interactive OSINT testing) and `networking` (passive node) modes via `ENVIRONMENT_PURPOSE`.

## Vulnerabilities & Objectives
- **OSINT Reconnaissance**: Discover hidden target flags and sensitive corporate contact details buried in target profiles (e.g. `alex_ceo`).
- **Profile Enumeration**: Query public user directories and API endpoints `/api/v1/users` and `/api/v1/users/{username}`.
- **SSL/TLS Certificate Analysis & Exploitation**:
  - **Weak Mode (`beginner` / `intermediate`)**: The platform uses an expired Let's Encrypt Staging certificate with a weak 1024-bit RSA key and a publicly leaked private key (`/certificate/download/key.pem`).
  - **Attack Scenario**: Download the leaked private key from `/certificate` or `/api/v1/certificate`, import it into Wireshark (`Edit -> Preferences -> Protocols -> TLS -> RSA Keys List`), and passively decrypt all encrypted traffic captured from Wave Chat users.
  - **Secure Mode (`DIFFICULTY_LEVEL=secure`)**: Upgrades the platform certificate to a valid TLS 1.3 certificate with strong 4096-bit RSA / ECDSA keys, Perfect Forward Secrecy (PFS), and strict HSTS headers. Exploitation or passive decryption via key extraction in Kali Linux is impossible.

## Flags
- Target CEO Recon Flag: `FLAG{WAVE_OSINT_CEO_LOCATION_RECON_2026}`
- Let's Encrypt Staging Certificate Exploit Flag: `FLAG{LETS_ENCRYPT_STAGING_KEY_EXPLOITED_2026}`
