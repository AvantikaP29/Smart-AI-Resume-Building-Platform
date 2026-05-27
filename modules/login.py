"""Login page module for HireSense AI."""
import streamlit as st
from utils.database import authenticate_user
def show():
    _, col2, _ = st.columns([1, 1.4, 1])
    
    with col2:
        # Keep your signature styling
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

        # Login Form (Wrapped to fix the rerun/loop issue)
        with st.form("login_form"):
            username_or_email = st.text_input("Username or Email", placeholder="Enter your credentials")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            # Form Submit Button
            login_btn = st.form_submit_button("🚀 Log In", use_container_width=True)
            
            if login_btn:
                if not username_or_email or not password:
                    st.error("Please enter both credentials.")
                else:
                    # Authenticate against your database
                    user = authenticate_user(username_or_email, password)
                    if user:
                        st.success(f"👋 Welcome back!")
                        st.session_state.authenticated = True
                        st.session_state.username = username_or_email
                        st.session_state.page = "dashboard"
                        st.rerun() # Forces page to update state immediately
                    else:
                        st.error("❌ Invalid username or password.")

        # Navigation Buttons (Stay outside the form)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📝 Sign Up", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
        with col_b:
            if st.button("🔒 Reset Password", use_container_width=True):
                st.session_state.page = "forgot_password"
                st.rerun()



