import os
import sys
import streamlit as st 

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.database import init_db

# 🎨 Page Config & CSS (Your original design)
st.set_page_config(page_title="HireSense AI", page_icon="🧠", layout="wide")
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
    else:
        # Dashboard flow (Your original structure)
        from modules.dashboard import show
        show()

if __name__ == "__main__":
    route()
