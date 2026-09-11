import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "school.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            program TEXT NOT NULL,
            gpa REAL NOT NULL,
            fees_due REAL NOT NULL,
            flag TEXT DEFAULT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM students")
    if cursor.fetchone()["count"] == 0:
        sample_students = [
            ("STD-1001", "Kofi Mensah", "BSc Computer Science", 3.85, 0.00, None),
            ("STD-1002", "Ama Serwaa", "BSc Cybersecurity", 3.92, 150.00, None),
            ("STD-9000", "University Registrar Master", "System Administrator", 4.00, 0.00, "FLAG{SCHOOL_IDOR_FILE_UPLOAD_COMPROMISE_2026}")
        ]

        cursor.executemany("""
            INSERT INTO students (student_id, full_name, program, gpa, fees_due, flag)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_students)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
