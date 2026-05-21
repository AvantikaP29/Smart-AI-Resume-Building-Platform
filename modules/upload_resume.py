"""
Upload Resume Page
Handles PDF/DOCX resume upload, text extraction, NLP parsing,
ATS scoring, job role prediction, and saving results to DB.
"""

import streamlit as st
import os
import time
from utils.resume_parser import parse_resume
from utils.ats_engine import calculate_ats_score
from utils.prediction_engine import predict_role
from utils.skill_gap import analyze_skill_gap
from utils.suggestions import generate_suggestions
from utils.database import save_resume

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def progress_step(bar, status_text, pct, message):
    bar.progress(pct)
    status_text.markdown(
        f"<p style='color:#9fa8da; font-size:0.85rem; text-align:center;'>{message}</p>",
        unsafe_allow_html=True
    )
    time.sleep(0.4)


def ats_color(score):
    if score >= 80:
        return "#00d4aa"
    elif score >= 65:
        return "#6c63ff"
    elif score >= 45:
        return "#ffd700"
    return "#ff6b6b"


def category_badge(cat):
    colors = {
        "Excellent": ("#00d4aa", "rgba(0,212,170,0.12)"),
        "Good":      ("#6c63ff", "rgba(108,99,255,0.12)"),
        "Average":   ("#ffd700", "rgba(255,215,0,0.12)"),
        "Poor":      ("#ff6b6b", "rgba(255,107,107,0.12)"),
    }
    fg, bg = colors.get(cat, ("#9fa8da", "rgba(159,168,218,0.12)"))
    return f"""
    <span style="background:{bg}; color:{fg}; border:1px solid {fg};
                 padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:700;">
        {cat}
    </span>"""


def skill_pill(skill, color="#6c63ff", bg="rgba(108,99,255,0.12)"):
    return (
        f"<span style='background:{bg}; color:{color}; border:1px solid {color}; "
        f"padding:3px 10px; border-radius:20px; font-size:0.78rem; "
        f"margin:3px; display:inline-block;'>{skill}</span>"
    )


# ─── MAIN PAGE ────────────────────────────────────────────────────────────────

