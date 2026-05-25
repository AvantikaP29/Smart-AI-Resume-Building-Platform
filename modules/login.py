"""Login page for HireSense AI."""
"""Login page for HireSense AI."""
import streamlit as st
from utils.database import authenticate_user

def show():
    # Centered column layout layout helper
    _, col2, _ = st.columns([1, 1.4, 1])
    
    with col2:
        # 1. Clean Branding Header (No weird floating border spacers)
        st.markdown("""
        <div style="text-align:center; padding: 20px 0 10px;">
            <div style="font-size:3.5rem; margin-bottom: 10px;">🧠</div>
            <h1 style="background:linear-gradient(135deg,#6c63ff,#00d4aa);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                        font-size:2.2rem; margin:0; font-weight: 700;">HireSense AI</h1>
            <p style="color:#9fa8da; font-size:0.95rem; margin-top: 5px;">Smart Recruitment Platform</p>
        </div>
        """, unsafe_allow_html=True)

        # 2. Fixed Neutral Entry Header (Replaced "Welcome Back" so it's clean for fresh users)
        st.markdown("""
        <h3 style='color:#e8eaf6; text-align: center; margin-top: 15px; margin-bottom: 25px; font-weight: 500;'>
            🔑 Account Access Portal
        </h3>
        """, unsafe_allow_html=True)

        # 3. Input Fields (Completely empty, secure, and formatting-error free)
        username = st.text_input("Username or Email", placeholder="Enter your username or email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # 4. Interactive Action Buttons Sequence
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🚀 Login", use_container_width=True):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials. Please try again.")
                        
        with col_b:
            if st.button("📝 Sign Up", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        
        if st.button("🔑 Forgot Password?", use_container_width=True):
            st.session_state.page = "forgot"
            st.rerun()

        # ❌ REMOVED: The old "Default Admin: admin / admin123" leakage string has been completely wiped out.
