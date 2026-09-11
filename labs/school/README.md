# 🎓 University Student Portal Cyber Range Lab

Simulates an academic university portal with student records, GPA lookup, and document uploads.

## Vulnerabilities & Objectives
- **Beginner / Intermediate**: IDOR on `/api/v1/students/{student_id}` to retrieve registrar account `STD-9000`.
- **Advanced / Expert**: Arbitrary File Upload flaw allowing executable script upload.
- **Secure**: File extension whitelist restriction (`.pdf`, `.docx`, `.png`, `.jpg`).

## Flag
- Target Registrar Flag: `FLAG{SCHOOL_IDOR_FILE_UPLOAD_COMPROMISE_2026}`
