"""
Analytics Page
Personal analytics dashboard with ATS trends, skill distribution,
resume completeness, role predictions history, and progress tracking.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.database import get_user_resumes, get_resume_stats
from utils.resume_parser import SKILLS_DB


# ─── PLOTLY THEME ─────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk, sans-serif", color="#9fa8da"),
    margin=dict(l=20, r=20, t=40, b=20),
)

PALETTE = ["#6c63ff", "#00d4aa", "#ffd700", "#ff6b6b",
           "#a78bfa", "#34d399", "#f472b6", "#60a5fa",
           "#fb923c", "#e879f9"]


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def ats_color(score: float) -> str:
    if score >= 80:   return "#00d4aa"
    elif score >= 65: return "#6c63ff"
    elif score >= 45: return "#ffd700"
    return "#ff6b6b"


def kpi_card(col, label, value, color="#6c63ff", icon="📊", sub=None):
    with col:
        sub_html = (f"<div style='color:#4a5270; font-size:0.7rem; margin-top:2px;'>{sub}</div>"
                    if sub else "")
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                    border-radius:12px; padding:16px; text-align:center; height:100%;">
            <div style="font-size:1.5rem;">{icon}</div>
            <div style="font-size:1.5rem; font-weight:800; color:{color};
                        line-height:1.2; margin-top:4px;">{value}</div>
            <div style="color:#9fa8da; font-size:0.75rem; margin-top:4px;">{label}</div>
            {sub_html}
        </div>
        """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin:28px 0 16px;">
        <h3 style="color:#e8eaf6; margin:0; font-size:1.1rem;">{title}</h3>
        {"<p style='color:#9fa8da; font-size:0.8rem; margin:4px 0 0;'>" + subtitle + "</p>"
         if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


# ─── CHARTS ───────────────────────────────────────────────────────────────────

def make_ats_timeline(resumes: list) -> go.Figure:
    """Line chart of ATS score over upload history."""
    labels = [f"#{i+1}" for i in range(len(resumes))]
    scores = [r["ats_score"] or 0 for r in reversed(resumes)]
    dates  = [str(r["uploaded_at"])[:10] for r in reversed(resumes)]
    colors = [ats_color(s) for s in scores]

    fig = go.Figure()

    # Shaded area
    fig.add_trace(go.Scatter(
        x=labels, y=scores,
        fill="tozeroy",
        fillcolor="rgba(108,99,255,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False, hoverinfo="skip",
    ))

    # Main line
    fig.add_trace(go.Scatter(
        x=labels, y=scores,
        mode="lines+markers+text",
        line=dict(color="#6c63ff", width=3, shape="spline"),
        marker=dict(size=10, color=colors,
                    line=dict(color="#161829", width=2)),
        text=[f"{s:.0f}" for s in scores],
        textposition="top center",
        textfont=dict(color="#e8eaf6", size=11),
        customdata=dates,
        hovertemplate="<b>Upload %{x}</b><br>Score: %{y:.1f}<br>Date: %{customdata}<extra></extra>",
        name="ATS Score",
    ))

    # Threshold lines
    fig.add_hline(y=80, line_dash="dot", line_color="#00d4aa", line_width=1,
                  annotation_text="Excellent (80)", annotation_font_color="#00d4aa",
                  annotation_font_size=11)
    fig.add_hline(y=65, line_dash="dot", line_color="#6c63ff", line_width=1,
                  annotation_text="Good (65)", annotation_font_color="#6c63ff",
                  annotation_font_size=11)
    fig.add_hline(y=45, line_dash="dot", line_color="#ffd700", line_width=1,
                  annotation_text="Average (45)", annotation_font_color="#ffd700",
                  annotation_font_size=11)

    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="#2a2d45", title="Upload #"),
        yaxis=dict(range=[0, 110], gridcolor="#2a2d45", title="ATS Score"),
        height=320,
        showlegend=False,
    )
    return fig


