"""Signup page for HireSense AI."""
import streamlit as st
from utils.database import create_user


def show():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding:40px 0 20px;">
            <div style="font-size:3rem;">🧠</div>
            <h1 style="background:linear-gradient(135deg,#6c63ff,#00d4aa);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                        font-size:2rem; margin:0;">HireSense AI</h1>
            <p style="color:#9fa8da;">Create your account</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#161829; border:1px solid rgba(108,99,255,0.25);
                    border-radius:16px; padding:32px;">
        """, unsafe_allow_html=True)

        st.markdown("<h3 style='color:#e8eaf6; margin-bottom:20px;'>🚀 Create Account</h3>",
                    unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email Address", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Min 6 characters")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password")

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
                        st.success("✅ " + result["message"])
                        st.info("Redirecting to login...")
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("❌ " + result["message"])
        with col_b:
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
