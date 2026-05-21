"""Forgot Password page."""
import streamlit as st
from utils.database import get_user_by_email, update_password


def show():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding:40px 0 20px;">
            <div style="font-size:3rem;">🔑</div>
            <h2 style="color:#e8eaf6;">Reset Password</h2>
            <p style="color:#9fa8da;">Enter your email to reset password</p>
        </div>
        <div style="background:#161829; border:1px solid rgba(108,99,255,0.25);
                    border-radius:16px; padding:32px;">
        """, unsafe_allow_html=True)

        email = st.text_input("Registered Email", placeholder="your@email.com")
        new_pass = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Reset Password", use_container_width=True):
                if not email or not new_pass or not confirm:
                    st.error("All fields are required.")
                elif new_pass != confirm:
                    st.error("Passwords don't match.")
                elif len(new_pass) < 6:
                    st.error("Password must be 6+ characters.")
                else:
                    user = get_user_by_email(email)
                    if user:
                        update_password(email, new_pass)
                        st.success("✅ Password reset successfully!")
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("❌ Email not found.")
        with col_b:
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