def make_score_distribution(resumes: list) -> go.Figure:
    """Histogram of ATS score distribution."""
    scores = [r["ats_score"] or 0 for r in resumes]

    fig = go.Figure(go.Histogram(
        x=scores,
        nbinsx=10,
        marker=dict(
            color=scores,
            colorscale=[[0, "#ff6b6b"], [0.45, "#ffd700"],
                        [0.65, "#6c63ff"], [1, "#00d4aa"]],
            line=dict(color="#161829", width=1),
        ),
        hovertemplate="Score range: %{x}<br>Count: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(title="ATS Score", gridcolor="#2a2d45"),
        yaxis=dict(title="Frequency", gridcolor="#2a2d45"),
        height=280,
        bargap=0.05,
    )
    return fig


def make_role_distribution(resumes: list) -> go.Figure:
    """Pie/donut of predicted roles."""
    role_counts = {}
    for r in resumes:
        role = r["predicted_role"] or "Unknown"
        role_counts[role] = role_counts.get(role, 0) + 1

    labels = list(role_counts.keys())
    values = list(role_counts.values())

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(
            colors=PALETTE[:len(labels)],
            line=dict(color="#161829", width=3),
        ),
        textfont=dict(color="#e8eaf6", size=12),
        hovertemplate="<b>%{label}</b><br>%{value} resumes (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9fa8da", size=11)),
        annotations=[dict(
            text=f"<b>{len(resumes)}</b><br>uploads",
            x=0.5, y=0.5, font_size=15, font_color="#e8eaf6", showarrow=False,
        )],
    )
    return fig


def make_category_gauge_row(resumes: list):
    """Four mini-gauges for each ATS category."""
    cats = {"Excellent": 0, "Good": 0, "Average": 0, "Poor": 0}
    for r in resumes:
        cat = r["ats_category"] or "Poor"
        if cat in cats:
            cats[cat] += 1

    total = len(resumes) or 1
    cat_colors = {"Excellent": "#00d4aa", "Good": "#6c63ff",
                  "Average": "#ffd700", "Poor": "#ff6b6b"}
    cat_icons  = {"Excellent": "🏆", "Good": "✅", "Average": "⚠️", "Poor": "❌"}

    cols = st.columns(4)
    for col, (cat, count) in zip(cols, cats.items()):
        pct   = round(count / total * 100, 1)
        color = cat_colors[cat]
        icon  = cat_icons[cat]
        with col:
            st.markdown(f"""
            <div style="background:#1e2035; border:1px solid {color}30;
                        border-radius:12px; padding:16px; text-align:center;">
                <div style="font-size:1.5rem;">{icon}</div>
                <div style="font-size:1.6rem; font-weight:800; color:{color};">{count}</div>
                <div style="color:#9fa8da; font-size:0.78rem;">{cat}</div>
                <div style="background:rgba(255,255,255,0.07); border-radius:5px;
                            height:6px; margin-top:8px; overflow:hidden;">
                    <div style="background:{color}; width:{pct}%; height:100%;
                                border-radius:5px;"></div>
                </div>
                <div style="color:{color}; font-size:0.72rem; margin-top:4px;">{pct}%</div>
            </div>
            """, unsafe_allow_html=True)


def make_skill_category_radar(skills: list) -> go.Figure:
    """Radar chart of skill coverage by category."""
    skill_set = set(s.lower() for s in skills)
    categories = []
    percentages = []

    for cat, cat_skills in SKILLS_DB.items():
        if cat == "soft_skills":
            continue
        matched = sum(1 for s in cat_skills if s in skill_set)
        pct = round(matched / len(cat_skills) * 100, 1) if cat_skills else 0
        categories.append(cat.replace("_", " ").title())
        percentages.append(pct)

    if not categories:
        return go.Figure()

    categories += [categories[0]]
    percentages += [percentages[0]]

    fig = go.Figure(go.Scatterpolar(
        r=percentages,
        theta=categories,
        fill="toself",
        fillcolor="rgba(0,212,170,0.12)",
        line=dict(color="#00d4aa", width=2),
        marker=dict(size=7, color="#6c63ff"),
        hovertemplate="<b>%{theta}</b><br>Coverage: %{r:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        polar=dict(
            bgcolor="rgba(22,24,41,0.6)",
            radialaxis=dict(visible=True, range=[0, 100],
                            gridcolor="#2a2d45", tickfont={"color": "#9fa8da"}),
            angularaxis=dict(gridcolor="#2a2d45",
                             tickfont={"color": "#e8eaf6", "size": 10}),
        ),
        height=340,
    )
    return fig


