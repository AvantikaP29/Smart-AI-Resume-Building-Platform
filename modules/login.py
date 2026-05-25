"""Login page for HireSense AI."""
import streamlit as st
from utils.database import authenticate_user

def show():
    # Centered column layout helper
    _, col2, _ = st.columns([1, 1.4, 1])
    
    with col2:
        # 1. Clean, Perfectly Centered Branding Header
        st.markdown("""
        <div style="text-align:center; padding: 30px 0 20px; width: 100%;">
            <div style="font-size:3.5rem; margin-bottom: 10px; text-align: center;">🧠</div>
            <h1 style="background:linear-gradient(135deg,#6c63ff,#00d4aa);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                        font-size:2.5rem; margin:0; font-weight: 700; text-align: center; display: block;">
                HireSense AI
            </h1>
            <p style="color:#9fa8da; font-size:1rem; margin-top: 8px; text-align: center;">
                Smart Recruitment Platform
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Space divider between logo and input elements
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # 2. Input Fields (Completely empty and secure)
        username = st.text_input("Username or Email", placeholder="Enter your username or email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        # 3. Interactive Action Buttons Sequence
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
