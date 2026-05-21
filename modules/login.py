"""Login page for HireSense AI."""
import streamlit as st
from utils.database import authenticate_user


def show():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding:40px 0 20px;">
            <div style="font-size:3rem;">🧠</div>
            <h1 style="background:linear-gradient(135deg,#6c63ff,#00d4aa);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                        font-size:2rem; margin:0;">HireSense AI</h1>
            <p style="color:#9fa8da; font-size:0.9rem;">Smart Recruitment Platform</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#161829; border:1px solid rgba(108,99,255,0.25);
                    border-radius:16px; padding:32px; margin:0 auto;">
        """, unsafe_allow_html=True)

        st.markdown("<h3 style='color:#e8eaf6; margin-bottom:20px;'>👋 Welcome Back</h3>",
                    unsafe_allow_html=True)

        username = st.text_input("Username or Email", placeholder="Enter your username or email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

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

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔑 Forgot Password?", use_container_width=True):
            st.session_state.page = "forgot"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#4a5270; font-size:0.8rem;">
            Default Admin: <code style="color:#6c63ff;">admin</code> /
            <code style="color:#6c63ff;">admin123</code>
        </div>
        """, unsafe_allow_html=True)