def make_skill_bar(skills: list) -> go.Figure:
    """Horizontal bar showing skill count per category."""
    skill_set = set(s.lower() for s in skills)
    cats, counts, totals = [], [], []

    for cat, cat_skills in SKILLS_DB.items():
        if cat == "soft_skills":
            continue
        matched = sum(1 for s in cat_skills if s in skill_set)
        cats.append(cat.replace("_", " ").title())
        counts.append(matched)
        totals.append(len(cat_skills))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Skills You Have",
        y=cats, x=counts,
        orientation="h",
        marker=dict(color="#6c63ff", opacity=0.85),
        text=counts, textposition="inside",
        textfont=dict(color="white"),
    ))
    fig.add_trace(go.Bar(
        name="Remaining",
        y=cats, x=[t - c for t, c in zip(totals, counts)],
        orientation="h",
        marker=dict(color="rgba(255,255,255,0.06)"),
        hovertemplate="Remaining: %{x}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="stack",
        xaxis=dict(gridcolor="#2a2d45", title="Skill Count"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=300,
        legend=dict(bgcolor="rgba(0,0,0,0)", x=0.5, y=1.1,
                    orientation="h", font=dict(color="#9fa8da")),
    )
    return fig


def make_completeness_meter(parsed: dict) -> go.Figure:
    """Waterfall-style bar showing resume section completeness."""
    sections = {
        "Name":          bool(parsed.get("name")),
        "Email":         bool(parsed.get("email")),
        "Phone":         bool(parsed.get("phone")),
        "LinkedIn":      bool(parsed.get("linkedin")),
        "GitHub":        bool(parsed.get("github")),
        "Skills (10+)":  len(parsed.get("skills", [])) >= 10,
        "Education":     bool(parsed.get("education")),
        "Experience":    parsed.get("experience_years") is not None,
        "Certifications":bool(parsed.get("certifications")),
        "Content Depth": parsed.get("word_count", 0) >= 300,
    }

    labels = list(sections.keys())
    values = [100 if v else 0 for v in sections.values()]
    colors = ["#00d4aa" if v else "#ff6b6b" for v in sections.values()]
    icons  = ["✅" if v else "❌" for v in sections.values()]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=icons,
        textposition="outside",
        textfont=dict(size=14),
        hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
    ))
    completeness = round(sum(sections.values()) / len(sections) * 100, 1)
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(tickangle=-30, gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(range=[0, 130], visible=False),
        height=280,
        title=dict(
            text=f"Resume Completeness: <b>{completeness:.0f}%</b>",
            font=dict(color="#e8eaf6", size=14), x=0.5,
        ),
    )
    return fig


