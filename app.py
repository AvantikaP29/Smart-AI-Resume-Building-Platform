

import streamlit as st
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.database import init_db

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HireSense AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "About": "AI Resume Screening & Job Role Prediction System v1.0"
    }
)

# ─── INITIALIZE DATABASE ──────────────────────────────────────────────────────
init_db()

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root Variables ── */
:root {
    --primary: #6c63ff;
    --primary-dark: #4f46e5;
    --secondary: #00d4aa;
    --accent: #ff6b6b;
    --bg-dark: #0d0f1a;
    --bg-card: #161829;
    --bg-card2: #1e2035;
    --text-primary: #e8eaf6;
    --text-secondary: #9fa8da;
    --border: rgba(108, 99, 255, 0.25);
    --success: #00d4aa;
    --warning: #ffd700;
    --danger: #ff6b6b;
    --gradient: linear-gradient(135deg, #6c63ff 0%, #00d4aa 100%);
    --font-main: 'Space Grotesk', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

/* ── Global Reset ── */
* { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-dark) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
}

[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Metric Cards ── */
[data-testid="metric-container"] {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--gradient) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: var(--font-main) !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(108, 99, 255, 0.4) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-card2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2) !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: var(--bg-card2) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 12px !important;
}

/* ── Progress Bar ── */
.stProgress > div > div > div {
    background: var(--gradient) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: var(--bg-card2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card2) !important;
    border-radius: 10px !important;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border-radius: 8px !important;
    font-family: var(--font-main) !important;
}
.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: white !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--bg-card2) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-dark); }
::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 3px; }

/* ── Custom card component ── */
.ai-card {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    margin: 8px 0;
    transition: border-color 0.2s;
}
.ai-card:hover { border-color: var(--primary); }

.ai-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-success { background: rgba(0,212,170,0.15); color: var(--success); border: 1px solid var(--success); }
.badge-warning { background: rgba(255,215,0,0.15); color: var(--warning); border: 1px solid var(--warning); }
.badge-danger  { background: rgba(255,107,107,0.15); color: var(--danger); border: 1px solid var(--danger); }
.badge-primary { background: rgba(108,99,255,0.15); color: var(--primary); border: 1px solid var(--primary); }

/* ── Sidebar nav items ── */
.sidebar-nav-item {
    padding: 10px 16px;
    border-radius: 8px;
    margin: 2px 0;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text-secondary);
    font-weight: 500;
}
.sidebar-nav-item:hover, .sidebar-nav-item.active {
    background: rgba(108, 99, 255, 0.15);
    color: var(--primary);
}

