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
        # Add your buttons here...

# 4. Global CSS
st.markdown("""
<style>
    .stButton > button { background: linear-gradient(135deg, #6c63ff, #00d4aa) !important; color: white !important; }
    [data-testid="stAppViewContainer"] { background-color: #0d0f1a !important; color: #e8eaf6 !important; }
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
