"""
Database utility module for AI Resume Screening System.
Handles SQLite operations for users, resumes, and admin analytics.
"""

import sqlite3
import bcrypt
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")


def get_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with all required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Resumes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT,
            resume_text TEXT,
            ats_score REAL,
            ats_category TEXT,
            predicted_role TEXT,
            confidence_score REAL,
            skills_found TEXT,
            missing_skills TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()

   # Create default admin if not exists
    admin_exists = cursor.execute(
        "SELECT id FROM users WHERE role='admin'"
    ).fetchone()

    # 🔒 CHANGE THIS to your chosen secure password string
    NEW_STRONG_PASSWORD = "Avantika#$2026" 

    if not admin_exists:
        hashed = bcrypt.hashpw(NEW_STRONG_PASSWORD.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ("admin", "admin@resumeai.com", hashed, "admin")
        )
        conn.commit()
    else:
        # 🛡️ Force-update the password for your existing deployment
        hashed = bcrypt.hashpw(NEW_STRONG_PASSWORD.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "UPDATE users SET password = ? WHERE username = 'admin'",
            (hashed,)
        )
        conn.commit()

    conn.close()
# ─── USER OPERATIONS ─────────────────────────────────────────────────────────

def create_user(username: str, email: str, password: str) -> Dict[str, Any]:
    """Create a new user with hashed password."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed)
        )
        conn.commit()
        conn.close()
        return {"success": True, "message": "Account created successfully!"}
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return {"success": False, "message": "Username already exists."}
        elif "email" in str(e):
            return {"success": False, "message": "Email already registered."}
        return {"success": False, "message": str(e)}


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user credentials."""
    conn = get_connection()
    cursor = conn.cursor()
    user = cursor.execute(
        "SELECT * FROM users WHERE username=? OR email=?", (username, username)
    ).fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        # Update last login
        conn = get_connection()
        conn.execute(
            "UPDATE users SET last_login=? WHERE id=?",
            (datetime.now(), user["id"])
        )
        conn.commit()
        conn.close()
        return dict(user)
    return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Fetch user by email."""
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(user) if user else None


def update_password(email: str, new_password: str) -> bool:
    """Update user password."""
    conn = get_connection()
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    rows = conn.execute(
        "UPDATE users SET password=? WHERE email=?", (hashed, email)
    ).rowcount
    conn.commit()
    conn.close()
    return rows > 0


def get_all_users() -> List[Dict]:
    """Fetch all users (admin only)."""
    conn = get_connection()
    users = conn.execute(
        "SELECT id, username, email, role, created_at, last_login FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(u) for u in users]


# ─── RESUME OPERATIONS ───────────────────────────────────────────────────────

def save_resume(user_id: int, filename: str, resume_text: str,
                ats_score: float, ats_category: str, predicted_role: str,
                confidence_score: float, skills_found: List[str],
                missing_skills: List[str]) -> int:
    """Save resume analysis results to database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resumes 
        (user_id, filename, resume_text, ats_score, ats_category, predicted_role,
         confidence_score, skills_found, missing_skills)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, filename, resume_text, ats_score, ats_category,
        predicted_role, confidence_score,
        ",".join(skills_found), ",".join(missing_skills)
    ))
    conn.commit()
    rid = cursor.lastrowid
    conn.close()
    return rid


def get_user_resumes(user_id: int) -> List[Dict]:
    """Get all resumes for a specific user."""
    conn = get_connection()
    resumes = conn.execute(
        "SELECT * FROM resumes WHERE user_id=? ORDER BY uploaded_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in resumes]


def get_all_resumes() -> List[Dict]:
    """Get all resumes with user info (admin)."""
    conn = get_connection()
    resumes = conn.execute("""
        SELECT r.*, u.username, u.email 
        FROM resumes r JOIN users u ON r.user_id = u.id
        ORDER BY r.uploaded_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in resumes]


def get_resume_stats() -> Dict:
    """Get analytics stats for admin dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    
    total_users = cursor.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
    total_resumes = cursor.execute("SELECT COUNT(*) FROM resumes").fetchone()[0]
    avg_ats = cursor.execute("SELECT AVG(ats_score) FROM resumes").fetchone()[0]
    
    role_dist = cursor.execute(
        "SELECT predicted_role, COUNT(*) as count FROM resumes GROUP BY predicted_role"
    ).fetchall()
    
    category_dist = cursor.execute(
        "SELECT ats_category, COUNT(*) as count FROM resumes GROUP BY ats_category"
    ).fetchall()
    
    conn.close()
    return {
        "total_users": total_users,
        "total_resumes": total_resumes,
        "avg_ats": round(avg_ats or 0, 1),
        "role_distribution": {r["predicted_role"]: r["count"] for r in role_dist},
        "category_distribution": {c["ats_category"]: c["count"] for c in category_dist}
    }


# ─── CHAT HISTORY ────────────────────────────────────────────────────────────

def save_chat_message(user_id: int, role: str, message: str):
    """Save chat message to history."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
        (user_id, role, message)
    )
    conn.commit()
    conn.close()


def get_chat_history(user_id: int, limit: int = 20) -> List[Dict]:
    """Get recent chat history for a user."""
    conn = get_connection()
    history = conn.execute(
        "SELECT role, message FROM chat_history WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(h) for h in reversed(history)]


def clear_chat_history(user_id: int):
    """Clear all chat history for a user."""
    conn = get_connection()
    conn.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