/* ── Chat bubbles ── */
.chat-user {
    background: linear-gradient(135deg, #6c63ff, #4f46e5);
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px 40px;
    font-size: 0.9rem;
}
.chat-bot {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 40px 8px 0;
    font-size: 0.9rem;
}

/* ── Score ring placeholder ── */
.score-display {
    text-align: center;
    padding: 20px;
}
.score-number {
    font-size: 4rem;
    font-weight: 700;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
}
.score-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE DEFAULTS ───────────────────────────────────────────────────
def init_session():
    defaults = {
        "authenticated": False,
        "user": None,
        "page": "login",
        "resume_parsed": None,
        "ats_report": None,
        "prediction": None,
        "chat_history": [],
        "gemini_api_key": "",
        "theme": "dark",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ─── ROUTING ──────────────────────────────────────────────────────────────────
def route():
    if not st.session_state.authenticated:
        # Public pages: login / signup / forgot password
        page = st.session_state.get("page", "login")
        if page == "signup":
            from modules.signup import show
            show()
        elif page == "forgot":
            from modules.forgot_password import show
            show()
        else:
            from modules.login import show
            show()
    else:
        # Authenticated layout with sidebar
        render_sidebar()
        page = st.session_state.get("page", "dashboard")

        if page == "dashboard":
            from modules.dashboard import show
            show()
        elif page == "upload":
            from modules.upload_resume import show
            show()
        elif page == "ats":
            from modules.ats_analysis import show
            show()
        elif page == "prediction":
            from modules.prediction import show
            show()
        elif page == "chatbot":
            from modules.chatbot import show
            show()
        elif page == "analytics":
            from modules.analytics import show
            show()
        elif page == "admin" and st.session_state.user.get("role") == "admin":
            from modules.admin import show
            show()
        else:
            from pages.dashboard import show
            show()
        


def render_sidebar():
    user = st.session_state.user
    is_admin = user.get("role") == "admin"

    with st.sidebar:
        # Logo & branding
        st.title("🧠 HireSense AI")
        st.markdown("""
        <div style="text-align:center; padding: 20px 0 10px;">
            <div style="font-size:2.5rem;">🧠</div>
            <div style="font-size:1.2rem; font-weight:700; background:linear-gradient(135deg,#6c63ff,#00d4aa);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                HireSense AI
            </div>
            <div style="font-size:0.7rem; color:#9fa8da; margin-top:2px;">
                Smart Resume Building Platform
            </div>
        </div>
        <hr style="border-color:rgba(108,99,255,0.2); margin:10px 0;">
        """, unsafe_allow_html=True)

        # User info
        st.markdown(f"""
        <div style="background:rgba(108,99,255,0.1); border:1px solid rgba(108,99,255,0.2);
                    border-radius:10px; padding:12px; margin-bottom:12px;">
            <div style="font-size:0.8rem; color:#9fa8da;">Logged in as</div>
            <div style="font-weight:600; color:#e8eaf6;">👤 {user['username']}</div>
            <div style="font-size:0.75rem; color:#6c63ff;">
                {'🛡️ Admin' if is_admin else '🎯 Candidate'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        nav_items = [
            ("🏠", "Dashboard", "dashboard"),
            ("📤", "Upload Resume", "upload"),
            ("📊", "ATS Analysis", "ats"),
            ("🎯", "Job Prediction", "prediction"),
            ("🤖", "AI Chatbot", "chatbot"),
            ("📈", "Analytics", "analytics"),
        ]
        if is_admin:
            nav_items.append(("🛡️", "Admin Panel", "admin"))

        for icon, label, page_key in nav_items:
            active = st.session_state.page == page_key
            btn_style = (
                "background:rgba(108,99,255,0.2); color:#6c63ff; border:1px solid rgba(108,99,255,0.4);"
                if active else
                "background:transparent; color:#9fa8da; border:1px solid transparent;"
            )
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
            ):
                st.session_state.page = page_key
                st.rerun()

        st.markdown("<hr style='border-color:rgba(108,99,255,0.2); margin:12px 0;'>", unsafe_allow_html=True)

        # 1. Fetch the key from the background Streamlit secrets securely
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = None

# 2. Updated UI code (Informs the user without exposing the key)
with st.expander("⚙️ AI Settings"):
    if api_key:
        st.success("🔒 System API Key is securely loaded and active.")
    else:
        # Fallback text input ONLY if the secrets key isn't configured
        api_key_input = st.text_input(
            "Enter Personal Gemini API Key",
            type="password",
            placeholder="AIza...",
            help="Get a free key at https://makersuite.google.com/app/apikey"
        )
        if api_key_input:
            api_key = api_key_input
            
        # Logout
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        if st.button("🚪  Logout", use_container_width=True):
            for key in ["authenticated", "user", "resume_parsed", "ats_report",
                        "prediction", "chat_history"]:
                st.session_state[key] = None if key not in ["authenticated"] else False
            st.session_state.page = "login"
            st.rerun()

        # Version footer
    with st.sidebar:
        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
        st.divider()
        st.markdown(
            """
            <div style="text-align:center; font-size:0.7rem; color:#888888; padding-bottom: 20px;">
                HireSense AI v1.0 • Powered by Gemini
            </div>
            """,
            unsafe_allow_html=True
        )


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    route()
else:
    route()
