import streamlit as st
from utils.database import get_user_resumes


def show():
    if 'user' not in st.session_state:
        st.error("Session expired or user not found. Please login again.")
        st.session_state.authenticated = False
        st.session_state.page = "login"
        st.rerun()
        return
    user = st.session_state.user
    resumes = get_user_resumes(user["id"])

    # Header
    st.markdown(f"""
    <div style="margin-bottom:30px;">
        <h1 style="color:#e8eaf6; margin:0; font-size:1.8rem;">
            👋 Hello, <span style="background:linear-gradient(135deg,#6c63ff,#00d4aa);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            {user['username'].title()}</span>!
        </h1>
        <p style="color:#9fa8da; margin-top:4px;">
            Your AI-powered career intelligence dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats
    total = len(resumes)
    avg_ats = round(sum(r["ats_score"] or 0 for r in resumes) / total, 1) if total else 0
    best_role = resumes[0]["predicted_role"] if resumes else "N/A"
    best_ats = max((r["ats_score"] or 0 for r in resumes), default=0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📄 Resumes Uploaded", total)
    with c2:
        st.metric("📊 Avg ATS Score", f"{avg_ats}/100" if total else "—")
    with c3:
        st.metric("🏆 Best ATS Score", f"{best_ats}/100" if total else "—")
    with c4:
        st.metric("🎯 Latest Prediction", best_role)

    st.markdown("<hr style='border-color:rgba(108,99,255,0.15); margin:24px 0;'>", unsafe_allow_html=True)

    # Quick Actions
    st.markdown("<h3 style='color:#e8eaf6;'>⚡ Quick Actions</h3>", unsafe_allow_html=True)
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("📤 Upload Resume", use_container_width=True):
            st.session_state.page = "upload"
            st.rerun()
    with qa2:
        if st.button("📊 ATS Analysis", use_container_width=True):
            st.session_state.page = "ats"
            st.rerun()
    with qa3:
        if st.button("🎯 Job Prediction", use_container_width=True):
            st.session_state.page = "prediction"
            st.rerun()
    with qa4:
        if st.button("🤖 AI Chatbot", use_container_width=True):
            st.session_state.page = "chatbot"
            st.rerun()

    st.markdown("<hr style='border-color:rgba(108,99,255,0.15); margin:24px 0;'>", unsafe_allow_html=True)

    # Recent resumes
    st.markdown("<h3 style='color:#e8eaf6;'>📋 Recent Resume Uploads</h3>", unsafe_allow_html=True)

    if not resumes:
        st.markdown("""
        <div style="background:#161829; border:2px dashed rgba(108,99,255,0.3);
                    border-radius:14px; padding:40px; text-align:center;">
            <div style="font-size:3rem;">📂</div>
            <h3 style="color:#9fa8da;">No resumes uploaded yet</h3>
            <p style="color:#4a5270;">Upload your first resume to get started!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📤 Upload Your First Resume", use_container_width=True):
            st.session_state.page = "upload"
            st.rerun()
    else:
        for r in resumes[:5]:
            ats = r["ats_score"] or 0
            cat = r["ats_category"] or "N/A"
            cat_color = {
                "Excellent": "#00d4aa", "Good": "#6c63ff",
                "Average": "#ffd700", "Poor": "#ff6b6b"
            }.get(cat, "#9fa8da")
            role = r["predicted_role"] or "Unknown"
            fname = r["filename"] or "resume"
            date = str(r["uploaded_at"])[:10]

            # FIXED: Using st.container with nested columns to replace broken flexbox CSS
            with st.container():
                st.markdown(f"""
                <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                            border-radius:12px; padding:16px; margin:4px 0;">
                    <table style="width:100%; border:none; border-collapse:collapse;">
                        <tr>
                            <td style="text-align:left; border:none; padding:0;">
                                <div style="font-weight:600; color:#e8eaf6; font-size:1rem;">📄 {fname}</div>
                                <div style="color:#9fa8da; font-size:0.8rem; margin-top:4px;">
                                    🎯 {role} &nbsp;|&nbsp; 📅 {date}
                                </div>
                            </td>
                            <td style="text-align:right; width:80px; border:none; padding:0;">
                                <div style="font-size:1.5rem; font-weight:700; color:#6c63ff; line-height:1.1;">{ats:.0f}</div>
                                <div style="font-size:0.75rem; color:{cat_color}; font-weight:600; margin-top:2px;">{cat}</div>
                            </td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)

    # Getting started guide
    if not resumes:
        st.markdown("<h3 style='color:#e8eaf6; margin-top:24px;'>🗺️ Getting Started</h3>", unsafe_allow_html=True)
        steps = [
            ("1", "Upload Resume", "Go to Upload Resume and upload your PDF or DOCX", "📤"),
            ("2", "Get ATS Score", "Our AI calculates your ATS score instantly", "📊"),
            ("3", "See Job Match", "Get predicted job roles with confidence scores", "🎯"),
            ("4", "Fix Gaps", "View missing skills and improvement suggestions", "🛠️"),
            ("5", "Chat with AI", "Ask the AI chatbot for career guidance", "🤖"),
        ]
        cols = st.columns(5)
        for i, (num, title, desc, icon) in enumerate(steps):
            with cols[i]:
                st.markdown(f"""
                <div style="background:#161829; border:1px solid rgba(108,99,255,0.2);
                            border-radius:12px; padding:16px; text-align:center; height:160px;">
                    <div style="font-size:1.8rem;">{icon}</div>
                    <div style="background:linear-gradient(135deg,#6c63ff,#00d4aa);
                                -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                                font-weight:700; font-size:1.2rem;">Step {num}</div>
                    <div style="font-weight:600; color:#e8eaf6; font-size:0.85rem;">{title}</div>
                    <div style="color:#9fa8da; font-size:0.75rem; margin-top:4px;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