def make_confidence_trend(resumes: list) -> go.Figure:
    """Bar chart of confidence scores per upload."""
    labels = [f"#{i+1}" for i in range(len(resumes))]
    confs  = [r["confidence_score"] or 0 for r in reversed(resumes)]
    colors = ["#00d4aa" if c >= 70 else "#6c63ff" if c >= 50
              else "#ffd700" if c >= 35 else "#ff6b6b" for c in confs]

    fig = go.Figure(go.Bar(
        x=labels, y=confs,
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=[f"{c:.0f}%" for c in confs],
        textposition="outside",
        textfont=dict(color="#e8eaf6", size=11),
        hovertemplate="Upload %{x}<br>Confidence: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="rgba(0,0,0,0)", title="Upload #"),
        yaxis=dict(range=[0, 115], gridcolor="#2a2d45", title="Confidence %"),
        height=280,
    )
    return fig


def make_upload_timeline(resumes: list) -> go.Figure:
    """Scatter plot of uploads over time."""
    from collections import Counter

    dates  = [str(r["uploaded_at"])[:10] for r in resumes]
    counts = Counter(dates)
    sorted_dates = sorted(counts.keys())
    vals = [counts[d] for d in sorted_dates]

    fig = go.Figure(go.Scatter(
        x=sorted_dates, y=vals,
        mode="lines+markers",
        line=dict(color="#6c63ff", width=2, shape="spline"),
        marker=dict(size=9, color="#00d4aa",
                    line=dict(color="#161829", width=2)),
        fill="tozeroy",
        fillcolor="rgba(108,99,255,0.08)",
        hovertemplate="Date: %{x}<br>Uploads: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="#2a2d45", title="Date"),
        yaxis=dict(gridcolor="#2a2d45", title="Uploads", dtick=1),
        height=240,
    )
    return fig


# ─── MAIN PAGE ────────────────────────────────────────────────────────────────

def show():
    user        = st.session_state.user
    resumes     = get_user_resumes(user["id"])
    parsed      = st.session_state.get("resume_parsed")
    prediction  = st.session_state.get("prediction")
    ats_report  = st.session_state.get("ats_report")

    st.markdown("""
    <h1 style='color:#e8eaf6; margin-bottom:4px;'>📈 Analytics Dashboard</h1>
    <p style='color:#9fa8da; margin-bottom:28px;'>
        Track your resume progress, skill growth, and ATS performance over time.
    </p>
    """, unsafe_allow_html=True)

    # ── No data ───────────────────────────────────────────────────────────
    if not resumes:
        render_no_data()
        return

    # ── Summary KPIs ──────────────────────────────────────────────────────
    scores     = [r["ats_score"] or 0 for r in resumes]
    avg_ats    = round(sum(scores) / len(scores), 1)
    best_ats   = max(scores)
    latest_ats = scores[0]
    improvement = round(latest_ats - scores[-1], 1) if len(scores) > 1 else 0
    total_skills = len(parsed.get("skills", [])) if parsed else 0
    top_role   = resumes[0]["predicted_role"] or "—"

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpi_card(k1, "Total Uploads",    len(resumes),        "#6c63ff",    "📄")
    kpi_card(k2, "Latest ATS",       f"{latest_ats:.0f}", ats_color(latest_ats), "📊",
             sub=resumes[0]["ats_category"] or "—")
    kpi_card(k3, "Best Score",       f"{best_ats:.0f}",   "#00d4aa",    "🏆")
    kpi_card(k4, "Average Score",    f"{avg_ats:.1f}",    "#ffd700",    "📈")
    kpi_card(k5, "Skills Detected",  total_skills,        "#a78bfa",    "🛠️")
    kpi_card(k6, "Top Role Match",   top_role[:12] + ("…" if len(top_role) > 12 else ""),
             "#00d4aa", "🎯")

    st.markdown("<hr style='border-color:rgba(108,99,255,0.15); margin:24px 0;'>",
                unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "📊 ATS Trends",
        "🛠️ Skill Analytics",
        "🎯 Role Analytics",
        "📋 Resume Health",
        "🏅 Progress Report",
    ])

    with tabs[0]: render_ats_trends_tab(resumes, scores, avg_ats, best_ats, improvement)
    with tabs[1]: render_skill_analytics_tab(parsed)
    with tabs[2]: render_role_analytics_tab(resumes, prediction)
    with tabs[3]: render_resume_health_tab(parsed, ats_report)
    with tabs[4]: render_progress_tab(resumes, parsed, prediction)


# ─── NO DATA ──────────────────────────────────────────────────────────────────

def render_no_data():
    st.markdown("""
    <div style="background:#161829; border:2px dashed rgba(108,99,255,0.35);
                border-radius:16px; padding:56px; text-align:center;">
        <div style="font-size:3.5rem;">📊</div>
        <h3 style="color:#9fa8da; margin-top:12px;">No Analytics Data Yet</h3>
        <p style="color:#4a5270;">Upload at least one resume to start seeing your analytics.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📤 Upload Resume Now", use_container_width=True):
        st.session_state.page = "upload"
        st.rerun()


# ─── TAB 1 : ATS TRENDS ───────────────────────────────────────────────────────

def render_ats_trends_tab(resumes, scores, avg_ats, best_ats, improvement):
    section_header("📈 ATS Score Over Time",
                   "Track how your score improves with each resume iteration.")

    # Score timeline
    if len(resumes) > 1:
        st.plotly_chart(make_ats_timeline(resumes), use_container_width=True,
                        config={"displayModeBar": False})
    else:
        st.info("Upload more resumes to see score trends over time.")
        # Single score gauge
        score = scores[0]
        color = ats_color(score)
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid {color}40;
                    border-radius:16px; padding:32px; text-align:center; max-width:300px;
                    margin:20px auto;">
            <div style="font-size:4rem; font-weight:800; color:{color};">{score:.0f}</div>
            <div style="color:#9fa8da;">Your ATS Score</div>
            <div style="background:rgba(255,255,255,0.08); border-radius:8px; height:10px;
                        overflow:hidden; margin-top:14px;">
                <div style="background:{color}; width:{score:.0f}%; height:100%;
                            border-radius:8px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Category distribution + score histogram
    dist_col, hist_col = st.columns(2)

    with dist_col:
        section_header("🏷️ Category Distribution", "How your resumes are rated")
        make_category_gauge_row(resumes)

    with hist_col:
        section_header("📊 Score Distribution", "Frequency of different score ranges")
        if len(resumes) > 2:
            st.plotly_chart(make_score_distribution(resumes), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("Upload 3+ resumes to see score distribution.")

    # Improvement insight
    if len(scores) > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        delta  = round(scores[0] - scores[-1], 1)
        d_color = "#00d4aa" if delta >= 0 else "#ff6b6b"
        d_icon  = "📈" if delta >= 0 else "📉"
        d_text  = f"+{delta}" if delta >= 0 else str(delta)
        st.markdown(f"""
        <div style="background:rgba({_hex_rgb(d_color)},0.08);
                    border:1px solid {d_color}40; border-radius:14px;
                    padding:20px 24px; display:flex; align-items:center; gap:20px;">
            <div style="font-size:2.5rem;">{d_icon}</div>
            <div>
                <div style="font-weight:700; color:{d_color}; font-size:1rem;">
                    Score Change: {d_text} points
                </div>
                <div style="color:#9fa8da; font-size:0.82rem; margin-top:4px;">
                    From your first upload ({scores[-1]:.0f}) to latest ({scores[0]:.0f}).
                    {"Keep improving!" if delta >= 0 else "Focus on the suggestions tab."}
                </div>
            </div>
            <div style="margin-left:auto; text-align:right;">
                <div style="color:#9fa8da; font-size:0.75rem;">Best Score</div>
                <div style="font-size:1.6rem; font-weight:800; color:#00d4aa;">
                    {best_ats:.0f}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─── TAB 2 : SKILL ANALYTICS ──────────────────────────────────────────────────

def render_skill_analytics_tab(parsed):
    section_header("🛠️ Skill Analytics",
                   "Coverage and distribution of your technical skills.")

    if not parsed:
        st.info("Upload and analyse a resume to see skill analytics.")
        if st.button("📤 Upload Resume", use_container_width=True):
            st.session_state.page = "upload"
            st.rerun()
        return

    skills    = parsed.get("skills", [])
    skill_set = set(s.lower() for s in skills)

    # Total skills KPIs
    total_possible = sum(len(v) for k, v in SKILLS_DB.items() if k != "soft_skills")
    coverage_pct   = round(len(skills) / total_possible * 100, 1)

    s1, s2, s3, s4 = st.columns(4)
    kpi_card(s1, "Total Skills",      len(skills),         "#6c63ff",    "🛠️")
    kpi_card(s2, "DB Coverage",       f"{coverage_pct}%",  "#00d4aa",    "📊")
    kpi_card(s3, "Certifications",    len(parsed.get("certifications", [])), "#ffd700", "🏆")
    kpi_card(s4, "Education Levels",  len(parsed.get("education", [])),      "#a78bfa", "🎓")

    st.markdown("<br>", unsafe_allow_html=True)
    radar_col, bar_col = st.columns(2)

    with radar_col:
        section_header("🕸️ Skill Radar", "Coverage per category")
        if skills:
            st.plotly_chart(make_skill_category_radar(skills), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No skills detected.")

    with bar_col:
        section_header("📊 Category Breakdown", "Skills matched vs total in each category")
        if skills:
            st.plotly_chart(make_skill_bar(skills), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No skills detected.")

    # All skills list
    if skills:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("📋 All Detected Skills", f"{len(skills)} skills found in your resume")

        # Group by category
        for cat, cat_skills in SKILLS_DB.items():
            matched = [s for s in cat_skills if s in skill_set]
            if not matched:
                continue
            cat_label = cat.replace("_", " ").title()
            cat_color = {
                "programming": "#6c63ff", "web": "#00d4aa", "data_science": "#ffd700",
                "databases": "#ff6b6b", "cloud_devops": "#a78bfa", "tools": "#34d399",
                "security": "#f472b6", "soft_skills": "#60a5fa",
            }.get(cat, "#9fa8da")

            with st.expander(f"{cat_label} ({len(matched)} skills)", expanded=False):
                pills = "".join(
                    f"<span style='background:{cat_color}18; color:{cat_color}; "
                    f"border:1px solid {cat_color}50; padding:3px 10px; "
                    f"border-radius:20px; font-size:0.78rem; margin:3px; "
                    f"display:inline-block;'>{s}</span>"
                    for s in matched
                )
                st.markdown(f"<div style='line-height:2.2; padding:4px 0;'>{pills}</div>",
                            unsafe_allow_html=True)


# ─── TAB 3 : ROLE ANALYTICS ───────────────────────────────────────────────────

def render_role_analytics_tab(resumes, prediction):
    section_header("🎯 Role Prediction Analytics",
                   "Breakdown of predicted roles across all your resume uploads.")

    role_col, conf_col = st.columns(2)

    with role_col:
        section_header("📊 Role Distribution", "Which roles your resumes match")
        if len(resumes) > 1:
            st.plotly_chart(make_role_distribution(resumes), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            # Single prediction display
            if prediction:
                role       = prediction["predicted_role"]
                conf       = prediction["confidence"]
                icon       = prediction.get("icon", "💼")
                conf_color = "#00d4aa" if conf >= 70 else "#6c63ff" if conf >= 50 else "#ffd700"
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,rgba(108,99,255,0.15),
                            rgba(0,212,170,0.1)); border:1px solid rgba(108,99,255,0.4);
                            border-radius:16px; padding:28px; text-align:center;">
                    <div style="font-size:3rem;">{icon}</div>
                    <div style="font-size:1.3rem; font-weight:700; color:#e8eaf6; margin-top:10px;">
                        {role}
                    </div>
                    <div style="font-size:2rem; font-weight:800; color:{conf_color}; margin-top:8px;">
                        {conf:.1f}%
                    </div>
                    <div style="color:#9fa8da; font-size:0.8rem;">AI Confidence</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No prediction available yet.")

    with conf_col:
        section_header("📈 Confidence Trend", "Prediction confidence per upload")
        if len(resumes) > 0:
            st.plotly_chart(make_confidence_trend(resumes), use_container_width=True,
                            config={"displayModeBar": False})

    # Role history table
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("📋 Prediction History", "All predictions across uploads")

    header_cols = st.columns([2, 2, 1.5, 1.5, 2])
    headers = ["📄 File", "🎯 Role", "🤖 Confidence", "📊 ATS", "📅 Date"]
    for col, h in zip(header_cols, headers):
        with col:
            st.markdown(f"<div style='color:#6c63ff; font-size:0.78rem; font-weight:700;'>"
                        f"{h}</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(108,99,255,0.15); margin:6px 0;'>",
                unsafe_allow_html=True)

    for r in resumes:
        conf    = r["confidence_score"] or 0
        score   = r["ats_score"] or 0
        c_color = "#00d4aa" if conf >= 70 else "#6c63ff" if conf >= 50 else "#ffd700"
        s_color = ats_color(score)
        fname   = (r["filename"] or "resume")[:22]
        role    = (r["predicted_role"] or "—")[:20]
        date    = str(r["uploaded_at"])[:10]

        row_cols = st.columns([2, 2, 1.5, 1.5, 2])
        with row_cols[0]:
            st.markdown(f"<span style='color:#e8eaf6; font-size:0.82rem;'>📄 {fname}</span>",
                        unsafe_allow_html=True)
        with row_cols[1]:
            st.markdown(f"<span style='color:#9fa8da; font-size:0.82rem;'>{role}</span>",
                        unsafe_allow_html=True)
        with row_cols[2]:
            st.markdown(f"<span style='color:{c_color}; font-weight:700; font-size:0.82rem;'>"
                        f"{conf:.0f}%</span>", unsafe_allow_html=True)
        with row_cols[3]:
            st.markdown(f"<span style='color:{s_color}; font-weight:700; font-size:0.82rem;'>"
                        f"{score:.0f}</span>", unsafe_allow_html=True)
        with row_cols[4]:
            st.markdown(f"<span style='color:#4a5270; font-size:0.78rem;'>{date}</span>",
                        unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(108,99,255,0.08); margin:4px 0;'>",
                    unsafe_allow_html=True)


# ─── TAB 4 : RESUME HEALTH ────────────────────────────────────────────────────

def render_resume_health_tab(parsed, ats_report):
    section_header("📋 Resume Health Check",
                   "How complete and well-structured your current resume is.")

    if not parsed:
        st.info("Upload and analyse a resume to see health metrics.")
        if st.button("📤 Upload Resume", use_container_width=True, key="health_upload"):
            st.session_state.page = "upload"
            st.rerun()
        return

    # Completeness chart
    st.plotly_chart(make_completeness_meter(parsed), use_container_width=True,
                    config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # Detailed health cards
    checks = [
        ("📧 Email",          bool(parsed.get("email")),
         parsed.get("email") or "Not found",          "Contact"),
        ("📞 Phone",          bool(parsed.get("phone")),
         parsed.get("phone") or "Not found",          "Contact"),
        ("🔗 LinkedIn",       bool(parsed.get("linkedin")),
         parsed.get("linkedin") or "Not found",       "Profile"),
        ("💻 GitHub",         bool(parsed.get("github")),
         parsed.get("github") or "Not found",         "Profile"),
        ("🛠️ Skills (10+)",   len(parsed.get("skills", [])) >= 10,
         f"{len(parsed.get('skills',[]))} detected",   "Skills"),
        ("🎓 Education",      bool(parsed.get("education")),
         ", ".join(parsed.get("education", [])) or "Not found", "Background"),
        ("🏆 Certifications", bool(parsed.get("certifications")),
         ", ".join(parsed.get("certifications", []))  or "None found", "Credentials"),
        ("⏱️ Experience",     parsed.get("experience_years") is not None,
         f"{parsed.get('experience_years')} years" if parsed.get("experience_years")
         else "Not stated", "Experience"),
        ("📝 Word Count",     300 <= parsed.get("word_count", 0) <= 900,
         f"{parsed.get('word_count', 0)} words (ideal: 300-900)", "Formatting"),
        ("👤 Name Detected",  bool(parsed.get("name")),
         parsed.get("name") or "Not detected", "Identity"),
    ]

    passed = sum(1 for _, ok, _, _ in checks if ok)
    total  = len(checks)
    health_pct = round(passed / total * 100)
    h_color = "#00d4aa" if health_pct >= 80 else "#6c63ff" if health_pct >= 60 \
              else "#ffd700" if health_pct >= 40 else "#ff6b6b"

    # Health score banner
    st.markdown(f"""
    <div style="background:rgba({_hex_rgb(h_color)},0.08); border:1px solid {h_color}40;
                border-radius:14px; padding:18px 24px; margin-bottom:20px;
                display:flex; align-items:center; gap:20px;">
        <div style="font-size:2.8rem; font-weight:800; color:{h_color};">{health_pct}%</div>
        <div>
            <div style="color:#e8eaf6; font-weight:700; font-size:1rem;">
                Resume Health Score
            </div>
            <div style="color:#9fa8da; font-size:0.82rem; margin-top:3px;">
                {passed}/{total} checks passed ·
                {"Excellent! 🏆" if health_pct >= 80
                 else "Good, a few gaps 👍" if health_pct >= 60
                 else "Needs improvement ⚠️" if health_pct >= 40
                 else "Major issues found ❌"}
            </div>
        </div>
        <div style="margin-left:auto; min-width:140px;">
            <div style="background:rgba(255,255,255,0.08); border-radius:8px;
                        height:12px; overflow:hidden;">
                <div style="background:{h_color}; width:{health_pct}%; height:100%;
                            border-radius:8px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Health check grid
    col_a, col_b = st.columns(2)
    for i, (label, ok, detail, category) in enumerate(checks):
        col = col_a if i % 2 == 0 else col_b
        color  = "#00d4aa" if ok else "#ff6b6b"
        bg     = "rgba(0,212,170,0.06)" if ok else "rgba(255,107,107,0.06)"
        border = "rgba(0,212,170,0.25)" if ok else "rgba(255,107,107,0.25)"
        icon   = "✅" if ok else "❌"
        with col:
            st.markdown(f"""
            <div style="background:{bg}; border:1px solid {border};
                        border-radius:10px; padding:12px 16px; margin:5px 0;">
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <div style="color:#e8eaf6; font-weight:600; font-size:0.85rem;">
                        {label}
                    </div>
                    <span style="font-size:1rem;">{icon}</span>
                </div>
                <div style="color:#9fa8da; font-size:0.75rem; margin-top:4px;
                            word-break:break-all;">{detail[:60]}</div>
                <div style="color:{color}; font-size:0.7rem; margin-top:2px;
                            font-weight:600;">{category}</div>
            </div>
            """, unsafe_allow_html=True)


# ─── TAB 5 : PROGRESS REPORT ──────────────────────────────────────────────────

def render_progress_tab(resumes, parsed, prediction):
    section_header("🏅 Progress Report",
                   "A summary of your overall career readiness and growth.")

    scores = [r["ats_score"] or 0 for r in resumes]
    latest = scores[0] if scores else 0

    # Upload activity timeline
    section_header("📅 Upload Activity", "When you submitted resumes")
    if len(resumes) > 1:
        st.plotly_chart(make_upload_timeline(resumes), use_container_width=True,
                        config={"displayModeBar": False})
    else:
        st.info("Upload more resumes to see activity timeline.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Career readiness score (composite)
    skill_score = min(len(parsed.get("skills", [])) / 12 * 100, 100) if parsed else 0
    contact_score = (sum([
        bool(parsed.get("email")),
        bool(parsed.get("phone")),
        bool(parsed.get("linkedin")),
        bool(parsed.get("github")),
    ]) / 4 * 100) if parsed else 0
    edu_score  = 70 if parsed and parsed.get("education") else 20
    cert_score = min(len(parsed.get("certifications", [])) * 30, 100) if parsed else 0
    conf_score = prediction.get("confidence", 0) if prediction else 0

    readiness = round(
        (latest * 0.30) +
        (skill_score * 0.25) +
        (contact_score * 0.15) +
        (edu_score * 0.15) +
        (cert_score * 0.10) +
        (conf_score * 0.05)
    , 1)

    r_color = ats_color(readiness)
    r_label = ("🏆 Job Ready" if readiness >= 80
               else "✅ Almost Ready" if readiness >= 65
               else "⚠️ In Progress" if readiness >= 45
               else "🔴 Needs Work")

    section_header("⚡ Career Readiness Score", "Composite score across all dimensions")

    left_r, right_r = st.columns([1, 1.5])
    with left_r:
        st.markdown(f"""
        <div style="background:#1e2035; border:2px solid {r_color}50;
                    border-radius:20px; padding:32px; text-align:center;">
            <div style="font-size:5rem; font-weight:800; color:{r_color}; line-height:1;">
                {readiness:.0f}
            </div>
            <div style="color:#9fa8da; font-size:0.85rem; margin-top:6px;">
                out of 100
            </div>
            <div style="margin-top:16px; font-size:1rem; font-weight:700; color:{r_color};">
                {r_label}
            </div>
            <div style="background:rgba(255,255,255,0.08); border-radius:8px;
                        height:10px; overflow:hidden; margin-top:16px;">
                <div style="background:linear-gradient(90deg,#6c63ff,{r_color});
                            width:{readiness:.0f}%; height:100%; border-radius:8px;">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right_r:
        components = [
            ("ATS Score",       latest,        0.30, "#6c63ff"),
            ("Skill Coverage",  skill_score,   0.25, "#00d4aa"),
            ("Contact Info",    contact_score, 0.15, "#ffd700"),
            ("Education",       edu_score,     0.15, "#a78bfa"),
            ("Certifications",  cert_score,    0.10, "#ff6b6b"),
            ("Role Confidence", conf_score,    0.05, "#34d399"),
        ]
        st.markdown("<h4 style='color:#e8eaf6; margin-bottom:14px;'>Score Components</h4>",
                    unsafe_allow_html=True)
        for name, val, weight, color in components:
            contrib = round(val * weight, 1)
            st.markdown(f"""
            <div style="margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:#9fa8da; font-size:0.8rem;">{name}</span>
                    <span style="color:{color}; font-size:0.8rem; font-weight:700;">
                        {val:.0f} × {weight} = +{contrib}
                    </span>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:5px;
                            height:7px; overflow:hidden;">
                    <div style="background:{color}; width:{val:.0f}%; height:100%;
                                border-radius:5px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Next steps
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("🎯 Recommended Next Steps")

    next_steps = []
    if latest < 65:
        next_steps.append(("📊", "Improve ATS Score",
                           "Focus on ATS Analysis tab for keyword and formatting fixes."))
    if skill_score < 60:
        next_steps.append(("🛠️", "Add More Skills",
                           "Learn and add at least 5 more relevant technical skills."))
    if not parsed or not parsed.get("linkedin"):
        next_steps.append(("🔗", "Add LinkedIn",
                           "LinkedIn URL on your resume boosts recruiter trust significantly."))
    if not parsed or not parsed.get("github"):
        next_steps.append(("💻", "Add GitHub",
                           "Showcase your code — employers look for evidence of real work."))
    if cert_score < 30:
        next_steps.append(("🏆", "Get Certified",
                           "Add at least one industry certification relevant to your role."))
    if not next_steps:
        next_steps.append(("🎉", "You're Doing Great!",
                           "Keep applying! Your resume is well-optimised."))

    step_cols = st.columns(min(len(next_steps), 3))
    for i, (icon, title, detail) in enumerate(next_steps[:3]):
        with step_cols[i]:
            st.markdown(f"""
            <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                        border-radius:12px; padding:18px; text-align:center;
                        min-height:130px;">
                <div style="font-size:1.8rem;">{icon}</div>
                <div style="font-weight:700; color:#e8eaf6; margin-top:8px;
                            font-size:0.88rem;">{title}</div>
                <div style="color:#9fa8da; font-size:0.78rem; margin-top:6px;
                            line-height:1.5;">{detail}</div>
            </div>
            """, unsafe_allow_html=True)


# ─── UTILITY ──────────────────────────────────────────────────────────────────

def _hex_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    return "108,99,255"
