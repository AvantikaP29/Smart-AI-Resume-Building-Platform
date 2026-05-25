"""Signup page for HireSense AI."""
import streamlit as st
from utils.database import create_user


def show():
    # Centered column layout helper
    _, col2, _ = st.columns([1, 1.4, 1])
    
    with col2:
        # 1. Clean, Perfectly Centered Branding Header (Matches your login page)
        st.markdown("""
        <div style="text-align:center; padding: 30px 15px 20px 0px; width: 100%;">
            <div style="font-size:3.5rem; margin-bottom: 10px; text-align: center;">🧠</div>
            <h1 style="background:linear-gradient(135deg,#6c63ff,#00d4aa);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                        font-size:2.5rem; margin:0; font-weight: 700; text-align: center; display: block;">
                HireSense AI
            </h1>
            <p style="color:#9fa8da; font-size:1rem; margin-top: 8px; text-align: center; font-weight: 500;">
                Smart Resume Building Platform
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Space divider between logo and inputs
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # 2. Native Input Fields (Completely clean and clear of broken HTML containers)
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email Address", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Min 6 characters")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password")

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # 3. Interactive Action Buttons Sequence
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Create Account", use_container_width=True):
                if not all([username, email, password, confirm]):
                    st.error("All fields are required.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif "@" not in email:
                    st.error("Invalid email address.")
                else:
                    result = create_user(username, email, password)
                    if result["success"]:
                        st.success("🎉 Account created successfully! Please log in with your credentials.")
                        
                        # Clear any accidental auto-logins
                        st.session_state.authenticated = False
                        st.session_state.user = None
                        
                        # Redirect directly back to the clean manual login screen
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("❌ " + result["message"])
