"""
Database utility module for AI Resume Screening System.
Handles SQLite operations for users, resumes, and admin analytics.
"""

import sqlite3
import bcrypt
import os
import streamlit as st
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")



def get_connection():
    """Returns a fresh connection instance tied securely to your persistent path configuration."""
    # This prevents the app from creating a temporary database file that gets erased on server reboots!
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_resource
def init_db():
    """Initialize database with all required tables exactly once on boot."""
    import bcrypt

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Clean Users Table Creation (Email is now native, no alter needed)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'candidate',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # 2. Resumes table
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

    # 3. Chat history table
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

    # 4. Handle default admin creation cleanly
    admin_exists = cursor.execute(
        "SELECT id FROM users WHERE role='admin'"
    ).fetchone()
    NEW_STRONG_PASSWORD = (
        "Avantika@#2026"  # Change this to your preferred pass
    )

    if not admin_exists:
        hashed = bcrypt.hashpw(
            NEW_STRONG_PASSWORD.encode(), bcrypt.gensalt()
        ).decode()
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ("admin", "admin@resumeai.com", hashed, "admin"),
        )
    else:
        hashed = bcrypt.hashpw(
            NEW_STRONG_PASSWORD.encode(), bcrypt.gensalt()
        ).decode()
        cursor.execute(
            "UPDATE users SET password = ? WHERE role = 'admin'", (hashed,)
        )

    conn.commit()
    conn.close()
# ─── USER OPERATIONS ─────────────────────────────────────────────────────────

def create_user(username, email, password):
    import bcrypt
    conn = get_connection()
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()
    
    # 🎯 FIX: Force lowercase and strip spaces right at entry
    username = username.strip().lower()
    email = email.strip().lower()
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password, role) 
            VALUES (?, ?, ?, 'candidate')
        """, (username, email, hashed_password))
        conn.commit()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row is not None:
            new_user = dict(row)
        else:
            new_user = {
                "id": cursor.lastrowid,
                "username": username,
                "email": email,
                "role": "candidate"
            }
            
        conn.close()
        return {"success": True, "message": "Account created!", "user": new_user}
        
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "message": "Username or Email already registered."}

import sqlite3
import bcrypt

def authenticate_user(username_or_email, password):
    conn = get_connection() 
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 🧼 Strip whitespace and enforce uniform lowercase lookup
    credential = username_or_email.strip().lower()
    
    # Query your table wrapping column keys in LOWER() to guarantee case-insensitivity
    cursor.execute("""
        SELECT * FROM users 
        WHERE LOWER(username) = ? OR LOWER(email) = ?
    """, (credential, credential))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        user_dict = dict(user)
        stored_password = user_dict["password"]
        
        # Verify the password match using bcrypt
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return user_dict
            
    return None
# 🎯 ADD THIS TO THE VERY BOTTOM OF utils/database.py

def get_user_by_email(email):
    """Fetches a user profile by email safely for password resets."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None


def update_password(email: str, new_password: str) -> bool:
    """Updates a user's password securely with a new hash."""
    import bcrypt
    conn = get_connection()
    cursor = conn.cursor()
    
    # Hash the brand new password securely
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        cursor.execute("""
            UPDATE users 
            SET password = ? 
            WHERE LOWER(email) = ?
        """, (hashed_password, email.strip().lower()))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False


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


def get_user_resumes(user_id):
    """Fetches all resumes uploaded by a specific user safely."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM resumes 
        WHERE user_id = ? 
        ORDER BY uploaded_at DESC
    """, (user_id,))
    
    resumes = cursor.fetchall()
    conn.close()
    
    # 🛡️ CRITICAL FIX: If no resumes exist yet, return an empty list instead of crashing!
    if resumes is None:
        return []
        
    return [dict(r) for r in resumes]


def get_resume_stats() -> Dict:
    """Get analytics stats for admin dashboard."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # Ensure rows can be queried as dicts
    cursor = conn.cursor()
    
    total_users = cursor.execute("SELECT COUNT(*) FROM users WHERE role='candidate'").fetchone()[0]
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
        "role_distribution": {r["predicted_role"]: r["count"] for r in role_dist} if role_dist else {},
        "category_distribution": {c["ats_category"]: c["count"] for c in category_dist} if category_dist else {}
    }


# 🎯 NEW HELPER: Add this function right below get_resume_stats()
def get_salary_benchmarks():
    """Returns salary benchmarks calibrated for the Indian tech market (LPA)."""
    return [
        {"role": "🔬 Data Scientist ⭐ Your match", "entry": "₹6.5L", "mid": "₹12.0L", "senior": "₹24.0L"},
        {"role": "🤖 AI/ML Engineer", "entry": "₹8.0L", "mid": "₹15.0L", "senior": "₹28.0L"},
        {"role": "🌐 Web Developer", "entry": "₹4.0L", "mid": "₹7.5L", "senior": "₹14.0L"},
        {"role": "⚙️ DevOps Engineer", "entry": "₹5.5L", "mid": "₹10.0L", "senior": "₹18.0L"},
        {"role": "☁️ Cloud Engineer", "entry": "₹6.0L", "mid": "₹11.0L", "senior": "₹20.0L"},
        {"role": "🛡️ Cybersecurity Analyst", "entry": "₹5.0L", "mid": "₹9.0L", "senior": "₹16.0L"},
        {"role": "📊 Business Analyst", "entry": "₹4.5L", "mid": "₹8.0L", "senior": "₹13.0L"},
        {"role": "🐍 Python Developer", "entry": "₹4.5L", "mid": "₹8.5L", "senior": "₹15.0L"}
    ]

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
