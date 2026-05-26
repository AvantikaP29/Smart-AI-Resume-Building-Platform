import os
import sys
import streamlit as st 

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.database import init_db

st.set_page_config(page_title="HireSense AI", page_icon="🧠", layout="wide")

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

def init_session():
    defaults = {"authenticated": False, "user": None, "page": "login"}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_session()

def render_sidebar():
    if "user" in st.session_state and st.session_state.user:
        user = st.session_state.user
    else:
        user = {"username": "Guest", "role": "candidate"}
    
    with st.sidebar:
        st.write(f"Logged in as: {user['username']}")
        if st.button("Dashboard"): st.session_state.page = "dashboard"; st.rerun()
        if st.button("Logout"): 
            st.session_state.authenticated = False; st.session_state.page = "login"; st.rerun()

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
        else:
            from modules.login import show
            show()

if __name__ == "__main__":
    route()
