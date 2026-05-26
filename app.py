import os
import sys
import streamlit as st 

# 1. Page Config must be first
st.set_page_config(page_title="HireSense AI", page_icon="🧠", layout="wide")

# 2. Path and Database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.database import init_db

# 3. Sidebar function (Correctly indented)
def render_sidebar():
    with st.sidebar:
        st.markdown("### 🧠 HireSense AI")
        st.divider()
        
        # Navigation Items
        if st.button("🏠 Dashboard", use_container_width=True): 
            st.session_state.page = "dashboard"; st.rerun()
        if st.button("📤 Upload Resume", use_container_width=True): 
            st.session_state.page = "upload"; st.rerun()
        if st.button("📊 ATS Analysis", use_container_width=True): 
            st.session_state.page = "ats"; st.rerun()
        if st.button("🎯 Job Prediction", use_container_width=True): 
            st.session_state.page = "prediction"; st.rerun()
        if st.button("🤖 AI Chatbot", use_container_width=True): 
            st.session_state.page = "chatbot"; st.rerun()
            
        st.divider()
        if st.button("🚪 Logout", use_container_width=True): 
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.rerun()

# 4. Global CSS
st.markdown("""
<style>
    /* Original Theme Colors */
    :root {
        --primary: #6c63ff;
        --secondary: #00d4aa;
        --bg-dark: #0d0f1a;
        --bg-card: #161829;
        --text-primary: #e8eaf6;
        --gradient: linear-gradient(135deg, #6c63ff 0%, #00d4aa 100%);
    }

    /* Apply background and text colors */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-dark) !important;
        color: var(--text-primary) !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--bg-card) !important;
    }

    /* Button gradient styling */
    .stButton > button {
        background: var(--gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    
    /* Make buttons look clickable/hoverable */
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(108, 99, 255, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# Database Initialization
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

def route():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    page = st.session_state.get("page", "login")
    
    # 1. PUBLIC PAGES (No sidebar)
    if not st.session_state.authenticated:
        if page == "signup":
            from modules.signup import show
            show()
        elif page == "forgot":
            from modules.forgot_password import show
            show()
        else:
            from modules.login import show
            show()
            
    # 2. AUTHENTICATED PAGES (Sidebar included)
    else:
        render_sidebar()  # <--- THIS IS WHERE YOUR SIDEBAR GOES
        
        if page == "dashboard":
            from modules.dashboard import show
            show()
        elif page == "upload":
            from modules.upload_resume import show
            show()
        else:
            # Default to dashboard if page is unrecognized
            from modules.dashboard import show
            show()

if __name__ == "__main__":
    route()
