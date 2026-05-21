"""
AI Chatbot Page
Career guidance chatbot powered by Google Gemini API.
Features: resume-aware context, chat history, quick prompts,
conversation memory, and fallback rule-based responses.
"""

import streamlit as st
import time
from utils.chatbot_utils import get_gemini_response, get_fallback_response
from utils.database import save_chat_message, get_chat_history, clear_chat_history

# ─── QUICK PROMPT CATEGORIES ──────────────────────────────────────────────────

QUICK_PROMPTS = {
    "📄 Resume Help": [
        "How can I improve my resume summary section?",
        "What action verbs should I use in my resume?",
        "How do I write measurable achievements?",
    ],
    "🎯 Career Advice": [
        "What skills should I learn for my predicted role?",
        "How do I transition into a data science career?",
        "How do I negotiate a better salary offer?",
    ],
    "🎤 Interview Prep": [
        "What are common interview questions for my role?",
        "How do I answer 'Tell me about yourself'?",
        "Tips for handling behavioral interview questions?",
    ],
}

GREETING_MESSAGES = [
    "Hello! I'm **HireSense AI** 🤖 — your personal career coach.",
    "I can help you with resume improvement, career roadmaps, interview prep, and more.",
    "Type your question below or pick a quick prompt to get started! 🚀",
]


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def build_resume_context() -> dict:
    parsed = st.session_state.get("resume_parsed")
    ats_report = st.session_state.get("ats_report")
    prediction = st.session_state.get("prediction")

    if not parsed:
        return {}

    return {
        "predicted_role": prediction.get("predicted_role") if prediction else "Unknown",
        "ats_score": ats_report.get("total_score", 0) if ats_report else 0,
        "skills": parsed.get("skills", []),
        "experience_years": parsed.get("experience_years"),
    }


def format_time() -> str:
    return time.strftime("%H:%M")


# ─── MAIN PAGE ────────────────────────────────────────────────────────────────

def show():
    user = st.session_state.user

    if not st.session_state.get("chat_history"):
        st.session_state.chat_history = get_chat_history(user["id"], limit=30)

    st.markdown("""
    <h1 style='color:#e8eaf6; margin-bottom:4px;'>🤖 HireSense AI Assistant</h1>
    <p style='color:#9fa8da; margin-bottom:24px;'>Get personalized career guidance and resume tips.</p>
    """, unsafe_allow_html=True)

    chat_col, panel_col = st.columns([1.7, 1])

    with panel_col:
        render_side_panel(user)

    with chat_col:
        render_chat_window(user)


# ─── SIDE PANEL ───────────────────────────────────────────────────────────────

def render_side_panel(user):
    resume_ctx = build_resume_context()
    if resume_ctx:
        role = resume_ctx.get("predicted_role", "—")
        ats = resume_ctx.get("ats_score", 0)
        st.markdown(f"""
        <div style="background:rgba(108,99,255,0.1); border:1px solid #6c63ff; border-radius:14px; padding:15px;">
            <div style="color:#6c63ff; font-weight:700; font-size:0.8rem; margin-bottom:10px;">HIRESENSE CONTEXT</div>
            <p style="margin:0; font-size:0.85rem; color:#e8eaf6;"><b>Role:</b> {role}</p>
            <p style="margin:0; font-size:0.85rem; color:#e8eaf6;"><b>ATS Score:</b> {ats:.0f}/100</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ⚡ Quick Prompts")
    selected_cat = st.selectbox("Category", list(QUICK_PROMPTS.keys()))
    for prompt in QUICK_PROMPTS[selected_cat]:
        if st.button(prompt, use_container_width=True, key=f"qp_{prompt}"):
            send_message(prompt, user["id"])
            st.rerun()

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        clear_chat_history(user["id"])
        st.session_state.chat_history = []
        st.rerun()


# ─── CHAT WINDOW ──────────────────────────────────────────────────────────────

def render_chat_window(user):
    chat_history = st.session_state.get("chat_history", [])

    # Container for messages
    chat_container = st.container(height=500)

    with chat_container:
        if not chat_history:
            for msg in GREETING_MESSAGES:
                render_message("assistant", msg)
        else:
            for msg in chat_history:
                render_message(msg["role"], msg.get("content", msg.get("message", "")))

    # FIXED INPUT: This uses st.chat_input which clears itself to stop loops
    if prompt := st.chat_input("Ask HireSense AI anything..."):
        send_message(prompt, user["id"])
        st.rerun()


# ─── MESSAGE RENDERER ─────────────────────────────────────────────────────────

def render_message(role: str, content: str):
    is_user = role == "user"
    align = "flex-end" if is_user else "flex-start"
    bg = "linear-gradient(135deg,#6c63ff,#4f46e5)" if is_user else "#1e2035"
    color = "white" if is_user else "#e8eaf6"
    label = "You" if is_user else "HireSense AI"
    avatar = "🧑" if is_user else "🤖"

    st.markdown(f"""
    <div style="display:flex; justify-content:{align}; margin:10px 0;">
        <div style="max-width:80%; background:{bg}; color:{color}; padding:12px; border-radius:15px;">
            <small style="opacity:0.7;">{avatar} {label}</small><br>{content}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── SEND MESSAGE ─────────────────────────────────────────────────────────────

def send_message(user_text: str, user_id: int):
    if not user_text.strip():
        return

    # Check for accidental double-submissions
    if st.session_state.chat_history and st.session_state.chat_history[-1].get("content") == user_text:
        return

    # User Message
    st.session_state.chat_history.append({"role": "user", "content": user_text})
    save_chat_message(user_id, "user", user_text)

    # Bot Logic
    api_key = st.session_state.get("gemini_api_key", "")
    resume_ctx = build_resume_context()

    # Prepare history for AI
    api_messages = [{"role": m["role"], "content": m.get("content", m.get("message", ""))} for m in
                    st.session_state.chat_history[-10:]]

    if api_key:
        response = get_gemini_response(api_messages, api_key, resume_ctx)
    else:
        response = get_fallback_response(user_text) or "Please add an API key in settings."

    # Assistant Message
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    save_chat_message(user_id, "assistant", response)
