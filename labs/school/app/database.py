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
            pin TEXT NOT NULL DEFAULT '1234',
            full_name TEXT NOT NULL,
            program TEXT NOT NULL,
            gpa REAL NOT NULL DEFAULT 3.0,
            fees_due REAL NOT NULL DEFAULT 0.0,
            flag TEXT DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_code TEXT NOT NULL,
            course_name TEXT NOT NULL,
            credits INTEGER NOT NULL DEFAULT 3,
            grade TEXT NOT NULL DEFAULT 'A',
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    try:
        cursor.execute("ALTER TABLE students ADD COLUMN pin TEXT NOT NULL DEFAULT '1234'")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT COUNT(*) as count FROM students")
    if cursor.fetchone()["count"] == 0:
        sample_students = [
            ("STD-1001", "1234", "Kofi Mensah", "BSc Computer Science", 3.85, 0.00, None),
            ("STD-1002", "1234", "Ama Serwaa", "BSc Cybersecurity", 3.92, 150.00, None),
            ("STD-1003", "1234", "Kwame Addo", "BSc Network Engineering", 3.50, 0.00, "FLAG{SCHOOL_IDOR_ACADEMIC_RECORD_COMPROMISE_2026}")
        ]

        cursor.executemany("""
            INSERT INTO students (student_id, pin, full_name, program, gpa, fees_due, flag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_students)

        sample_courses = [
            # Kofi Mensah (STD-1001)
            ("STD-1001", "CS101", "Introduction to Computer Science", 3, "A"),
            ("STD-1001", "CS202", "Data Structures & Algorithms", 4, "A"),
            ("STD-1001", "NET301", "Computer Networks & Protocols", 3, "B+"),
            ("STD-1001", "SEC401", "Ethical Hacking & Web Penetration Testing", 3, "A"),

            # Ama Serwaa (STD-1002)
            ("STD-1002", "SEC101", "Cybersecurity Fundamentals", 3, "A"),
            ("STD-1002", "SEC202", "Network Defence & Firewalls", 4, "A"),
            ("STD-1002", "SEC303", "Cryptography & PKI", 3, "A"),
            ("STD-1002", "SEC404", "Digital Forensics & Incident Response", 3, "A-"),

            # Kwame Addo (STD-1003)
            ("STD-1003", "NET101", "Routing & Switching Basics", 3, "B"),
            ("STD-1003", "NET202", "Enterprise Network Design", 4, "A"),
            ("STD-1003", "NET303", "Wireless & Mobile Networks", 3, "B+"),
            ("STD-1003", "SEC405", "Cloud Security Architecture", 3, "A")
        ]

        cursor.executemany("""
            INSERT INTO courses (student_id, course_code, course_name, credits, grade)
            VALUES (?, ?, ?, ?, ?)
        """, sample_courses)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
