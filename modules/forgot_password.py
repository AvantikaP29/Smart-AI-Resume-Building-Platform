"""Forgot Password page."""
import streamlit as st
from utils.database import update_password # Ensure this exists in your database.py

def show():
    _, col2, _ = st.columns([1, 1.4, 1])
    with col2:
        st.subheader("🔒 Reset Password")
        
        with st.form("reset_form"):
            email = st.text_input("Enter your registered email")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submit = st.form_submit_button("Update Password")
            
            if submit:
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    # Call your backend function
                    # Ensure update_password checks if email exists and updates DB
                    result = update_password(email, new_password)
                    if result["success"]:
                        st.success("Password updated! Redirecting to login...")
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(result["message"])

        if st.button("← Back to Login"):
            st.session_state.page = "login"
            st.rerun()
      
