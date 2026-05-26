"""Signup page module for HireSense AI."""
import streamlit as st
from utils.database import create_user


def show():
    _, col2, _ = st.columns([1, 1.4, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align:center; padding: 30px 15px 20px 0px; width: 100%;">
            <div style="font-size:3.5rem; margin-bottom: 10px; text-align: center;">🧠</div>
            <h1 style="background:linear-gradient(135deg,#6c63ff,#00d4aa);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                        font-size:2.5rem; margin:0; font-weight: 700; text-align: center; display: block;">
                HireSense AI
            </h1>
            <p style="color:#9fa8da; font-size:1rem; margin-top: 8px; text-align: center; font-weight: 500;">
                Create your account
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # Form fields
        username = st.text_input("Username", placeholder="Choose a unique username")
        email = st.text_input("Email Address", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Min 6 characters")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password")

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

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
                        st.success("🎉 Account created successfully! Please log in below.")
                        
                        # Hard reset authentication states to force manual input
                        st.session_state.authenticated = False
                        st.session_state.user = None
                        
                        # Redirect to clean login view
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("❌ " + result["message"])
                        
        with col_b:
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
