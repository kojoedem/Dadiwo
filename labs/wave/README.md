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
- **Secure Mode**: When `DIFFICULTY_LEVEL=secure`, sensitive flags and PIN details are sanitized from API outputs.

## Flags
- Target CEO Recon Flag: `FLAG{WAVE_OSINT_CEO_LOCATION_RECON_2026}`
