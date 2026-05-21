"""
ATS Analysis Page
Full ATS score breakdown, keyword analysis, resume strength meter,
optimization suggestions, and historical score tracking.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.database import get_user_resumes
from utils.ats_engine import calculate_ats_score, get_ats_category
from utils.resume_parser import parse_resume


# ─── COLOUR HELPERS ───────────────────────────────────────────────────────────

def ats_color(score: float) -> str:
    if score >= 80:   return "#00d4aa"
    elif score >= 65: return "#6c63ff"
    elif score >= 45: return "#ffd700"
    return "#ff6b6b"


def category_emoji(cat: str) -> str:
    return {"Excellent": "🏆", "Good": "✅", "Average": "⚠️", "Poor": "❌"}.get(cat, "📊")


def priority_color(pri: str):
    return {
        "Critical": ("#ff6b6b", "rgba(255,107,107,0.12)"),
        "High":     ("#ffd700", "rgba(255,215,0,0.12)"),
        "Medium":   ("#6c63ff", "rgba(108,99,255,0.12)"),
        "Low":      ("#9fa8da", "rgba(159,168,218,0.12)"),
    }.get(pri, ("#9fa8da", "rgba(159,168,218,0.12)"))


def skill_pill(text: str, color: str = "#6c63ff", bg: str = "rgba(108,99,255,0.12)") -> str:
    return (
        f"<span style='background:{bg}; color:{color}; border:1px solid {color}; "
        f"padding:3px 11px; border-radius:20px; font-size:0.78rem; "
        f"margin:3px; display:inline-block;'>{text}</span>"
    )


# ─── PLOTLY THEME ─────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk, sans-serif", color="#9fa8da"),
    margin=dict(l=20, r=20, t=40, b=20),
)


# ─── GAUGE CHART ──────────────────────────────────────────────────────────────

def make_gauge(score: float, label: str = "ATS Score") -> go.Figure:
    color = ats_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        delta={"reference": 65, "increasing": {"color": "#00d4aa"},
               "decreasing": {"color": "#ff6b6b"}},
        title={"text": label, "font": {"size": 16, "color": "#9fa8da"}},
        number={"font": {"size": 52, "color": color}, "suffix": "/100"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1,
                     "tickcolor": "#4a5270", "tickfont": {"color": "#9fa8da"}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "rgba(30,32,53,0.8)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  45], "color": "rgba(255,107,107,0.15)"},
                {"range": [45, 65], "color": "rgba(255,215,0,0.12)"},
                {"range": [65, 80], "color": "rgba(108,99,255,0.12)"},
                {"range": [80,100], "color": "rgba(0,212,170,0.12)"},
            ],
            "threshold": {
                "line": {"color": "#ffffff", "width": 2},
                "thickness": 0.75,
                "value": score,
            },
        },
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=300)
    return fig


# ─── RADAR CHART ──────────────────────────────────────────────────────────────

def make_radar(breakdown: dict) -> go.Figure:
    cats   = list(breakdown.keys())
    scores = [breakdown[c]["score"] for c in cats]
    cats  += [cats[0]]
    scores += [scores[0]]

    fig = go.Figure(go.Scatterpolar(
        r=scores,
        theta=cats,
        fill="toself",
        fillcolor="rgba(108,99,255,0.18)",
        line=dict(color="#6c63ff", width=2),
        marker=dict(size=6, color="#00d4aa"),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        polar=dict(
            bgcolor="rgba(22,24,41,0.6)",
            radialaxis=dict(visible=True, range=[0, 100],
                            gridcolor="#2a2d45", tickfont={"color": "#9fa8da"}),
            angularaxis=dict(gridcolor="#2a2d45", tickfont={"color": "#e8eaf6"}),
        ),
        height=320,
    )
    return fig


# ─── HISTORY BAR CHART ────────────────────────────────────────────────────────

def make_history_chart(resumes: list) -> go.Figure:
    labels = [f"#{i+1} {r['filename'][:18]}…" if len(r['filename'] or '') > 18
              else f"#{i+1} {r['filename'] or 'resume'}" for i, r in enumerate(resumes)]
    scores = [r["ats_score"] or 0 for r in resumes]
    colors = [ats_color(s) for s in scores]

    fig = go.Figure(go.Bar(
        x=labels,
        y=scores,
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=[f"{s:.0f}" for s in scores],
        textposition="outside",
        textfont=dict(color="#e8eaf6", size=12),
    ))
    fig.add_hline(y=65, line_dash="dot", line_color="#6c63ff",
                  annotation_text="Good threshold (65)",
                  annotation_font_color="#9fa8da")
    fig.add_hline(y=80, line_dash="dot", line_color="#00d4aa",
                  annotation_text="Excellent (80)",
                  annotation_font_color="#9fa8da")
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(tickangle=-30, gridcolor="#2a2d45"),
        yaxis=dict(range=[0, 110], gridcolor="#2a2d45"),
        height=300,
    )
    return fig


# ─── BREAKDOWN BAR CHART ──────────────────────────────────────────────────────

def make_breakdown_bar(breakdown: dict) -> go.Figure:
    criteria = list(breakdown.keys())
    scores   = [breakdown[c]["score"] for c in criteria]
    weights  = [breakdown[c]["weight"] for c in criteria]
    colors   = [ats_color(s) for s in scores]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Score",
        x=criteria,
        y=scores,
        marker=dict(color=colors, opacity=0.85),
        text=[f"{s:.0f}" for s in scores],
        textposition="outside",
        textfont=dict(color="#e8eaf6"),
    ))
    fig.add_trace(go.Scatter(
        name="Weight %",
        x=criteria,
        y=weights,
        mode="lines+markers",
        line=dict(color="#ffd700", width=2, dash="dot"),
        marker=dict(size=8, color="#ffd700"),
        yaxis="y2",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        yaxis=dict(title="Score /100", range=[0, 115], gridcolor="#2a2d45"),
        yaxis2=dict(title="Weight %", overlaying="y", side="right",
                    range=[0, 60], gridcolor="rgba(0,0,0,0)"),
        legend=dict(bgcolor="rgba(0,0,0,0)", x=0.01, y=1.1, orientation="h"),
        height=320,
        barmode="group",
    )
    return fig


# ─── MAIN PAGE ────────────────────────────────────────────────────────────────

def show():
    st.markdown("""
    <h1 style='color:#e8eaf6; margin-bottom:4px;'>📊 ATS Analysis</h1>
    <p style='color:#9fa8da; margin-bottom:28px;'>
        Deep-dive into your ATS score — what's working, what's missing, and how to improve.
    </p>
    """, unsafe_allow_html=True)

    # ── Check if we have data ─────────────────────────────────────────────
    ats_report  = st.session_state.get("ats_report")
    parsed      = st.session_state.get("resume_parsed")
    user        = st.session_state.user
    all_resumes = get_user_resumes(user["id"])

    if not ats_report or not parsed:
        render_no_data(all_resumes)
        return

    # ── Summary KPI Strip ────────────────────────────────────────────────
    score  = ats_report["total_score"]
    cat    = ats_report["category"]
    color  = ats_color(score)
    emoji  = category_emoji(cat)

    k1, k2, k3, k4, k5 = st.columns(5)
    kpi_card(k1, "ATS Score",     f"{score:.0f}/100",         color,    "📊")
    kpi_card(k2, "Category",      f"{emoji} {cat}",           color,    "🏷️")
    kpi_card(k3, "Skills Found",  len(parsed.get("skills", [])), "#6c63ff", "🛠️")
    kpi_card(k4, "Missing KW",    len(ats_report.get("missing_keywords", [])), "#ff6b6b", "🔑")
    kpi_card(k5, "Suggestions",   len(ats_report.get("suggestions", [])),      "#ffd700", "💡")

    st.markdown("<hr style='border-color:rgba(108,99,255,0.15); margin:24px 0;'>",
                unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "🎯 Score Overview",
        "📐 Breakdown",
        "🔑 Keywords",
        "💡 Optimization",
        "📈 History",
        "📋 Full Report",
    ])

    with tabs[0]: render_overview_tab(ats_report, parsed, score, cat, color, emoji)
    with tabs[1]: render_breakdown_tab(ats_report)
    with tabs[2]: render_keywords_tab(ats_report, parsed)
    with tabs[3]: render_optimization_tab(ats_report, parsed)
    with tabs[4]: render_history_tab(all_resumes)
    with tabs[5]: render_full_report_tab(ats_report, parsed)


# ─── NO DATA STATE ────────────────────────────────────────────────────────────

def render_no_data(all_resumes: list):
    st.markdown("""
    <div style="background:#161829; border:2px dashed rgba(108,99,255,0.35);
                border-radius:16px; padding:48px; text-align:center; margin:20px 0;">
        <div style="font-size:3.5rem;">📭</div>
        <h3 style="color:#9fa8da; margin-top:12px;">No ATS Report Found</h3>
        <p style="color:#4a5270;">Upload and analyse a resume first to see your ATS score.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📤 Upload Resume Now", use_container_width=True):
        st.session_state.page = "upload"
        st.rerun()

    if all_resumes:
        st.markdown("<h3 style='color:#e8eaf6; margin-top:32px;'>📋 Past Analyses</h3>",
                    unsafe_allow_html=True)
        for r in all_resumes[:5]:
            s = r["ats_score"] or 0
            c_color = ats_color(s)
            st.markdown(f"""
            <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                        border-radius:12px; padding:16px; margin:8px 0;
                        display:flex; align-items:center; justify-content:space-between;">
                <div>
                    <div style="font-weight:600; color:#e8eaf6;">📄 {r['filename'] or 'resume'}</div>
                    <div style="color:#9fa8da; font-size:0.8rem;">
                        🎯 {r['predicted_role'] or '—'} &nbsp;|&nbsp; 📅 {str(r['uploaded_at'])[:10]}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.6rem; font-weight:800; color:{c_color};">{s:.0f}</div>
                    <div style="font-size:0.75rem; color:{c_color};">{r['ats_category'] or '—'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ─── KPI CARD ─────────────────────────────────────────────────────────────────

def kpi_card(col, label, value, color="#6c63ff", icon="📊"):
    with col:
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                    border-radius:12px; padding:16px; text-align:center;">
            <div style="font-size:1.4rem;">{icon}</div>
            <div style="font-size:1.4rem; font-weight:800; color:{color}; line-height:1.2;">
                {value}
            </div>
            <div style="color:#9fa8da; font-size:0.75rem; margin-top:4px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)


# ─── TAB 1 : SCORE OVERVIEW ───────────────────────────────────────────────────

def render_overview_tab(ats_report, parsed, score, cat, color, emoji):
    left, right = st.columns([1, 1.1])

    with left:
        st.plotly_chart(make_gauge(score), use_container_width=True, config={"displayModeBar": False})

        # Category banner
        cat_msgs = {
            "Excellent": ("🎉 Outstanding Resume!", "Your resume is highly ATS-optimised. Apply with confidence!", "#00d4aa"),
            "Good":      ("✅ Good Resume",         "Solid resume. A few tweaks can push you to Excellent.",         "#6c63ff"),
            "Average":   ("⚠️ Needs Improvement",  "Several areas need work. Follow the suggestions below.",        "#ffd700"),
            "Poor":      ("❌ Significant Gaps",    "Major improvements needed. Check the Optimization tab.",        "#ff6b6b"),
        }
        title, msg, c = cat_msgs.get(cat, ("📊 Result", "", color))
        st.markdown(f"""
        <div style="background:rgba({_hex_rgb(c)},0.1); border:1px solid {c}50;
                    border-radius:12px; padding:16px; text-align:center; margin-top:8px;">
            <div style="font-size:1.1rem; font-weight:700; color:{c};">{title}</div>
            <div style="color:#9fa8da; font-size:0.82rem; margin-top:4px;">{msg}</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        # Resume strength meter (5 pillars)
        st.markdown("<h4 style='color:#e8eaf6; margin-bottom:16px;'>🏋️ Resume Strength Meter</h4>",
                    unsafe_allow_html=True)

        pillars = [
            ("Skills Coverage",    min(len(parsed.get("skills", [])) / 12 * 100, 100),  "🛠️"),
            ("Contact Completeness",
             sum([bool(parsed.get("email")), bool(parsed.get("phone")),
                  bool(parsed.get("linkedin")), bool(parsed.get("github"))]) / 4 * 100,  "📇"),
            ("Education",          100 if parsed.get("education") else 30,               "🎓"),
            ("Certifications",     min(len(parsed.get("certifications", [])) * 30, 100), "🏆"),
            ("Content Depth",      min(parsed.get("word_count", 0) / 600 * 100, 100),   "📝"),
        ]

        for name, pct, ico in pillars:
            bar_color = ats_color(pct)
            st.markdown(f"""
            <div style="margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span style="color:#e8eaf6; font-size:0.85rem;">{ico} {name}</span>
                    <span style="color:{bar_color}; font-weight:700; font-size:0.85rem;">
                        {pct:.0f}%
                    </span>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:6px;
                            height:9px; overflow:hidden;">
                    <div style="background:{bar_color}; width:{pct:.0f}%; height:100%;
                                border-radius:6px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ATS category legend
        st.markdown("""
        <div style="background:#161829; border:1px solid rgba(108,99,255,0.15);
                    border-radius:10px; padding:14px; margin-top:8px;">
            <div style="color:#9fa8da; font-size:0.78rem; font-weight:600;
                        margin-bottom:8px;">ATS SCORE LEGEND</div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <span style="color:#00d4aa; font-size:0.78rem;">🏆 80-100 Excellent</span>
                <span style="color:#6c63ff; font-size:0.78rem;">✅ 65-79 Good</span>
                <span style="color:#ffd700; font-size:0.78rem;">⚠️ 45-64 Average</span>
                <span style="color:#ff6b6b; font-size:0.78rem;">❌ 0-44 Poor</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─── TAB 2 : BREAKDOWN ────────────────────────────────────────────────────────

def render_breakdown_tab(ats_report):
    breakdown = ats_report.get("breakdown", {})

    st.markdown("<h3 style='color:#e8eaf6;'>📐 Score Breakdown</h3>", unsafe_allow_html=True)

    # Bar + Radar side by side
    chart_l, chart_r = st.columns(2)
    with chart_l:
        st.markdown("<p style='color:#9fa8da; font-size:0.82rem;'>Score per criterion with weight overlay</p>",
                    unsafe_allow_html=True)
        st.plotly_chart(make_breakdown_bar(breakdown), use_container_width=True,
                        config={"displayModeBar": False})
    with chart_r:
        st.markdown("<p style='color:#9fa8da; font-size:0.82rem;'>Radar view of all criteria</p>",
                    unsafe_allow_html=True)
        st.plotly_chart(make_radar(breakdown), use_container_width=True,
                        config={"displayModeBar": False})

    st.markdown("<hr style='border-color:rgba(108,99,255,0.12); margin:20px 0;'>",
                unsafe_allow_html=True)

    # Detailed criterion cards
    st.markdown("<h4 style='color:#e8eaf6;'>Criterion Details</h4>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    items = list(breakdown.items())
    for i, (crit, data) in enumerate(items):
        col = col_a if i % 2 == 0 else col_b
        with col:
            s      = data["score"]
            w      = data["weight"]
            note   = data.get("note", "")
            c      = ats_color(s)
            contrib = round(s * w / 100, 1)
            st.markdown(f"""
            <div style="background:#1e2035; border:1px solid {c}30;
                        border-radius:12px; padding:18px; margin:6px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-weight:700; color:#e8eaf6; font-size:0.95rem;">{crit}</div>
                    <div style="font-size:1.4rem; font-weight:800; color:{c};">{s:.0f}</div>
                </div>
                <div style="color:#9fa8da; font-size:0.78rem; margin:6px 0;">{note}</div>
                <div style="background:rgba(255,255,255,0.07); border-radius:5px;
                            height:7px; overflow:hidden; margin:8px 0;">
                    <div style="background:{c}; width:{s:.0f}%; height:100%; border-radius:5px;">
                    </div>
                </div>
                <div style="display:flex; justify-content:space-between;
                            color:#4a5270; font-size:0.72rem;">
                    <span>Weight: {w}%</span>
                    <span>Contributes: +{contrib} pts</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ─── TAB 3 : KEYWORDS ─────────────────────────────────────────────────────────

def render_keywords_tab(ats_report, parsed):
    st.markdown("<h3 style='color:#e8eaf6;'>🔑 Keyword Analysis</h3>", unsafe_allow_html=True)

    found_skills  = parsed.get("skills", [])
    missing_kw    = ats_report.get("missing_keywords", [])

    # Two columns
    f_col, m_col = st.columns(2)

    with f_col:
        st.markdown(f"""
        <div style="background:rgba(0,212,170,0.06); border:1px solid rgba(0,212,170,0.25);
                    border-radius:12px; padding:18px; margin-bottom:16px;">
            <h4 style="color:#00d4aa; margin-bottom:12px;">
                ✅ Keywords Found &nbsp;
                <span style="font-size:0.85rem; font-weight:400; color:#9fa8da;">
                    ({len(found_skills)} detected)
                </span>
            </h4>
        </div>
        """, unsafe_allow_html=True)
        if found_skills:
            pills = "".join(skill_pill(s, "#00d4aa", "rgba(0,212,170,0.1)") for s in found_skills)
            st.markdown(f"<div style='line-height:2.4;'>{pills}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#4a5270;'>No skills/keywords detected.</p>",
                        unsafe_allow_html=True)

    with m_col:
        st.markdown(f"""
        <div style="background:rgba(255,107,107,0.06); border:1px solid rgba(255,107,107,0.25);
                    border-radius:12px; padding:18px; margin-bottom:16px;">
            <h4 style="color:#ff6b6b; margin-bottom:12px;">
                ❌ High-Value Missing Keywords &nbsp;
                <span style="font-size:0.85rem; font-weight:400; color:#9fa8da;">
                    ({len(missing_kw)} missing)
                </span>
            </h4>
        </div>
        """, unsafe_allow_html=True)
        if missing_kw:
            pills = "".join(skill_pill(k, "#ff6b6b", "rgba(255,107,107,0.1)") for k in missing_kw)
            st.markdown(f"<div style='line-height:2.4;'>{pills}</div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background:rgba(255,215,0,0.08); border:1px solid rgba(255,215,0,0.25);
                        border-radius:10px; padding:12px; margin-top:16px;">
                <div style="color:#ffd700; font-size:0.82rem; font-weight:600;">
                    💡 Pro Tip
                </div>
                <div style="color:#9fa8da; font-size:0.8rem; margin-top:4px;">
                    Mirror keywords from the job description into your resume.
                    ATS systems match exact words — spelling matters.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#00d4aa;'>✅ No critical keywords missing!</p>",
                        unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(108,99,255,0.12); margin:24px 0;'>",
                unsafe_allow_html=True)

    # Skills donut by category
    st.markdown("<h4 style='color:#e8eaf6;'>🗂️ Skill Distribution by Category</h4>",
                unsafe_allow_html=True)
    render_skill_donut(found_skills)


def render_skill_donut(skills: list):
    from utils.resume_parser import SKILLS_DB

    skill_set = set(s.lower() for s in skills)
    cat_counts = {}
    for cat, cat_skills in SKILLS_DB.items():
        matched = sum(1 for s in cat_skills if s in skill_set)
        if matched:
            cat_counts[cat.replace("_", " ").title()] = matched

    if not cat_counts:
        st.info("No categorised skills found.")
        return

    fig = go.Figure(go.Pie(
        labels=list(cat_counts.keys()),
        values=list(cat_counts.values()),
        hole=0.55,
        marker=dict(colors=["#6c63ff","#00d4aa","#ffd700","#ff6b6b",
                             "#a78bfa","#34d399","#f472b6","#60a5fa"]),
        textfont=dict(color="#e8eaf6", size=12),
        hovertemplate="<b>%{label}</b><br>%{value} skills<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=320,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9fa8da")),
        annotations=[dict(text=f"<b>{sum(cat_counts.values())}</b><br><span>skills</span>",
                          x=0.5, y=0.5, font_size=16,
                          font_color="#e8eaf6", showarrow=False)],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── TAB 4 : OPTIMIZATION ─────────────────────────────────────────────────────

def render_optimization_tab(ats_report, parsed):
    st.markdown("<h3 style='color:#e8eaf6;'>💡 ATS Optimization Guide</h3>",
                unsafe_allow_html=True)

    suggestions = ats_report.get("suggestions", [])
    if not suggestions:
        st.success("✅ Your resume is well-optimised. No major improvements needed.")
        return

    # Quick wins vs strategic
    quick  = [s for s in suggestions if "Add" in s or "Ensure" in s or "Mention" in s]
    strat  = [s for s in suggestions if s not in quick]

    q_col, s_col = st.columns(2)
    with q_col:
        st.markdown("""
        <div style="background:rgba(0,212,170,0.07); border:1px solid rgba(0,212,170,0.25);
                    border-radius:10px; padding:14px; margin-bottom:14px;">
            <h4 style="color:#00d4aa; margin:0;">⚡ Quick Wins</h4>
            <p style="color:#9fa8da; font-size:0.8rem; margin:4px 0 0;">
                Do these first — easy, high impact
            </p>
        </div>
        """, unsafe_allow_html=True)
        if quick:
            for tip in quick:
                st.markdown(f"""
                <div style="background:#1e2035; border-left:3px solid #00d4aa;
                            border-radius:0 8px 8px 0; padding:10px 14px; margin:6px 0;
                            color:#9fa8da; font-size:0.83rem;">{tip}</div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#4a5270; font-size:0.82rem;'>No quick wins identified.</p>",
                        unsafe_allow_html=True)

    with s_col:
        st.markdown("""
        <div style="background:rgba(108,99,255,0.07); border:1px solid rgba(108,99,255,0.25);
                    border-radius:10px; padding:14px; margin-bottom:14px;">
            <h4 style="color:#6c63ff; margin:0;">🗺️ Strategic Improvements</h4>
            <p style="color:#9fa8da; font-size:0.8rem; margin:4px 0 0;">
                Longer-term quality boosts
            </p>
        </div>
        """, unsafe_allow_html=True)
        if strat:
            for tip in strat:
                st.markdown(f"""
                <div style="background:#1e2035; border-left:3px solid #6c63ff;
                            border-radius:0 8px 8px 0; padding:10px 14px; margin:6px 0;
                            color:#9fa8da; font-size:0.83rem;">{tip}</div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#4a5270; font-size:0.82rem;'>No strategic items.</p>",
                        unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(108,99,255,0.12); margin:24px 0;'>",
                unsafe_allow_html=True)

    # ATS checklist
    st.markdown("<h4 style='color:#e8eaf6;'>✅ ATS Readiness Checklist</h4>",
                unsafe_allow_html=True)
    checks = [
        ("Email address present",             bool(parsed.get("email"))),
        ("Phone number present",              bool(parsed.get("phone"))),
        ("LinkedIn URL included",             bool(parsed.get("linkedin"))),
        ("GitHub URL included",              bool(parsed.get("github"))),
        ("10+ skills listed",                len(parsed.get("skills", [])) >= 10),
        ("Education clearly stated",          bool(parsed.get("education"))),
        ("Certifications mentioned",          bool(parsed.get("certifications"))),
        ("Years of experience mentioned",     parsed.get("experience_years") is not None),
        ("Resume 300+ words",                parsed.get("word_count", 0) >= 300),
        ("Resume under 900 words",           parsed.get("word_count", 0) <= 900),
    ]
    ch_a, ch_b = st.columns(2)
    for i, (item, passed) in enumerate(checks):
        col = ch_a if i % 2 == 0 else ch_b
        with col:
            icon  = "✅" if passed else "❌"
            color = "#00d4aa" if passed else "#ff6b6b"
            st.markdown(f"""
            <div style="background:#1e2035; border-radius:8px; padding:10px 14px;
                        margin:4px 0; display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.1rem;">{icon}</span>
                <span style="color:{color}; font-size:0.83rem;">{item}</span>
            </div>
            """, unsafe_allow_html=True)


# ─── TAB 5 : HISTORY ──────────────────────────────────────────────────────────

def render_history_tab(all_resumes: list):
    st.markdown("<h3 style='color:#e8eaf6;'>📈 Score History</h3>", unsafe_allow_html=True)

    if not all_resumes:
        st.info("No previous resumes found. Upload more resumes to track progress.")
        return

    # Chart
    st.plotly_chart(make_history_chart(all_resumes), use_container_width=True,
                    config={"displayModeBar": False})

    # Table
    st.markdown("<h4 style='color:#e8eaf6; margin-top:20px;'>📋 All Uploads</h4>",
                unsafe_allow_html=True)
    for r in all_resumes:
        s = r["ats_score"] or 0
        c = ats_color(s)
        cat = r["ats_category"] or "—"
        role = r["predicted_role"] or "—"
        date = str(r["uploaded_at"])[:10]
        fname = r["filename"] or "resume"

        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.18);
                    border-radius:12px; padding:14px 20px; margin:6px 0;
                    display:flex; align-items:center; justify-content:space-between;">
            <div>
                <div style="font-weight:600; color:#e8eaf6; font-size:0.9rem;">📄 {fname}</div>
                <div style="color:#9fa8da; font-size:0.78rem; margin-top:3px;">
                    🎯 {role} &nbsp;|&nbsp; 📅 {date}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.5rem; font-weight:800; color:{c};">{s:.0f}</div>
                <div style="color:{c}; font-size:0.72rem; font-weight:600;">{cat}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Stats summary
    if len(all_resumes) > 1:
        scores = [r["ats_score"] or 0 for r in all_resumes]
        st.markdown("<br>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        kpi_card(s1, "Best Score",    f"{max(scores):.0f}",                     "#00d4aa", "🏆")
        kpi_card(s2, "Latest Score",  f"{scores[0]:.0f}",                       "#6c63ff", "📊")
        kpi_card(s3, "Average Score", f"{sum(scores)/len(scores):.1f}",         "#ffd700", "📈")
        kpi_card(s4, "Total Uploads", len(all_resumes),                          "#9fa8da", "📄")


# ─── TAB 6 : FULL REPORT ──────────────────────────────────────────────────────

def render_full_report_tab(ats_report, parsed):
    st.markdown("<h3 style='color:#e8eaf6;'>📋 Full ATS Report</h3>", unsafe_allow_html=True)

    score = ats_report["total_score"]
    cat   = ats_report["category"]
    color = ats_color(score)

    report_md = f"""
# ATS Resume Analysis Report
**Generated by HireSenseAI**

---

## Candidate Summary
| Field | Value |
|-------|-------|
| Name | {parsed.get('name') or '—'} |
| Email | {parsed.get('email') or '—'} |
| Phone | {parsed.get('phone') or '—'} |
| LinkedIn | {parsed.get('linkedin') or '—'} |
| GitHub | {parsed.get('github') or '—'} |
| Experience | {f"{parsed.get('experience_years')} years" if parsed.get('experience_years') else '—'} |

---

## ATS Score
**Total Score: {score:.0f} / 100 — {cat}**

### Breakdown
| Criterion | Score | Weight | Note |
|-----------|-------|--------|------|
"""
    for crit, data in ats_report.get("breakdown", {}).items():
        report_md += f"| {crit} | {data['score']:.0f}/100 | {data['weight']}% | {data.get('note','')} |\n"

    report_md += f"""
---

## Skills Detected ({len(parsed.get('skills', []))})
{', '.join(parsed.get('skills', [])) or 'None detected'}

## Missing Keywords
{', '.join(ats_report.get('missing_keywords', [])) or 'None'}

## Education
{', '.join(parsed.get('education', [])) or 'Not detected'}

## Certifications
{', '.join(parsed.get('certifications', [])) or 'None'}

---

## Improvement Suggestions
"""
    for tip in ats_report.get("suggestions", []):
        report_md += f"- {tip}\n"

    st.markdown(f"""
    <div style="background:#0d0f1a; border:1px solid rgba(108,99,255,0.2);
                border-radius:12px; padding:24px; max-height:520px; overflow-y:auto;
                font-family:'JetBrains Mono', monospace; font-size:0.82rem;
                color:#9fa8da; line-height:1.8; white-space:pre-wrap;">{report_md}</div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="⬇️ Download Report (.md)",
        data=report_md,
        file_name="ats_report.md",
        mime="text/markdown",
        use_container_width=True,
    )


# ─── UTILITY ──────────────────────────────────────────────────────────────────

def _hex_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    return "108,99,255"
