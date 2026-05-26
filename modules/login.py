"""Login page module for HireSense AI."""
import streamlit as st
from utils.database import authenticate_user


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
                Smart Resume Building Platform
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        username_or_email = st.text_input("Username or Email", placeholder="Enter your credentials")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🚀 Log In", use_container_width=True):
                if not username_or_email or not password:
                    st.error("Please enter both credentials.")
                else:
                    user = authenticate_user(username_or_email, password)
                    if user:
                        st.success(f"👋 Welcome back, {user['username']}!")
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("❌ Invalid username/email or password.")
                        
        with col_b:
            if st.button("📝 Sign Up Instead", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
                
        # Forgot password anchor
        st.markdown("<br><p style='text-align: center;'><a href='#' onclick='return false;' style='color: #6c63ff; text-decoration: none;'>Forgot Password?</a></p>", unsafe_allow_html=True)
        if st.button("🔒 Reset Password Profile", use_container_width=True):
            st.session_state.page = "forgot_password"
            st.rerun()