def show():
    st.markdown("""
    <h1 style='color:#e8eaf6; margin-bottom:4px;'>📤 Upload Resume</h1>
    <p style='color:#9fa8da; margin-bottom:24px;'>
        Upload your PDF or DOCX resume and get instant AI-powered analysis.
    </p>
    """, unsafe_allow_html=True)

    # ── Upload Zone ────────────────────────────────────────────────────────
    upload_col, info_col = st.columns([1.6, 1])

    with upload_col:
        st.markdown("""
        <div style="background:#161829; border:2px dashed rgba(108,99,255,0.4);
                    border-radius:16px; padding:30px 24px; text-align:center; margin-bottom:16px;">
            <div style="font-size:2.5rem;">📁</div>
            <div style="color:#e8eaf6; font-weight:600; font-size:1.05rem;">
                Drop your resume here or click to browse
            </div>
            <div style="color:#9fa8da; font-size:0.82rem; margin-top:6px;">
                Supported formats: <strong>PDF</strong> and <strong>DOCX</strong> &nbsp;|&nbsp; Max size: 5 MB
            </div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            label="Upload Resume",
            type=["pdf", "docx"],
            label_visibility="collapsed"
        )

    with info_col:
        st.markdown("""
        <div style="background:#161829; border:1px solid rgba(108,99,255,0.2);
                    border-radius:14px; padding:20px; height:100%;">
            <h4 style="color:#6c63ff; margin-bottom:12px;">ℹ️ What We Analyse</h4>
            <ul style="color:#9fa8da; font-size:0.85rem; line-height:2; padding-left:18px;">
                <li>Skills & Technologies</li>
                <li>Education & Certifications</li>
                <li>Years of Experience</li>
                <li>Contact & Profile Links</li>
                <li>ATS Score (out of 100)</li>
                <li>Predicted Job Role</li>
                <li>Skill Gap & Missing Skills</li>
                <li>Resume Improvement Tips</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # ── Analyse Button ─────────────────────────────────────────────────────
    if uploaded_file:
        file_size_kb = round(uploaded_file.size / 1024, 1)
        st.markdown(f"""
        <div style="background:rgba(0,212,170,0.08); border:1px solid rgba(0,212,170,0.3);
                    border-radius:10px; padding:12px 18px; margin:12px 0; display:flex;
                    align-items:center; gap:12px;">
            <span style="font-size:1.5rem;">✅</span>
            <div>
                <div style="color:#00d4aa; font-weight:600;">{uploaded_file.name}</div>
                <div style="color:#9fa8da; font-size:0.8rem;">
                    {file_size_kb} KB &nbsp;|&nbsp; {uploaded_file.type}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀  Analyse Resume Now", use_container_width=True):
            run_analysis(uploaded_file)

    # ── Show previous results if available ────────────────────────────────
    if st.session_state.get("resume_parsed") and not uploaded_file:
        st.markdown("""
        <div style="background:rgba(108,99,255,0.08); border:1px solid rgba(108,99,255,0.3);
                    border-radius:10px; padding:12px 18px; margin:12px 0;">
            <span style="color:#9fa8da; font-size:0.85rem;">
                💡 Showing results from your last analysis.
                Upload a new file to re-analyse.
            </span>
        </div>
        """, unsafe_allow_html=True)
        render_results()


# ─── ANALYSIS PIPELINE ────────────────────────────────────────────────────────

def run_analysis(uploaded_file):
    file_bytes = uploaded_file.read()
    filename   = uploaded_file.name

    # Save file to disk
    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # Progress UI
    st.markdown("<br>", unsafe_allow_html=True)
    progress_container = st.container()
    with progress_container:
        bar         = st.progress(0)
        status_text = st.empty()

        progress_step(bar, status_text,  5, "📖 Reading resume file...")
        parsed = parse_resume(file_bytes, filename)

        if "error" in parsed:
            bar.empty(); status_text.empty()
            st.error(f"❌ {parsed['error']}")
            return

        progress_step(bar, status_text, 30, "🧠 Running NLP extraction...")
        progress_step(bar, status_text, 50, "📊 Calculating ATS score...")
        ats_report = calculate_ats_score(parsed)

        progress_step(bar, status_text, 65, "🎯 Predicting best job role...")
        prediction = predict_role(parsed["raw_text"], parsed["skills"])

        progress_step(bar, status_text, 80, "🔍 Analysing skill gaps...")
        skill_gap  = analyze_skill_gap(parsed["skills"], prediction["predicted_role"])

        progress_step(bar, status_text, 92, "💡 Generating suggestions...")
        suggestions = generate_suggestions(parsed, ats_report, prediction["predicted_role"])

        progress_step(bar, status_text, 100, "✅ Analysis complete!")
        time.sleep(0.3)
        bar.empty(); status_text.empty()

    # Persist to DB
    save_resume(
        user_id        = st.session_state.user["id"],
        filename       = filename,
        resume_text    = parsed["raw_text"],
        ats_score      = ats_report["total_score"],
        ats_category   = ats_report["category"],
        predicted_role = prediction["predicted_role"],
        confidence_score = prediction["confidence"],
        skills_found   = parsed["skills"],
        missing_skills = skill_gap["missing_skills"],
    )

    # Store in session
    st.session_state.resume_parsed  = parsed
    st.session_state.ats_report     = ats_report
    st.session_state.prediction     = prediction
    st.session_state.skill_gap      = skill_gap
    st.session_state.suggestions    = suggestions

    st.success("✅ Resume analysed and saved successfully!")
    st.rerun()


# ─── RESULTS RENDERER ─────────────────────────────────────────────────────────

def render_results():
    parsed      = st.session_state.resume_parsed
    ats_report  = st.session_state.ats_report
    prediction  = st.session_state.prediction
    skill_gap   = st.session_state.get("skill_gap", {})
    suggestions = st.session_state.get("suggestions", [])

    st.markdown("<hr style='border-color:rgba(108,99,255,0.15); margin:28px 0;'>",
                unsafe_allow_html=True)
    st.markdown("<h2 style='color:#e8eaf6;'>📋 Analysis Results</h2>", unsafe_allow_html=True)

    tabs = st.tabs([
        "👤 Profile",
        "📊 ATS Score",
        "🎯 Job Prediction",
        "🔍 Skill Gap",
        "💡 Suggestions",
        "📄 Raw Text",
    ])

    # ── Tab 1 : Profile ───────────────────────────────────────────────────
    with tabs[0]:
        render_profile_tab(parsed)

    # ── Tab 2 : ATS Score ─────────────────────────────────────────────────
    with tabs[1]:
        render_ats_tab(ats_report)

    # ── Tab 3 : Job Prediction ────────────────────────────────────────────
    with tabs[2]:
        render_prediction_tab(prediction)

    # ── Tab 4 : Skill Gap ─────────────────────────────────────────────────
    with tabs[3]:
        render_skill_gap_tab(skill_gap)

    # ── Tab 5 : Suggestions ───────────────────────────────────────────────
    with tabs[4]:
        render_suggestions_tab(suggestions)

    # ── Tab 6 : Raw Text ──────────────────────────────────────────────────
    with tabs[5]:
        render_raw_text_tab(parsed)


# ─── TAB RENDERERS ────────────────────────────────────────────────────────────

def render_profile_tab(parsed):
    st.markdown("<h3 style='color:#e8eaf6;'>👤 Extracted Profile</h3>", unsafe_allow_html=True)

    # Top row – contact info cards
    c1, c2, c3, c4 = st.columns(4)
    def info_card(col, icon, label, value, color="#6c63ff"):
        with col:
            st.markdown(f"""
            <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                        border-radius:12px; padding:16px; text-align:center;">
                <div style="font-size:1.6rem;">{icon}</div>
                <div style="color:#9fa8da; font-size:0.72rem; margin:4px 0;">{label}</div>
                <div style="color:{color}; font-weight:600; font-size:0.85rem;
                            word-break:break-all;">{value or '—'}</div>
            </div>
            """, unsafe_allow_html=True)

    info_card(c1, "👤", "Name",  parsed.get("name"),  "#e8eaf6")
    info_card(c2, "📧", "Email", parsed.get("email"), "#00d4aa")
    info_card(c3, "📞", "Phone", parsed.get("phone"), "#6c63ff")
    info_card(c4, "⏱️", "Experience",
              f"{parsed.get('experience_years')} yrs" if parsed.get("experience_years") else None,
              "#ffd700")

    st.markdown("<br>", unsafe_allow_html=True)

    # Links
    lk_col, gh_col = st.columns(2)
    with lk_col:
        lk = parsed.get("linkedin")
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid rgba(0,119,181,0.4);
                    border-radius:10px; padding:14px; display:flex; align-items:center; gap:12px;">
            <span style="font-size:1.4rem;">🔗</span>
            <div>
                <div style="color:#9fa8da; font-size:0.75rem;">LinkedIn</div>
                <div style="color:{'#0077B5' if lk else '#4a5270'}; font-size:0.85rem;">
                    {lk if lk else 'Not found – add your LinkedIn URL'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with gh_col:
        gh = parsed.get("github")
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid rgba(255,255,255,0.15);
                    border-radius:10px; padding:14px; display:flex; align-items:center; gap:12px;">
            <span style="font-size:1.4rem;">💻</span>
            <div>
                <div style="color:#9fa8da; font-size:0.75rem;">GitHub</div>
                <div style="color:{'#e8eaf6' if gh else '#4a5270'}; font-size:0.85rem;">
                    {gh if gh else 'Not found – add your GitHub URL'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    sk_col, ed_col, cert_col = st.columns(3)

    # Skills
    with sk_col:
        skills = parsed.get("skills", [])
        st.markdown(f"<h4 style='color:#6c63ff;'>🛠️ Skills ({len(skills)})</h4>",
                    unsafe_allow_html=True)
        if skills:
            pills = "".join(skill_pill(s) for s in skills)
            st.markdown(f"<div style='line-height:2;'>{pills}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#4a5270;'>No skills detected.</p>", unsafe_allow_html=True)

    # Education
    with ed_col:
        edu = parsed.get("education", [])
        st.markdown(f"<h4 style='color:#00d4aa;'>🎓 Education</h4>", unsafe_allow_html=True)
        if edu:
            for e in edu:
                st.markdown(
                    f"<div style='background:rgba(0,212,170,0.1); color:#00d4aa; "
                    f"border:1px solid rgba(0,212,170,0.3); border-radius:8px; "
                    f"padding:6px 12px; margin:4px 0; font-size:0.85rem;'>{e}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<p style='color:#4a5270;'>No education info detected.</p>",
                        unsafe_allow_html=True)

    # Certifications
    with cert_col:
        certs = parsed.get("certifications", [])
        st.markdown(f"<h4 style='color:#ffd700;'>🏆 Certifications</h4>", unsafe_allow_html=True)
        if certs:
            for c in certs:
                st.markdown(
                    f"<div style='background:rgba(255,215,0,0.1); color:#ffd700; "
                    f"border:1px solid rgba(255,215,0,0.3); border-radius:8px; "
                    f"padding:6px 12px; margin:4px 0; font-size:0.85rem;'>{c}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<p style='color:#4a5270;'>No certifications detected.</p>",
                        unsafe_allow_html=True)


def render_ats_tab(ats_report):
    score = ats_report["total_score"]
    cat   = ats_report["category"]
    color = ats_color(score)

    st.markdown("<h3 style='color:#e8eaf6;'>📊 ATS Score Report</h3>", unsafe_allow_html=True)

    # Big score display
    left, right = st.columns([1, 1.6])
    with left:
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid {color}40;
                    border-radius:20px; padding:32px; text-align:center;">
            <div style="font-size:5rem; font-weight:800; color:{color}; line-height:1;">
                {score:.0f}
            </div>
            <div style="color:#9fa8da; font-size:0.85rem;">out of 100</div>
            <div style="margin-top:14px;">{category_badge(cat)}</div>
            <div style="margin-top:18px;">
                <div style="background:rgba(255,255,255,0.08); border-radius:8px;
                            height:10px; overflow:hidden;">
                    <div style="background:{color}; width:{score}%; height:100%;
                                border-radius:8px; transition:width 1s;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("<h4 style='color:#e8eaf6; margin-bottom:12px;'>Score Breakdown</h4>",
                    unsafe_allow_html=True)
        breakdown = ats_report.get("breakdown", {})
        for criterion, data in breakdown.items():
            s  = data["score"]
            w  = data["weight"]
            note = data.get("note", "")
            bar_color = ats_color(s)
            st.markdown(f"""
            <div style="margin-bottom:14px;">
                <div style="display:flex; justify-content:space-between;
                            align-items:center; margin-bottom:4px;">
                    <span style="color:#e8eaf6; font-size:0.85rem; font-weight:600;">
                        {criterion}
                    </span>
                    <span style="color:{bar_color}; font-weight:700; font-size:0.9rem;">
                        {s:.0f}/100
                        <span style="color:#4a5270; font-weight:400; font-size:0.75rem;">
                            (weight {w}%)
                        </span>
                    </span>
                </div>
                <div style="background:rgba(255,255,255,0.08); border-radius:6px;
                            height:8px; overflow:hidden;">
                    <div style="background:{bar_color}; width:{s}%; height:100%;
                                border-radius:6px;"></div>
                </div>
                <div style="color:#9fa8da; font-size:0.75rem; margin-top:3px;">{note}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Missing keywords
    missing_kw = ats_report.get("missing_keywords", [])
    if missing_kw:
        st.markdown("<h4 style='color:#ff6b6b;'>🔑 Missing ATS Keywords</h4>",
                    unsafe_allow_html=True)
        pills = "".join(
            skill_pill(k, color="#ff6b6b", bg="rgba(255,107,107,0.1)") for k in missing_kw
        )
        st.markdown(f"<div style='line-height:2;'>{pills}</div>", unsafe_allow_html=True)


def render_prediction_tab(prediction):
    st.markdown("<h3 style='color:#e8eaf6;'>🎯 Job Role Prediction</h3>", unsafe_allow_html=True)

    role       = prediction["predicted_role"]
    confidence = prediction["confidence"]
    icon       = prediction.get("icon", "💼")
    desc       = prediction.get("description", "")
    conf_color = "#00d4aa" if confidence >= 70 else "#ffd700" if confidence >= 50 else "#ff6b6b"

    # Primary prediction card
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, rgba(108,99,255,0.15), rgba(0,212,170,0.1));
                border:1px solid rgba(108,99,255,0.4); border-radius:18px;
                padding:28px 32px; margin-bottom:24px;">
        <div style="display:flex; align-items:center; gap:20px;">
            <div style="font-size:3.5rem;">{icon}</div>
            <div style="flex:1;">
                <div style="font-size:1.6rem; font-weight:700; color:#e8eaf6;">{role}</div>
                <div style="color:#9fa8da; font-size:0.9rem; margin-top:4px;">{desc}</div>
                <div style="margin-top:14px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span style="color:#9fa8da; font-size:0.82rem;">AI Confidence</span>
                        <span style="color:{conf_color}; font-weight:700;">{confidence:.1f}%</span>
                    </div>
                    <div style="background:rgba(255,255,255,0.1); border-radius:8px;
                                height:10px; overflow:hidden;">
                        <div style="background:linear-gradient(90deg,#6c63ff,#00d4aa);
                                    width:{min(confidence,100)}%; height:100%;
                                    border-radius:8px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Matched keywords
    matched = prediction.get("matched_keywords", [])
    if matched:
        st.markdown("<h4 style='color:#00d4aa;'>✅ Matched Keywords</h4>",
                    unsafe_allow_html=True)
        pills = "".join(
            skill_pill(k, color="#00d4aa", bg="rgba(0,212,170,0.1)") for k in matched[:20]
        )
        st.markdown(f"<div style='line-height:2; margin-bottom:20px;'>{pills}</div>",
                    unsafe_allow_html=True)

    # Alternative roles
    alts = prediction.get("alternatives", [])
    if alts:
        st.markdown("<h4 style='color:#e8eaf6;'>🔄 Alternative Role Matches</h4>",
                    unsafe_allow_html=True)
        for alt in alts:
            c = alt["confidence"]
            c_color = "#ffd700" if c >= 40 else "#9fa8da"
            st.markdown(f"""
            <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                        border-radius:10px; padding:14px 18px; margin:6px 0;
                        display:flex; align-items:center; justify-content:space-between;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <span style="font-size:1.3rem;">{alt.get('icon','💼')}</span>
                    <span style="color:#e8eaf6; font-weight:600;">{alt['role']}</span>
                </div>
                <div style="text-align:right;">
                    <span style="color:{c_color}; font-weight:700;">{c:.1f}%</span>
                    <div style="background:rgba(255,255,255,0.08); border-radius:4px;
                                height:5px; width:100px; margin-top:4px; overflow:hidden;">
                        <div style="background:{c_color}; width:{min(c,100)}%;
                                    height:100%; border-radius:4px;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_skill_gap_tab(skill_gap):
    if not skill_gap:
        st.info("Run an analysis first.")
        return

    st.markdown("<h3 style='color:#e8eaf6;'>🔍 Skill Gap Analysis</h3>", unsafe_allow_html=True)

    match_pct  = skill_gap.get("match_percentage", 0)
    readiness  = skill_gap.get("readiness_level", {})
    r_color    = readiness.get("color", "#9fa8da")
    r_level    = readiness.get("level", "")
    r_msg      = readiness.get("message", "")
    r_emoji    = readiness.get("emoji", "")
    existing   = skill_gap.get("existing_skills", [])
    missing    = skill_gap.get("missing_skills", [])
    critical   = skill_gap.get("critical_missing", [])
    role       = skill_gap.get("role", "")
    resources  = skill_gap.get("learning_resources", [])

    # Readiness card
    st.markdown(f"""
    <div style="background:rgba({_hex_to_rgb(r_color)},0.1); border:1px solid {r_color}50;
                border-radius:14px; padding:20px 24px; margin-bottom:20px;
                display:flex; align-items:center; gap:20px;">
        <div style="font-size:2.5rem;">{r_emoji}</div>
        <div>
            <div style="font-size:1.1rem; font-weight:700; color:{r_color};">{r_level}</div>
            <div style="color:#9fa8da; font-size:0.85rem;">{r_msg}</div>
        </div>
        <div style="margin-left:auto; text-align:right;">
            <div style="font-size:2rem; font-weight:800; color:{r_color};">{match_pct:.0f}%</div>
            <div style="color:#9fa8da; font-size:0.75rem;">skill match for {role}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Match bar
    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:#9fa8da; font-size:0.82rem;">
                {len(existing)} matched / {skill_gap.get('total_required',0)} required
            </span>
            <span style="color:{r_color}; font-weight:700;">{match_pct:.0f}%</span>
        </div>
        <div style="background:rgba(255,255,255,0.08); border-radius:8px; height:12px; overflow:hidden;">
            <div style="background:linear-gradient(90deg,#6c63ff,#00d4aa);
                        width:{match_pct}%; height:100%; border-radius:8px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Skills columns
    have_col, miss_col = st.columns(2)

    with have_col:
        st.markdown(f"<h4 style='color:#00d4aa;'>✅ Skills You Have ({len(existing)})</h4>",
                    unsafe_allow_html=True)
        if existing:
            pills = "".join(skill_pill(s, "#00d4aa", "rgba(0,212,170,0.1)") for s in existing)
            st.markdown(f"<div style='line-height:2.2;'>{pills}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#4a5270;'>No matching skills found.</p>",
                        unsafe_allow_html=True)

    with miss_col:
        st.markdown(f"<h4 style='color:#ff6b6b;'>❌ Missing Skills ({len(missing)})</h4>",
                    unsafe_allow_html=True)
        if critical:
            st.markdown("<p style='color:#ff6b6b; font-size:0.8rem;'>🔴 Critical:</p>",
                        unsafe_allow_html=True)
            pills = "".join(skill_pill(s, "#ff6b6b", "rgba(255,107,107,0.1)") for s in critical)
            st.markdown(f"<div style='line-height:2.2; margin-bottom:8px;'>{pills}</div>",
                        unsafe_allow_html=True)
        others = [s for s in missing if s not in critical]
        if others:
            pills = "".join(skill_pill(s, "#ffd700", "rgba(255,215,0,0.1)") for s in others[:12])
            st.markdown(f"<div style='line-height:2.2;'>{pills}</div>", unsafe_allow_html=True)

    # Learning resources
    if resources:
        st.markdown("<br><h4 style='color:#6c63ff;'>📚 Recommended Learning Resources</h4>",
                    unsafe_allow_html=True)
        res_cols = st.columns(2)
        for i, res in enumerate(resources):
            with res_cols[i % 2]:
                st.markdown(f"""
                <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                            border-radius:10px; padding:14px; margin:6px 0;">
                    <div style="color:#e8eaf6; font-weight:600; font-size:0.88rem;">
                        🎯 {res['skill'].title()}
                    </div>
                    <div style="color:#9fa8da; font-size:0.8rem; margin:4px 0;">
                        📖 {res['course']}
                    </div>
                    <div style="color:#6c63ff; font-size:0.78rem;">
                        🔗 <a href="{res['url']}" target="_blank"
                             style="color:#6c63ff;">{res['platform']}</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)


def render_suggestions_tab(suggestions):
    st.markdown("<h3 style='color:#e8eaf6;'>💡 Resume Improvement Suggestions</h3>",
                unsafe_allow_html=True)

    if not suggestions:
        st.success("✅ Your resume looks great! No major improvements needed.")
        return

    priority_colors = {
        "Critical": ("#ff6b6b", "rgba(255,107,107,0.1)"),
        "High":     ("#ffd700", "rgba(255,215,0,0.1)"),
        "Medium":   ("#6c63ff", "rgba(108,99,255,0.1)"),
        "Low":      ("#9fa8da", "rgba(159,168,218,0.1)"),
    }

    for sug in suggestions:
        pri   = sug.get("priority", "Medium")
        color, bg = priority_colors.get(pri, ("#9fa8da", "rgba(159,168,218,0.1)"))
        st.markdown(f"""
        <div style="background:{bg}; border-left:4px solid {color};
                    border-radius:0 10px 10px 0; padding:14px 18px; margin:8px 0;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                <span style="font-size:1.2rem;">{sug.get('icon','💡')}</span>
                <span style="color:#e8eaf6; font-weight:700; font-size:0.9rem;">
                    {sug.get('title','')}
                </span>
                <span style="background:{color}22; color:{color}; border:1px solid {color};
                             padding:2px 8px; border-radius:10px; font-size:0.72rem;
                             font-weight:700; margin-left:auto;">
                    {pri}
                </span>
            </div>
            <div style="color:#9fa8da; font-size:0.82rem; padding-left:34px;">
                {sug.get('detail','')}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_raw_text_tab(parsed):
    st.markdown("<h3 style='color:#e8eaf6;'>📄 Extracted Resume Text</h3>",
                unsafe_allow_html=True)

    wc = parsed.get("word_count", 0)
    cc = parsed.get("char_count", 0)
    m1, m2 = st.columns(2)
    m1.metric("📝 Word Count", wc)
    m2.metric("🔤 Character Count", cc)

    st.markdown("<br>", unsafe_allow_html=True)
    raw = parsed.get("raw_text", "")
    st.markdown(f"""
    <div style="background:#0d0f1a; border:1px solid rgba(108,99,255,0.2);
                border-radius:12px; padding:20px; max-height:500px; overflow-y:auto;
                font-family:'JetBrains Mono', monospace; font-size:0.82rem;
                color:#9fa8da; line-height:1.8; white-space:pre-wrap;">
{raw[:5000]}{'...[truncated]' if len(raw) > 5000 else ''}
    </div>
    """, unsafe_allow_html=True)


# ─── UTILITY ──────────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> str:
    """Convert #rrggbb to 'r,g,b' string for rgba()."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"{r},{g},{b}"
    return "108,99,255"
