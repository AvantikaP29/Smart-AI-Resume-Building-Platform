import os
import sys
import streamlit as st 

# Add project root to path to prevent folder resolution bugs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.database import init_db

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="HireSense AI", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# ─── INITIALIZE DATABASE ──────────────────────────────────────────────────────
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# ─── GLOBAL CSS (Your original colors) ────────────────────────────────────────
st.markdown("""
<style>
:root { --primary: #6c63ff; --bg-dark: #0d0f1a; --bg-card2: #1e2035; --text-primary: #e8eaf6; }
html, body, [data-testid="stAppViewContainer"] { background-color: var(--bg-dark) !important; color: var(--text-primary) !important; }
.stButton > button { background: linear-gradient(135deg, #6c63ff 0%, #00d4aa 100%) !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
def init_session():
    defaults = {"authenticated": False, "user": None, "page": "login"}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_session()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("### 🧠 HireSense AI")
        if st.button("Dashboard", use_container_width=True): st.session_state.page = "dashboard"; st.rerun()
        if st.button("Upload Resume", use_container_width=True): st.session_state.page = "upload"; st.rerun()
        if st.button("Logout", use_container_width=True): 
            st.session_state.authenticated = False; st.session_state.page = "login"; st.rerun()

# ─── ROUTING ──────────────────────────────────────────────────────────────────
def route():
    if not st.session_state.authenticated:
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
        render_sidebar()
        page = st.session_state.get("page", "dashboard")
        if page == "dashboard":
            from modules.dashboard import show
            show()
        elif page == "upload":
            from modules.upload_resume import show
            show()
        else:
            from modules.login import show
            show()

if __name__ == "__main__":
    route()
