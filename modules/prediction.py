"""
Job Role Prediction Page
Displays AI-predicted job roles, confidence scores, role requirements,
skill match, salary info, learning roadmap, and career pathway.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.prediction_engine import predict_role, get_role_requirements, JOB_ROLES
from utils.skill_gap import analyze_skill_gap
from utils.database import get_user_resumes


# ─── PLOTLY THEME ─────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk, sans-serif", color="#9fa8da"),
    margin=dict(l=20, r=20, t=40, b=20),
)

ROLE_COLORS = [
    "#6c63ff", "#00d4aa", "#ffd700", "#ff6b6b",
    "#a78bfa", "#34d399", "#f472b6", "#60a5fa",
]


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def skill_pill(text, color="#6c63ff", bg="rgba(108,99,255,0.12)"):
    return (
        f"<span style='background:{bg}; color:{color}; border:1px solid {color}; "
        f"padding:3px 11px; border-radius:20px; font-size:0.78rem; "
        f"margin:3px; display:inline-block;'>{text}</span>"
    )


def conf_color(c):
    if c >= 70: return "#00d4aa"
    elif c >= 50: return "#6c63ff"
    elif c >= 35: return "#ffd700"
    return "#ff6b6b"


def conf_label(c):
    if c >= 70: return ("High Match", "#00d4aa")
    elif c >= 50: return ("Good Match", "#6c63ff")
    elif c >= 35: return ("Partial Match", "#ffd700")
    return ("Low Match", "#ff6b6b")


def kpi_card(col, label, value, color="#6c63ff", icon="📊"):
    with col:
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                    border-radius:12px; padding:16px; text-align:center;">
            <div style="font-size:1.4rem;">{icon}</div>
            <div style="font-size:1.35rem; font-weight:800; color:{color}; line-height:1.2;">
                {value}
            </div>
            <div style="color:#9fa8da; font-size:0.75rem; margin-top:4px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)


# ─── CHARTS ───────────────────────────────────────────────────────────────────

def make_confidence_bar(predictions: list) -> go.Figure:
    roles = [p["role"] for p in predictions]
    confs = [p["confidence"] for p in predictions]
    colors = [conf_color(c) for c in confs]

    fig = go.Figure(go.Bar(
        x=confs,
        y=roles,
        orientation="h",
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=[f"{c:.1f}%" for c in confs],
        textposition="outside",
        textfont=dict(color="#e8eaf6", size=12),
    ))
    fig.add_vline(x=50, line_dash="dot", line_color="#ffd700",
                  annotation_text="50% threshold",
                  annotation_font_color="#9fa8da")
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(range=[0, 115], gridcolor="#2a2d45", title="Confidence %"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", autorange="reversed"),
        height=max(280, len(predictions) * 55),
    )
    return fig


def make_skill_match_gauge(match_pct: float, role: str) -> go.Figure:
    color = conf_color(match_pct)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=match_pct,
        title={"text": f"Skill Match<br><span style='font-size:0.8em;color:#9fa8da;'>{role}</span>",
               "font": {"size": 14, "color": "#9fa8da"}},
        number={"font": {"size": 44, "color": color}, "suffix": "%"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1,
                     "tickcolor": "#4a5270", "tickfont": {"color": "#9fa8da"}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "rgba(30,32,53,0.8)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "rgba(255,107,107,0.15)"},
                {"range": [40, 65], "color": "rgba(255,215,0,0.12)"},
                {"range": [65, 80], "color": "rgba(108,99,255,0.12)"},
                {"range": [80,100], "color": "rgba(0,212,170,0.12)"},
            ],
        },
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=260)
    return fig


def make_roles_radar(all_preds: list) -> go.Figure:
    roles = [p["role"] for p in all_preds[:6]]
    confs = [p["confidence"] for p in all_preds[:6]]
    roles += [roles[0]]
    confs += [confs[0]]

    fig = go.Figure(go.Scatterpolar(
        r=confs,
        theta=roles,
        fill="toself",
        fillcolor="rgba(108,99,255,0.15)",
        line=dict(color="#6c63ff", width=2),
        marker=dict(size=7, color="#00d4aa"),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        polar=dict(
            bgcolor="rgba(22,24,41,0.6)",
            radialaxis=dict(visible=True, range=[0, 100],
                            gridcolor="#2a2d45", tickfont={"color": "#9fa8da"}),
            angularaxis=dict(gridcolor="#2a2d45", tickfont={"color": "#e8eaf6", "size": 10}),
        ),
        height=340,
    )
    return fig


def make_skill_donut(existing: list, missing: list) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=["Skills You Have", "Skills to Learn"],
        values=[max(len(existing), 1), max(len(missing), 1)],
        hole=0.6,
        marker=dict(colors=["#00d4aa", "#ff6b6b"],
                    line=dict(color="#161829", width=3)),
        textfont=dict(color="#e8eaf6", size=13),
        hovertemplate="<b>%{label}</b><br>%{value} skills (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=280,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9fa8da")),
        annotations=[dict(
            text=f"<b>{len(existing)}/{len(existing)+len(missing)}</b>",
            x=0.5, y=0.5, font_size=18, font_color="#e8eaf6", showarrow=False
        )],
    )
    return fig


def make_all_roles_bar() -> go.Figure:
    """Static chart showing all supported roles."""
    roles = list(JOB_ROLES.keys())
    colors = ROLE_COLORS[:len(roles)]
    sample_demand = [92, 95, 88, 85, 83, 87, 78, 82]   # illustrative demand index

    fig = go.Figure(go.Bar(
        x=roles,
        y=sample_demand[:len(roles)],
        marker=dict(color=colors, opacity=0.8),
        text=[f"{v}%" for v in sample_demand[:len(roles)]],
        textposition="outside",
        textfont=dict(color="#e8eaf6", size=11),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(tickangle=-25, gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(range=[0, 110], gridcolor="#2a2d45", title="Market Demand Index"),
        height=300,
        title=dict(text="2025 Tech Role Market Demand", font=dict(color="#9fa8da", size=13)),
    )
    return fig


# ─── MAIN PAGE ────────────────────────────────────────────────────────────────

def show():
    st.markdown("""
    <h1 style='color:#e8eaf6; margin-bottom:4px;'>🎯 Job Role Prediction</h1>
    <p style='color:#9fa8da; margin-bottom:28px;'>
        AI-powered job role matching based on your resume skills, experience, and keywords.
    </p>
    """, unsafe_allow_html=True)

    prediction  = st.session_state.get("prediction")
    parsed      = st.session_state.get("resume_parsed")
    skill_gap   = st.session_state.get("skill_gap")
    user        = st.session_state.user
    all_resumes = get_user_resumes(user["id"])

    # ── No data state ─────────────────────────────────────────────────────
    if not prediction or not parsed:
        render_no_data(all_resumes)
        return

    # ── KPI Strip ─────────────────────────────────────────────────────────
    role       = prediction["predicted_role"]
    confidence = prediction["confidence"]
    icon       = prediction.get("icon", "💼")
    c_color    = conf_color(confidence)
    c_label, _ = conf_label(confidence)
    alts       = prediction.get("alternatives", [])
    all_preds  = prediction.get("all_predictions", [prediction])

    # Recompute skill gap if missing
    if not skill_gap:
        skill_gap = analyze_skill_gap(parsed.get("skills", []), role)
        st.session_state.skill_gap = skill_gap

    match_pct  = skill_gap.get("match_percentage", 0)
    readiness  = skill_gap.get("readiness_level", {})

    k1, k2, k3, k4, k5 = st.columns(5)
    kpi_card(k1, "Predicted Role",   role,                       c_color,    icon)
    kpi_card(k2, "AI Confidence",    f"{confidence:.1f}%",       c_color,    "🤖")
    kpi_card(k3, "Skill Match",      f"{match_pct:.0f}%",        conf_color(match_pct), "🎯")
    kpi_card(k4, "Alt. Roles Found", len(alts),                  "#6c63ff",  "🔄")
    kpi_card(k5, "Readiness",        readiness.get("level","—"), conf_color(match_pct), "⚡")

    st.markdown("<hr style='border-color:rgba(108,99,255,0.15); margin:24px 0;'>",
                unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "🥇 Top Match",
        "📊 All Predictions",
        "🗂️ Role Requirements",
        "🔍 Skill Match",
        "🗺️ Career Roadmap",
        "💰 Market Info",
    ])

    with tabs[0]: render_top_match_tab(prediction, skill_gap, parsed)
    with tabs[1]: render_all_predictions_tab(all_preds)
    with tabs[2]: render_requirements_tab(role, icon)
    with tabs[3]: render_skill_match_tab(skill_gap, parsed)
    with tabs[4]: render_roadmap_tab(role)
    with tabs[5]: render_market_tab(role)


# ─── NO DATA ──────────────────────────────────────────────────────────────────

def render_no_data(all_resumes):
    st.markdown("""
    <div style="background:#161829; border:2px dashed rgba(108,99,255,0.35);
                border-radius:16px; padding:48px; text-align:center; margin:20px 0;">
        <div style="font-size:3.5rem;">🎯</div>
        <h3 style="color:#9fa8da; margin-top:12px;">No Prediction Available</h3>
        <p style="color:#4a5270;">Upload and analyse a resume first to see your job role prediction.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📤 Upload Resume Now", use_container_width=True):
        st.session_state.page = "upload"
        st.rerun()

    if all_resumes:
        st.markdown("<h3 style='color:#e8eaf6; margin-top:32px;'>📋 Past Predictions</h3>",
                    unsafe_allow_html=True)
        for r in all_resumes[:5]:
            role  = r["predicted_role"] or "—"
            conf  = r["confidence_score"] or 0
            date  = str(r["uploaded_at"])[:10]
            fname = r["filename"] or "resume"
            c     = conf_color(conf)
            st.markdown(f"""
            <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                        border-radius:12px; padding:14px 20px; margin:6px 0;
                        display:flex; align-items:center; justify-content:space-between;">
                <div>
                    <div style="font-weight:600; color:#e8eaf6;">📄 {fname}</div>
                    <div style="color:#9fa8da; font-size:0.78rem;">📅 {date}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1rem; font-weight:700; color:#e8eaf6;">{role}</div>
                    <div style="color:{c}; font-size:0.78rem;">{conf:.1f}% confidence</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Show all supported roles
    st.markdown("<h3 style='color:#e8eaf6; margin-top:32px;'>💼 Roles We Predict</h3>",
                unsafe_allow_html=True)
    render_all_roles_grid()


# ─── TAB 1 : TOP MATCH ────────────────────────────────────────────────────────

def render_top_match_tab(prediction, skill_gap, parsed):
    role       = prediction["predicted_role"]
    confidence = prediction["confidence"]
    icon       = prediction.get("icon", "💼")
    desc       = prediction.get("description", "")
    c_color    = conf_color(confidence)
    c_label, _ = conf_label(confidence)
    matched_kw = prediction.get("matched_keywords", [])
    readiness  = skill_gap.get("readiness_level", {})
    r_color    = readiness.get("color", "#9fa8da")
    r_level    = readiness.get("level", "")
    r_msg      = readiness.get("message", "")
    r_emoji    = readiness.get("emoji", "")

    hero_col, gauge_col = st.columns([1.4, 1])

    # ── Hero card ─────────────────────────────────────────────────────────
    with hero_col:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(108,99,255,0.18),
                    rgba(0,212,170,0.1)); border:1px solid rgba(108,99,255,0.4);
                    border-radius:20px; padding:28px 32px; margin-bottom:16px;">
            <div style="display:flex; align-items:flex-start; gap:20px;">
                <div style="font-size:3.8rem; line-height:1;">{icon}</div>
                <div style="flex:1;">
                    <div style="font-size:1.65rem; font-weight:800; color:#e8eaf6;
                                line-height:1.2;">{role}</div>
                    <div style="color:#9fa8da; font-size:0.88rem; margin-top:6px;
                                line-height:1.5;">{desc}</div>
                    <div style="margin-top:16px;">
                        <span style="background:rgba({_hex_rgb(c_color)},0.15);
                                     color:{c_color}; border:1px solid {c_color};
                                     padding:4px 14px; border-radius:20px;
                                     font-size:0.8rem; font-weight:700;">
                            {c_label}
                        </span>
                    </div>
                    <!-- Confidence bar -->
                    <div style="margin-top:18px;">
                        <div style="display:flex; justify-content:space-between;
                                    margin-bottom:6px;">
                            <span style="color:#9fa8da; font-size:0.8rem;">AI Confidence</span>
                            <span style="color:{c_color}; font-weight:700;">
                                {confidence:.1f}%
                            </span>
                        </div>
                        <div style="background:rgba(255,255,255,0.1); border-radius:8px;
                                    height:10px; overflow:hidden;">
                            <div style="background:linear-gradient(90deg,#6c63ff,{c_color});
                                        width:{min(confidence,100):.0f}%; height:100%;
                                        border-radius:8px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Readiness banner
        st.markdown(f"""
        <div style="background:rgba({_hex_rgb(r_color)},0.08);
                    border:1px solid {r_color}45; border-radius:12px;
                    padding:16px 20px; display:flex; align-items:center; gap:16px;">
            <div style="font-size:2rem;">{r_emoji}</div>
            <div>
                <div style="font-weight:700; color:{r_color}; font-size:1rem;">{r_level}</div>
                <div style="color:#9fa8da; font-size:0.82rem; margin-top:2px;">{r_msg}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Gauge ─────────────────────────────────────────────────────────────
    with gauge_col:
        st.plotly_chart(
            make_skill_match_gauge(skill_gap.get("match_percentage", 0), role),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        # Quick stats
        existing = skill_gap.get("existing_skills", [])
        missing  = skill_gap.get("missing_skills", [])
        st.markdown(f"""
        <div style="display:flex; gap:10px; margin-top:8px;">
            <div style="flex:1; background:rgba(0,212,170,0.1); border:1px solid rgba(0,212,170,0.3);
                        border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:1.4rem; font-weight:800; color:#00d4aa;">{len(existing)}</div>
                <div style="color:#9fa8da; font-size:0.75rem;">Skills matched</div>
            </div>
            <div style="flex:1; background:rgba(255,107,107,0.1); border:1px solid rgba(255,107,107,0.3);
                        border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:1.4rem; font-weight:800; color:#ff6b6b;">{len(missing)}</div>
                <div style="color:#9fa8da; font-size:0.75rem;">Skills missing</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Matched Keywords ──────────────────────────────────────────────────
    if matched_kw:
        st.markdown("<br><h4 style='color:#00d4aa;'>✅ Keywords That Matched This Role</h4>",
                    unsafe_allow_html=True)
        pills = "".join(skill_pill(k, "#00d4aa", "rgba(0,212,170,0.1)") for k in matched_kw)
        st.markdown(f"<div style='line-height:2.4;'>{pills}</div>", unsafe_allow_html=True)

    # ── Action buttons ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("🔍 View Skill Gap", use_container_width=True):
            st.session_state.page = "ats"
            st.rerun()
    with b2:
        if st.button("🤖 Get Career Advice", use_container_width=True):
            st.session_state.page = "chatbot"
            st.rerun()
    with b3:
        if st.button("📊 View ATS Report", use_container_width=True):
            st.session_state.page = "ats"
            st.rerun()


# ─── TAB 2 : ALL PREDICTIONS ──────────────────────────────────────────────────

def render_all_predictions_tab(all_preds):
    st.markdown("<h3 style='color:#e8eaf6;'>📊 All Role Predictions</h3>", unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("<p style='color:#9fa8da; font-size:0.82rem;'>Confidence score per role</p>",
                    unsafe_allow_html=True)
        st.plotly_chart(make_confidence_bar(all_preds), use_container_width=True,
                        config={"displayModeBar": False})

    with right:
        st.markdown("<p style='color:#9fa8da; font-size:0.82rem;'>Radar comparison</p>",
                    unsafe_allow_html=True)
        if len(all_preds) >= 3:
            st.plotly_chart(make_roles_radar(all_preds), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("Upload more varied resumes to enable radar comparison.")

    st.markdown("<hr style='border-color:rgba(108,99,255,0.12); margin:20px 0;'>",
                unsafe_allow_html=True)
    st.markdown("<h4 style='color:#e8eaf6;'>Role-by-Role Breakdown</h4>", unsafe_allow_html=True)

    for i, pred in enumerate(all_preds):
        c  = pred["confidence"]
        cc = conf_color(c)
        cl, _ = conf_label(c)
        is_top = i == 0
        border = "rgba(108,99,255,0.6)" if is_top else "rgba(108,99,255,0.15)"
        bg     = "rgba(108,99,255,0.08)" if is_top else "#1e2035"

        st.markdown(f"""
        <div style="background:{bg}; border:1px solid {border};
                    border-radius:12px; padding:16px 20px; margin:6px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div style="display:flex; align-items:center; gap:14px;">
                    <div style="font-size:1.6rem;">{pred.get('icon','💼')}</div>
                    <div>
                        <div style="font-weight:700; color:#e8eaf6;">
                            {pred['role']}
                            {"&nbsp;<span style='background:rgba(108,99,255,0.3); color:#6c63ff; "
                             "padding:2px 8px; border-radius:10px; font-size:0.7rem;'>TOP</span>"
                             if is_top else ""}
                        </div>
                        <div style="color:#9fa8da; font-size:0.78rem; margin-top:2px;">
                            {pred.get('description','')[:80]}…
                        </div>
                    </div>
                </div>
                <div style="text-align:right; min-width:100px;">
                    <div style="font-size:1.3rem; font-weight:800; color:{cc};">{c:.1f}%</div>
                    <div style="color:{cc}; font-size:0.72rem; font-weight:600;">{cl}</div>
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.07); border-radius:5px;
                        height:6px; overflow:hidden; margin-top:10px;">
                <div style="background:{cc}; width:{min(c,100):.0f}%;
                            height:100%; border-radius:5px;"></div>
            </div>
            {"<div style='color:#9fa8da; font-size:0.75rem; margin-top:6px;'>🔑 Matched: " +
             ", ".join(pred.get('matched_keywords', [])[:6]) + "</div>"
             if pred.get('matched_keywords') else ""}
        </div>
        """, unsafe_allow_html=True)


# ─── TAB 3 : ROLE REQUIREMENTS ────────────────────────────────────────────────

def render_requirements_tab(role, icon):
    st.markdown(f"<h3 style='color:#e8eaf6;'>{icon} {role} — Requirements</h3>",
                unsafe_allow_html=True)

    req = get_role_requirements(role)
    if not req:
        st.info("Requirements not available for this role.")
        return

    # Salary banner
    salary = req.get("avg_salary", "N/A")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(0,212,170,0.12),rgba(108,99,255,0.1));
                border:1px solid rgba(0,212,170,0.35); border-radius:14px;
                padding:18px 24px; margin-bottom:24px; display:flex;
                align-items:center; gap:20px;">
        <div style="font-size:2.5rem;">💰</div>
        <div>
            <div style="color:#9fa8da; font-size:0.8rem;">Average Salary Range</div>
            <div style="font-size:1.4rem; font-weight:800; color:#00d4aa;">{salary}</div>
            <div style="color:#4a5270; font-size:0.75rem;">USD/year · varies by location & seniority</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    core_col, adv_col = st.columns(2)

    # Core skills
    with core_col:
        st.markdown("<h4 style='color:#00d4aa;'>⭐ Core Skills Required</h4>",
                    unsafe_allow_html=True)
        for sk in req.get("core_skills", []):
            st.markdown(f"""
            <div style="background:rgba(0,212,170,0.08); border-left:3px solid #00d4aa;
                        border-radius:0 8px 8px 0; padding:9px 14px; margin:5px 0;
                        color:#e8eaf6; font-size:0.85rem; font-weight:500;">⭐ {sk}</div>
            """, unsafe_allow_html=True)

    # Advanced skills
    with adv_col:
        st.markdown("<h4 style='color:#6c63ff;'>🚀 Advanced Skills</h4>",
                    unsafe_allow_html=True)
        for sk in req.get("advanced_skills", []):
            st.markdown(f"""
            <div style="background:rgba(108,99,255,0.08); border-left:3px solid #6c63ff;
                        border-radius:0 8px 8px 0; padding:9px 14px; margin:5px 0;
                        color:#e8eaf6; font-size:0.85rem;">🚀 {sk}</div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tools_col, cert_col = st.columns(2)

    # Tools
    with tools_col:
        st.markdown("<h4 style='color:#ffd700;'>🛠️ Key Tools & Technologies</h4>",
                    unsafe_allow_html=True)
        tools = req.get("tools", [])
        if tools:
            pills = "".join(skill_pill(t, "#ffd700", "rgba(255,215,0,0.1)") for t in tools)
            st.markdown(f"<div style='line-height:2.4;'>{pills}</div>",
                        unsafe_allow_html=True)

    # Certifications
    with cert_col:
        st.markdown("<h4 style='color:#ff6b6b;'>🏆 Recommended Certifications</h4>",
                    unsafe_allow_html=True)
        for cert in req.get("certifications", []):
            st.markdown(f"""
            <div style="background:rgba(255,107,107,0.08); border-left:3px solid #ff6b6b;
                        border-radius:0 8px 8px 0; padding:9px 14px; margin:5px 0;
                        color:#e8eaf6; font-size:0.85rem;">🏆 {cert}</div>
            """, unsafe_allow_html=True)


# ─── TAB 4 : SKILL MATCH ──────────────────────────────────────────────────────

def render_skill_match_tab(skill_gap, parsed):
    st.markdown("<h3 style='color:#e8eaf6;'>🔍 Skill Match Analysis</h3>",
                unsafe_allow_html=True)

    existing  = skill_gap.get("existing_skills", [])
    missing   = skill_gap.get("missing_skills", [])
    critical  = skill_gap.get("critical_missing", [])
    match_pct = skill_gap.get("match_percentage", 0)
    resources = skill_gap.get("learning_resources", [])

    # Donut + match bar
    d_col, b_col = st.columns([1, 1.3])
    with d_col:
        st.plotly_chart(make_skill_donut(existing, missing), use_container_width=True,
                        config={"displayModeBar": False})
    with b_col:
        st.markdown(f"""
        <div style="padding:10px 0;">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="color:#e8eaf6; font-weight:600;">Overall Skill Match</span>
                <span style="color:{conf_color(match_pct)}; font-weight:800;
                             font-size:1.1rem;">{match_pct:.1f}%</span>
            </div>
            <div style="background:rgba(255,255,255,0.08); border-radius:8px;
                        height:14px; overflow:hidden; margin-bottom:20px;">
                <div style="background:linear-gradient(90deg,#6c63ff,#00d4aa);
                            width:{match_pct:.0f}%; height:100%; border-radius:8px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Category-wise breakdown
        skill_cats = skill_gap.get("skill_categories", {})
        for cat_name, data in list(skill_cats.items())[:6]:
            pct   = data.get("percentage", 0)
            match = data.get("matched", 0)
            total = data.get("total", 0)
            cc    = conf_color(pct)
            label = cat_name.replace("_", " ").title()
            st.markdown(f"""
            <div style="margin-bottom:11px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:#9fa8da; font-size:0.8rem;">{label}</span>
                    <span style="color:{cc}; font-size:0.8rem; font-weight:600;">
                        {match}/{total}
                    </span>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:5px;
                            height:7px; overflow:hidden;">
                    <div style="background:{cc}; width:{pct:.0f}%; height:100%;
                                border-radius:5px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(108,99,255,0.12); margin:20px 0;'>",
                unsafe_allow_html=True)

    have_col, miss_col = st.columns(2)

    with have_col:
        st.markdown(f"<h4 style='color:#00d4aa;'>✅ Skills You Have ({len(existing)})</h4>",
                    unsafe_allow_html=True)
        if existing:
            pills = "".join(skill_pill(s, "#00d4aa", "rgba(0,212,170,0.1)") for s in existing)
            st.markdown(f"<div style='line-height:2.4;'>{pills}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#4a5270;'>No matching skills found.</p>",
                        unsafe_allow_html=True)

    with miss_col:
        st.markdown(f"<h4 style='color:#ff6b6b;'>❌ Skills to Learn ({len(missing)})</h4>",
                    unsafe_allow_html=True)
        if critical:
            st.markdown("<p style='color:#ff6b6b; font-size:0.78rem; margin:4px 0;'>🔴 Critical:</p>",
                        unsafe_allow_html=True)
            pills = "".join(skill_pill(s, "#ff6b6b", "rgba(255,107,107,0.1)") for s in critical)
            st.markdown(f"<div style='line-height:2.4; margin-bottom:8px;'>{pills}</div>",
                        unsafe_allow_html=True)
        non_crit = [s for s in missing if s not in critical]
        if non_crit:
            pills = "".join(skill_pill(s, "#ffd700", "rgba(255,215,0,0.1)") for s in non_crit[:12])
            st.markdown(f"<div style='line-height:2.4;'>{pills}</div>", unsafe_allow_html=True)

    # Learning resources
    if resources:
        st.markdown("<br><h4 style='color:#6c63ff;'>📚 Learning Resources for Missing Skills</h4>",
                    unsafe_allow_html=True)
        r_cols = st.columns(2)
        for i, res in enumerate(resources):
            with r_cols[i % 2]:
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
                             style="color:#6c63ff; text-decoration:none;">
                            {res['platform']}
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ─── TAB 5 : CAREER ROADMAP ───────────────────────────────────────────────────

def render_roadmap_tab(role):
    st.markdown(f"<h3 style='color:#e8eaf6;'>🗺️ Career Roadmap — {role}</h3>",
                unsafe_allow_html=True)

    req = get_role_requirements(role)
    path = req.get("learning_path", ["No path available."])

    # Visual timeline
    st.markdown("<h4 style='color:#9fa8da; font-size:0.9rem; margin-bottom:16px;'>"
                "Suggested learning progression:</h4>", unsafe_allow_html=True)

    if path:
        raw = path[0] if isinstance(path, list) else path
        steps = [s.strip() for s in raw.split("→")]
        for i, step in enumerate(steps):
            is_last = i == len(steps) - 1
            dot_color = "#00d4aa" if is_last else "#6c63ff"
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:16px; margin:8px 0;">
                <div style="display:flex; flex-direction:column; align-items:center; min-width:32px;">
                    <div style="width:32px; height:32px; border-radius:50%;
                                background:{dot_color}22; border:2px solid {dot_color};
                                display:flex; align-items:center; justify-content:center;
                                font-size:0.8rem; font-weight:700; color:{dot_color};">
                        {i+1}
                    </div>
                    {"" if is_last else
                     "<div style='width:2px; height:24px; background:rgba(108,99,255,0.3);'></div>"}
                </div>
                <div style="background:#1e2035; border:1px solid {dot_color}40;
                            border-radius:10px; padding:10px 18px; flex:1;
                            color:#e8eaf6; font-weight:{'700' if is_last else '500'};
                            font-size:0.88rem;">
                    {step}
                    {"&nbsp; 🏁" if is_last else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Role-specific roadmap detail cards
    roadmap_details = get_roadmap_detail(role)
    st.markdown("<h4 style='color:#e8eaf6;'>📅 Phase-by-Phase Plan</h4>",
                unsafe_allow_html=True)
    for phase in roadmap_details:
        duration_color = {"0-1 Month": "#ff6b6b", "1-3 Months": "#ffd700",
                          "3-6 Months": "#6c63ff", "6-12 Months": "#00d4aa"
                          }.get(phase["duration"], "#9fa8da")
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                    border-radius:14px; padding:18px 22px; margin:10px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between;
                        margin-bottom:10px;">
                <div style="font-weight:700; color:#e8eaf6; font-size:0.95rem;">
                    {phase['phase']}
                </div>
                <span style="background:{duration_color}22; color:{duration_color};
                             border:1px solid {duration_color}; padding:3px 12px;
                             border-radius:20px; font-size:0.75rem; font-weight:700;">
                    ⏱ {phase['duration']}
                </span>
            </div>
            <div style="color:#9fa8da; font-size:0.82rem; line-height:1.8;">
                {"".join(f"• {task}<br>" for task in phase['tasks'])}
            </div>
        </div>
        """, unsafe_allow_html=True)


def get_roadmap_detail(role: str) -> list:
    """Return phase-by-phase roadmap for each role."""
    roadmaps = {
        "Data Scientist": [
            {"phase": "Phase 1 — Foundations",       "duration": "0-1 Month",
             "tasks": ["Python basics (variables, loops, functions)", "Statistics & probability",
                       "NumPy & Pandas fundamentals", "Jupyter Notebook setup"]},
            {"phase": "Phase 2 — Core ML",           "duration": "1-3 Months",
             "tasks": ["Scikit-learn (regression, classification, clustering)",
                       "Data visualisation (Matplotlib, Seaborn, Plotly)",
                       "Feature engineering & preprocessing", "Model evaluation metrics"]},
            {"phase": "Phase 3 — Deep Learning",     "duration": "3-6 Months",
             "tasks": ["TensorFlow / PyTorch basics", "Neural networks, CNN, RNN, LSTM",
                       "NLP with Hugging Face Transformers", "Computer vision projects"]},
            {"phase": "Phase 4 — Production Ready",  "duration": "6-12 Months",
             "tasks": ["MLOps: MLflow, DVC, model versioning", "Deploy models (FastAPI, Docker)",
                       "Cloud ML (AWS SageMaker / GCP Vertex)", "Build 3 portfolio projects"]},
        ],
        "AI/ML Engineer": [
            {"phase": "Phase 1 — Foundations",       "duration": "0-1 Month",
             "tasks": ["Python + OOP", "Linear algebra & calculus basics",
                       "Git & Docker fundamentals"]},
            {"phase": "Phase 2 — ML/DL",             "duration": "1-3 Months",
             "tasks": ["Scikit-learn, TensorFlow, PyTorch",
                       "LLMs, fine-tuning, Hugging Face", "GPU setup with CUDA"]},
            {"phase": "Phase 3 — MLOps",             "duration": "3-6 Months",
             "tasks": ["ML pipelines: Airflow, Kubeflow", "Kubernetes for model serving",
                       "Monitoring: Prometheus, Grafana"]},
            {"phase": "Phase 4 — Enterprise",        "duration": "6-12 Months",
             "tasks": ["Distributed training", "LLM deployment at scale",
                       "Cloud certifications: AWS ML / GCP Pro"]},
        ],
        "Web Developer": [
            {"phase": "Phase 1 — Frontend Basics",   "duration": "0-1 Month",
             "tasks": ["HTML5 & CSS3", "Responsive design", "JavaScript ES6+"]},
            {"phase": "Phase 2 — Framework",         "duration": "1-3 Months",
             "tasks": ["React.js / Vue.js", "State management (Redux / Pinia)",
                       "REST API consumption, Axios"]},
            {"phase": "Phase 3 — Backend",           "duration": "3-6 Months",
             "tasks": ["Node.js + Express", "Databases: PostgreSQL, MongoDB",
                       "Authentication: JWT, OAuth"]},
            {"phase": "Phase 4 — Full Stack",        "duration": "6-12 Months",
             "tasks": ["Docker + CI/CD", "Deploy on Vercel / AWS / Render",
                       "Performance optimisation, testing"]},
        ],
        "DevOps Engineer": [
            {"phase": "Phase 1 — Linux & Networking", "duration": "0-1 Month",
             "tasks": ["Linux commands & shell scripting", "Networking: TCP/IP, DNS, HTTP",
                       "Git version control"]},
            {"phase": "Phase 2 — Containers",        "duration": "1-3 Months",
             "tasks": ["Docker: images, compose, networking",
                       "Kubernetes: pods, deployments, services", "Helm charts"]},
            {"phase": "Phase 3 — CI/CD & Cloud",     "duration": "3-6 Months",
             "tasks": ["Jenkins / GitHub Actions pipelines",
                       "AWS / Azure / GCP fundamentals", "Terraform IaC"]},
            {"phase": "Phase 4 — SRE / Advanced",   "duration": "6-12 Months",
             "tasks": ["Monitoring: Prometheus, Grafana, ELK",
                       "Service mesh: Istio", "CKA / AWS DevOps Pro certification"]},
        ],
    }
    # Default generic roadmap for roles not explicitly mapped
    default = [
        {"phase": "Phase 1 — Foundations",  "duration": "0-1 Month",
         "tasks": ["Learn core programming language for this role",
                   "Study fundamentals and theory", "Set up development environment"]},
        {"phase": "Phase 2 — Core Skills",  "duration": "1-3 Months",
         "tasks": ["Build domain-specific skills", "Work on guided tutorials & courses",
                   "Complete 1 small project"]},
        {"phase": "Phase 3 — Projects",     "duration": "3-6 Months",
         "tasks": ["Build 2-3 portfolio projects", "Contribute to open source",
                   "Apply for internships or junior roles"]},
        {"phase": "Phase 4 — Job Ready",    "duration": "6-12 Months",
         "tasks": ["Get industry certification", "Network on LinkedIn",
                   "Practice interview questions"]},
    ]
    return roadmaps.get(role, default)


# ─── TAB 6 : MARKET INFO ──────────────────────────────────────────────────────

def render_market_tab(role):
    st.markdown("<h3 style='color:#e8eaf6;'>💰 Market Insights</h3>", unsafe_allow_html=True)

    # Demand chart
    st.plotly_chart(make_all_roles_bar(), use_container_width=True,
                    config={"displayModeBar": False})

    st.markdown("<hr style='border-color:rgba(108,99,255,0.12); margin:20px 0;'>",
                unsafe_allow_html=True)

    # Salary table for all roles
    st.markdown("<h4 style='color:#e8eaf6;'>💵 Salary Benchmarks (USD/year)</h4>",
                unsafe_allow_html=True)

    salary_data = {
        "Data Scientist":       ("$70K", "$95K",  "$140K", "🔬"),
        "AI/ML Engineer":       ("$90K", "$120K", "$165K", "🤖"),
        "Web Developer":        ("$55K", "$80K",  "$120K", "🌐"),
        "DevOps Engineer":      ("$75K", "$100K", "$148K", "⚙️"),
        "Cloud Engineer":       ("$80K", "$110K", "$150K", "☁️"),
        "Cybersecurity Analyst":("$70K", "$95K",  "$135K", "🛡️"),
        "Business Analyst":     ("$60K", "$80K",  "$115K", "📊"),
        "Python Developer":     ("$65K", "$90K",  "$125K", "🐍"),
    }

    header = """
    <div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr;
                background:#161829; border-radius:10px 10px 0 0;
                padding:10px 18px; border:1px solid rgba(108,99,255,0.2);
                border-bottom:none;">
        <div style="color:#6c63ff; font-weight:700; font-size:0.8rem;">ROLE</div>
        <div style="color:#6c63ff; font-weight:700; font-size:0.8rem; text-align:center;">ENTRY</div>
        <div style="color:#6c63ff; font-weight:700; font-size:0.8rem; text-align:center;">MID</div>
        <div style="color:#6c63ff; font-weight:700; font-size:0.8rem; text-align:center;">SENIOR</div>
    </div>
    """
    st.markdown(header, unsafe_allow_html=True)

    for r_name, (entry, mid, senior, ico) in salary_data.items():
        is_current = r_name == role
        bg    = "rgba(108,99,255,0.1)" if is_current else "#1e2035"
        bdr   = "rgba(108,99,255,0.5)" if is_current else "rgba(108,99,255,0.15)"
        flag  = "&nbsp;⭐ Your match" if is_current else ""
        st.markdown(f"""
        <div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr;
                    background:{bg}; border:1px solid {bdr};
                    border-top:none; padding:11px 18px;
                    transition:background 0.2s;">
            <div style="color:#e8eaf6; font-weight:{'700' if is_current else '500'};
                        font-size:0.85rem;">
                {ico} {r_name}{flag}
            </div>
            <div style="color:#ff6b6b; font-weight:600; font-size:0.85rem;
                        text-align:center;">{entry}</div>
            <div style="color:#ffd700; font-weight:600; font-size:0.85rem;
                        text-align:center;">{mid}</div>
            <div style="color:#00d4aa; font-weight:600; font-size:0.85rem;
                        text-align:center;">{senior}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#161829; border:1px solid rgba(108,99,255,0.15);
                border-top:none; border-radius:0 0 10px 10px;
                padding:8px 18px; color:#4a5270; font-size:0.72rem;">
        * Figures are approximate US market ranges. Actual compensation varies by location,
        company size, and individual experience.
    </div>
    """, unsafe_allow_html=True)

    # Job search links
    st.markdown("<br><h4 style='color:#e8eaf6;'>🔎 Find Jobs Now</h4>", unsafe_allow_html=True)
    encoded_role = role.replace(" ", "+")
    job_links = [
        ("LinkedIn Jobs",   f"https://www.linkedin.com/jobs/search/?keywords={encoded_role}", "#0077B5"),
        ("Indeed",          f"https://www.indeed.com/jobs?q={encoded_role}",                  "#2164f3"),
        ("Glassdoor",       f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={encoded_role}", "#0caa41"),
        ("Naukri (India)",  f"https://www.naukri.com/{encoded_role.lower().replace('+','-')}-jobs", "#ff7555"),
    ]
    j1, j2, j3, j4 = st.columns(4)
    for col, (name, url, color) in zip([j1, j2, j3, j4], job_links):
        with col:
            st.markdown(f"""
            <a href="{url}" target="_blank" style="text-decoration:none;">
                <div style="background:{color}18; border:1px solid {color}50;
                            border-radius:10px; padding:12px; text-align:center;
                            transition:all 0.2s; cursor:pointer;">
                    <div style="color:{color}; font-weight:700; font-size:0.85rem;">
                        🔗 {name}
                    </div>
                    <div style="color:#9fa8da; font-size:0.72rem; margin-top:3px;">
                        Search {role}
                    </div>
                </div>
            </a>
            """, unsafe_allow_html=True)


# ─── ALL ROLES GRID (no-data state) ───────────────────────────────────────────

def render_all_roles_grid():
    cols = st.columns(4)
    for i, (role_name, config) in enumerate(JOB_ROLES.items()):
        with cols[i % 4]:
            st.markdown(f"""
            <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.18);
                        border-radius:12px; padding:16px; text-align:center; margin:6px 0;
                        min-height:100px;">
                <div style="font-size:2rem;">{config['icon']}</div>
                <div style="color:#e8eaf6; font-weight:600; font-size:0.82rem; margin-top:6px;">
                    {role_name}
                </div>
                <div style="color:#9fa8da; font-size:0.72rem; margin-top:4px; line-height:1.4;">
                    {config['description'][:55]}…
                </div>
            </div>
            """, unsafe_allow_html=True)


# ─── UTILITY ──────────────────────────────────────────────────────────────────

def _hex_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    return "108,99,255"
