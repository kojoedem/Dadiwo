import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "wave.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL DEFAULT '1234',
            full_name TEXT NOT NULL,
            bio TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            workplace TEXT,
            job_title TEXT,
            relationship_status TEXT,
            profile_pic TEXT,
            flag TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            caption TEXT,
            location_tag TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT,
            file_size_kb REAL NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        sample_users = [
            (
                "alex_ceo", "1234", "Alex Mercer",
                "CEO & Founder at Apex Wave Dynamics. Technology enthusiast, keynote speaker & angel investor.",
                "alex.mercer@apexwave.lab", "+1-555-019-2831", "Seattle, WA",
                "Apex Wave Dynamics", "Chief Executive Officer", "Married",
                "avatar_alex.jpg", "FLAG{WAVE_OSINT_CEO_LOCATION_RECON_2026}"
            ),
            (
                "sarah_sec", "1234", "Sarah Connor",
                "Lead Cybersecurity Engineer. Threat hunting, Incident Response & Zero Trust Architectures.",
                "s.connor@apexwave.lab", "+1-555-014-9982", "Austin, TX",
                "Apex Wave Dynamics", "Lead Cyber Security Engineer", "Single",
                "avatar_sarah.jpg", None
            ),
            (
                "david_dev", "1234", "David Miller",
                "Senior Full Stack Developer building scalable cloud microservices. Coffee & Python.",
                "david.m@devlabs.io", "+1-555-018-4421", "San Francisco, CA",
                "DevLabs Global", "Senior Developer", "In a relationship",
                "avatar_david.jpg", None
            ),
            (
                "elena_mkt", "1234", "Elena Rostova",
                "VP of Global Marketing & Public Relations. Digital campaigns, social growth & brand strategy.",
                "elena.r@wavechat.lab", "+1-555-012-7710", "New York, NY",
                "Wave Chat Inc.", "VP of Marketing", "Single",
                "avatar_elena.jpg", None
            ),
            (
                "marcus_ops", "1234", "Marcus Vance",
                "Infrastructure & Cloud Operations Lead. Kubernetes, DevSecOps & High Availability Systems.",
                "m.vance@wavechat.lab", "+1-555-016-3390", "Chicago, IL",
                "Wave Chat Inc.", "Cloud Ops Lead", "Married",
                "avatar_marcus.jpg", None
            )
        ]

        cursor.executemany("""
            INSERT INTO users (username, pin, full_name, bio, email, phone, location, workplace, job_title, relationship_status, profile_pic, flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_users)

        # Seed sample posts
        sample_posts = [
            ("alex_ceo", "Excited to launch our new Wave Chat platform! Connectivity redefined. 🌊🚀", "Seattle HQ"),
            ("sarah_sec", "Performing annual penetration tests on our perimeter services today. Safety first! 🔐", "Security Lab"),
            ("david_dev", "Deploying microservices with lightweight asset pipeline. Clean code everyday!", "San Francisco HQ")
        ]

        for username, caption, loc in sample_posts:
            cursor.execute("INSERT INTO posts (username, caption, location_tag) VALUES (?, ?, ?)", (username, caption, loc))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
