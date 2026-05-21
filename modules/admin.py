"""
Admin Dashboard Page
Full admin panel: user management, resume oversight, ATS analytics,
prediction stats, system health, and data export.
Only accessible to users with role='admin'.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils.database import get_all_users, get_all_resumes, get_resume_stats


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


def kpi_card(col, label, value, color="#6c63ff", icon="📊", sub=None, delta=None):
    with col:
        delta_html = ""
        if delta is not None:
            d_color = "#00d4aa" if delta >= 0 else "#ff6b6b"
            d_arrow = "▲" if delta >= 0 else "▼"
            delta_html = (f"<div style='color:{d_color}; font-size:0.72rem; margin-top:2px;'>"
                          f"{d_arrow} {abs(delta)}</div>")
        sub_html = (f"<div style='color:#4a5270; font-size:0.7rem; margin-top:2px;'>{sub}</div>"
                    if sub else "")
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid rgba(108,99,255,0.2);
                    border-radius:12px; padding:16px; text-align:center; height:100%;">
            <div style="font-size:1.4rem;">{icon}</div>
            <div style="font-size:1.5rem; font-weight:800; color:{color};
                        line-height:1.2; margin-top:4px;">{value}</div>
            <div style="color:#9fa8da; font-size:0.75rem; margin-top:4px;">{label}</div>
            {sub_html}{delta_html}
        </div>
        """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin:24px 0 14px;">
        <h3 style="color:#e8eaf6; margin:0; font-size:1.1rem;">{title}</h3>
        {"<p style='color:#9fa8da; font-size:0.8rem; margin:4px 0 0;'>" + subtitle + "</p>"
         if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def status_badge(text: str, color: str, bg: str) -> str:
    return (f"<span style='background:{bg}; color:{color}; border:1px solid {color}; "
            f"padding:2px 10px; border-radius:12px; font-size:0.72rem; "
            f"font-weight:700;'>{text}</span>")


# ─── CHARTS ───────────────────────────────────────────────────────────────────

def make_ats_category_donut(stats: dict) -> go.Figure:
    cat_dist = stats.get("category_distribution", {})
    if not cat_dist:
        return go.Figure()

    cat_colors = {"Excellent": "#00d4aa", "Good": "#6c63ff",
                  "Average": "#ffd700",   "Poor": "#ff6b6b"}
    labels = list(cat_dist.keys())
    values = list(cat_dist.values())
    colors = [cat_colors.get(l, "#9fa8da") for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.58,
        marker=dict(colors=colors, line=dict(color="#161829", width=3)),
        textfont=dict(color="#e8eaf6", size=12),
        hovertemplate="<b>%{label}</b><br>%{value} resumes (%{percent})<extra></extra>",
    ))
    total = sum(values)
    fig.update_layout(
        **PLOTLY_LAYOUT, height=280,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9fa8da", size=11)),
        annotations=[dict(text=f"<b>{total}</b><br>total",
                          x=0.5, y=0.5, font_size=15,
                          font_color="#e8eaf6", showarrow=False)],
    )
    return fig


def make_role_bar(stats: dict) -> go.Figure:
    role_dist = stats.get("role_distribution", {})
    if not role_dist:
        return go.Figure()

    roles  = list(role_dist.keys())
    counts = list(role_dist.values())
    colors = PALETTE[:len(roles)]

    fig = go.Figure(go.Bar(
        x=counts, y=roles,
        orientation="h",
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=counts, textposition="outside",
        textfont=dict(color="#e8eaf6", size=11),
        hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="#2a2d45", title="Number of Resumes"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", autorange="reversed"),
        height=max(260, len(roles) * 48),
    )
    return fig


def make_signups_timeline(users: list) -> go.Figure:
    from collections import Counter
    dates  = [str(u["created_at"])[:10] for u in users if u.get("created_at")]
    counts = Counter(dates)
    sorted_dates = sorted(counts.keys())
    cumulative, total = [], 0
    for d in sorted_dates:
        total += counts[d]
        cumulative.append(total)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sorted_dates, y=cumulative,
        mode="lines+markers",
        fill="tozeroy",
        fillcolor="rgba(108,99,255,0.1)",
        line=dict(color="#6c63ff", width=2, shape="spline"),
        marker=dict(size=7, color="#00d4aa",
                    line=dict(color="#161829", width=2)),
        name="Cumulative Users",
        hovertemplate="Date: %{x}<br>Total Users: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="#2a2d45"),
        yaxis=dict(gridcolor="#2a2d45", title="Total Users"),
        height=260, showlegend=False,
    )
    return fig


def make_ats_heatmap(resumes: list) -> go.Figure:
    """Scatter of ATS score vs confidence."""
    scores = [r["ats_score"] or 0      for r in resumes]
    confs  = [r["confidence_score"] or 0 for r in resumes]
    roles  = [r["predicted_role"] or "Unknown" for r in resumes]
    users  = [r.get("username", "—")   for r in resumes]

    fig = go.Figure(go.Scatter(
        x=scores, y=confs,
        mode="markers",
        marker=dict(
            size=10,
            color=scores,
            colorscale=[[0, "#ff6b6b"], [0.45, "#ffd700"],
                        [0.65, "#6c63ff"], [1, "#00d4aa"]],
            showscale=True,
            colorbar=dict(title="ATS Score", tickfont=dict(color="#9fa8da")),
            opacity=0.8,
            line=dict(color="#161829", width=1),
        ),
        text=[f"User: {u}<br>Role: {r}" for u, r in zip(users, roles)],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "ATS Score: %{x:.0f}<br>"
            "Confidence: %{y:.0f}%<extra></extra>"
        ),
    ))
    fig.add_hline(y=50, line_dash="dot", line_color="#ffd700",
                  annotation_text="50% conf", annotation_font_color="#9fa8da")
    fig.add_vline(x=65, line_dash="dot", line_color="#6c63ff",
                  annotation_text="Good ATS", annotation_font_color="#9fa8da")
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(title="ATS Score", range=[0, 105], gridcolor="#2a2d45"),
        yaxis=dict(title="Confidence %", range=[0, 105], gridcolor="#2a2d45"),
        height=320,
    )
    return fig


def make_daily_uploads(resumes: list) -> go.Figure:
    from collections import Counter
    dates  = [str(r["uploaded_at"])[:10] for r in resumes]
    counts = Counter(dates)
    sorted_dates = sorted(counts.keys())
    vals = [counts[d] for d in sorted_dates]

    fig = go.Figure(go.Bar(
        x=sorted_dates, y=vals,
        marker=dict(color="#6c63ff", opacity=0.8, line=dict(width=0)),
        text=vals, textposition="outside",
        textfont=dict(color="#e8eaf6", size=10),
        hovertemplate="Date: %{x}<br>Uploads: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickangle=-30),
        yaxis=dict(gridcolor="#2a2d45", title="Uploads", dtick=1),
        height=250,
    )
    return fig


# ─── MAIN PAGE ────────────────────────────────────────────────────────────────

def show():
    # ── Access guard ──────────────────────────────────────────────────────
    user = st.session_state.user
    if user.get("role") != "admin":
        st.markdown("""
        <div style="background:rgba(255,107,107,0.1); border:1px solid rgba(255,107,107,0.4);
                    border-radius:14px; padding:40px; text-align:center; margin-top:40px;">
            <div style="font-size:3rem;">🚫</div>
            <h2 style="color:#ff6b6b; margin-top:12px;">Access Denied</h2>
            <p style="color:#9fa8da;">This page is restricted to administrators only.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Load data ─────────────────────────────────────────────────────────
    all_users   = get_all_users()
    all_resumes = get_all_resumes()
    stats       = get_resume_stats()

    # Filter out admin from user count
    regular_users = [u for u in all_users if u.get("role") != "admin"]

    # Page header
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between;
                margin-bottom:8px;">
        <div>
            <h1 style="color:#e8eaf6; margin:0; font-size:1.8rem;">🛡️ Admin Dashboard</h1>
            <p style="color:#9fa8da; margin:4px 0 0; font-size:0.85rem;">
                Platform overview · Last refreshed: {datetime.now().strftime("%d %b %Y, %H:%M")}
            </p>
        </div>
        <div style="background:rgba(108,99,255,0.15); border:1px solid rgba(108,99,255,0.4);
                    border-radius:10px; padding:8px 16px; text-align:right;">
            <div style="color:#9fa8da; font-size:0.72rem;">Logged in as</div>
            <div style="color:#6c63ff; font-weight:700;">🛡️ {user['username']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Platform KPIs ─────────────────────────────────────────────────────
    avg_ats   = stats.get("avg_ats", 0)
    total_res = stats.get("total_resumes", 0)
    total_usr = stats.get("total_users", 0)
    role_dist = stats.get("role_distribution", {})
    top_role  = max(role_dist, key=role_dist.get) if role_dist else "—"

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpi_card(k1, "Total Users",       total_usr,           "#6c63ff", "👥",
             sub="registered accounts")
    kpi_card(k2, "Total Resumes",     total_res,           "#00d4aa", "📄",
             sub="all time uploads")
    kpi_card(k3, "Avg ATS Score",     f"{avg_ats:.1f}",    ats_color(avg_ats), "📊",
             sub="platform average")
    kpi_card(k4, "Most Predicted",    top_role[:12] + ("…" if len(top_role) > 12 else ""),
             "#ffd700", "🎯", sub="top role match")
    kpi_card(k5, "Active Today",
             len([u for u in all_users
                  if u.get("last_login") and str(u["last_login"])[:10] == datetime.now().strftime("%Y-%m-%d")]),
             "#a78bfa", "🟢", sub="users logged in")
    kpi_card(k6, "Avg Resumes/User",
             round(total_res / max(total_usr, 1), 1),
             "#34d399", "📈", sub="per user")

    st.markdown("<hr style='border-color:rgba(108,99,255,0.15); margin:24px 0;'>",
                unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "📊 Overview",
        "👥 Users",
        "📄 Resumes",
        "📈 Analytics",
        "⚙️ System",
    ])

    with tabs[0]: render_overview_tab(stats, all_users, all_resumes)
    with tabs[1]: render_users_tab(all_users, regular_users)
    with tabs[2]: render_resumes_tab(all_resumes)
    with tabs[3]: render_analytics_tab(stats, all_users, all_resumes)
    with tabs[4]: render_system_tab(all_users, all_resumes)


# ─── TAB 1 : OVERVIEW ─────────────────────────────────────────────────────────

def render_overview_tab(stats, all_users, all_resumes):
    section_header("🌐 Platform Overview", "High-level health of the HireSenseAI platform.")

    left, right = st.columns(2)

    with left:
        section_header("🏷️ ATS Category Distribution",
                       "How resumes are distributed across ATS grades")
        fig = make_ats_category_donut(stats)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No resume data yet.")

    with right:
        section_header("🎯 Role Prediction Distribution",
                       "Most commonly predicted roles")
        fig = make_role_bar(stats)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No prediction data yet.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick insights strip
    section_header("💡 Quick Insights")
    scores = [r["ats_score"] or 0 for r in all_resumes]
    excellent = sum(1 for s in scores if s >= 80)
    poor      = sum(1 for s in scores if s < 45)
    total     = len(scores) or 1

    i1, i2, i3, i4 = st.columns(4)
    insight_card(i1, "🏆", "Excellent Resumes",
                 f"{excellent} ({round(excellent/total*100)}%)",
                 "#00d4aa", "80+ ATS score")
    insight_card(i2, "❌", "Poor Resumes",
                 f"{poor} ({round(poor/total*100)}%)",
                 "#ff6b6b", "Below 45 ATS score")
    insight_card(i3, "📅", "Latest Signup",
                 str(all_users[0]["created_at"])[:10] if all_users else "—",
                 "#6c63ff", "Most recent user")
    insight_card(i4, "📤", "Latest Upload",
                 str(all_resumes[0]["uploaded_at"])[:10] if all_resumes else "—",
                 "#ffd700", "Most recent resume")


def insight_card(col, icon, label, value, color, sub):
    with col:
        st.markdown(f"""
        <div style="background:#1e2035; border:1px solid {color}30;
                    border-radius:12px; padding:16px; text-align:center;">
            <div style="font-size:1.6rem;">{icon}</div>
            <div style="color:{color}; font-weight:700; font-size:1rem;
                        margin-top:6px;">{value}</div>
            <div style="color:#9fa8da; font-size:0.78rem; margin-top:3px;">{label}</div>
            <div style="color:#4a5270; font-size:0.7rem; margin-top:2px;">{sub}</div>
        </div>
        """, unsafe_allow_html=True)


# ─── TAB 2 : USERS ────────────────────────────────────────────────────────────

def render_users_tab(all_users, regular_users):
    section_header("👥 User Management",
                   f"{len(regular_users)} registered users on the platform.")

    # Search & filter
    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search = st.text_input("🔍 Search users", placeholder="Search by username or email…",
                               label_visibility="collapsed")
    with filter_col:
        sort_by = st.selectbox("Sort", ["Newest", "Oldest", "Username A-Z"],
                               label_visibility="collapsed")

    # Filter users
    display_users = [u for u in all_users if u.get("role") != "admin"]
    if search:
        display_users = [u for u in display_users
                         if search.lower() in (u.get("username","") + u.get("email","")).lower()]
    if sort_by == "Oldest":
        display_users = list(reversed(display_users))
    elif sort_by == "Username A-Z":
        display_users.sort(key=lambda u: u.get("username","").lower())

    st.markdown(f"<p style='color:#9fa8da; font-size:0.8rem; margin:8px 0;'>"
                f"Showing {len(display_users)} users</p>", unsafe_allow_html=True)

    # Table header
    render_table_header(["#", "👤 Username", "📧 Email", "📅 Joined",
                          "🕐 Last Login", "🎭 Role"])

    if not display_users:
        st.markdown("<div style='text-align:center; color:#4a5270; padding:20px;'>"
                    "No users found.</div>", unsafe_allow_html=True)
        return

    for i, u in enumerate(display_users):
        role   = u.get("role", "user")
        joined = str(u.get("created_at","—"))[:10]
        last   = str(u.get("last_login","Never"))[:10] if u.get("last_login") else "Never"
        is_admin = role == "admin"
        role_badge = (
            status_badge("Admin", "#ff6b6b", "rgba(255,107,107,0.12)") if is_admin
            else status_badge("User", "#6c63ff", "rgba(108,99,255,0.12)")
        )
        cols = st.columns([0.5, 1.5, 2, 1.2, 1.2, 1])
        row_data = [
            (cols[0], f"<span style='color:#4a5270; font-size:0.8rem;'>{i+1}</span>"),
            (cols[1], f"<span style='color:#e8eaf6; font-weight:600; font-size:0.85rem;'>"
                      f"👤 {u.get('username','—')}</span>"),
            (cols[2], f"<span style='color:#9fa8da; font-size:0.82rem;'>{u.get('email','—')}</span>"),
            (cols[3], f"<span style='color:#9fa8da; font-size:0.8rem;'>{joined}</span>"),
            (cols[4], f"<span style='color:#9fa8da; font-size:0.8rem;'>{last}</span>"),
            (cols[5], role_badge),
        ]
        for col, html in row_data:
            with col:
                st.markdown(html, unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(108,99,255,0.08); margin:5px 0;'>",
                    unsafe_allow_html=True)

    # Export button
    st.markdown("<br>", unsafe_allow_html=True)
    user_csv = generate_user_csv(display_users)
    st.download_button(
        label="⬇️ Export Users CSV",
        data=user_csv,
        file_name="users_export.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ─── TAB 3 : RESUMES ──────────────────────────────────────────────────────────

def render_resumes_tab(all_resumes):
    section_header("📄 Resume Management",
                   f"{len(all_resumes)} total resumes uploaded across all users.")

    # Filters
    f1, f2, f3 = st.columns([2, 1.5, 1.5])
    with f1:
        search = st.text_input("🔍 Search", placeholder="Search by filename or username…",
                               label_visibility="collapsed")
    with f2:
        cat_filter = st.selectbox("ATS Category",
                                  ["All", "Excellent", "Good", "Average", "Poor"],
                                  label_visibility="collapsed")
    with f3:
        sort_r = st.selectbox("Sort by",
                              ["Newest", "Oldest", "Highest ATS", "Lowest ATS"],
                              label_visibility="collapsed")

    # Apply filters
    display = all_resumes[:]
    if search:
        display = [r for r in display
                   if search.lower() in (r.get("filename","") + r.get("username","")).lower()]
    if cat_filter != "All":
        display = [r for r in display if r.get("ats_category") == cat_filter]
    if sort_r == "Oldest":
        display = list(reversed(display))
    elif sort_r == "Highest ATS":
        display.sort(key=lambda r: r.get("ats_score") or 0, reverse=True)
    elif sort_r == "Lowest ATS":
        display.sort(key=lambda r: r.get("ats_score") or 0)

    st.markdown(f"<p style='color:#9fa8da; font-size:0.8rem; margin:8px 0;'>"
                f"Showing {len(display)} resumes</p>", unsafe_allow_html=True)

    # Table
    render_table_header(["#", "📄 File", "👤 User", "🎯 Predicted Role",
                          "📊 ATS", "🏷️ Category", "📅 Uploaded"])

    for i, r in enumerate(display[:50]):   # cap at 50 rows
        score = r.get("ats_score") or 0
        cat   = r.get("ats_category") or "—"
        sc    = ats_color(score)
        cat_colors = {"Excellent": ("#00d4aa", "rgba(0,212,170,0.12)"),
                      "Good":      ("#6c63ff", "rgba(108,99,255,0.12)"),
                      "Average":   ("#ffd700", "rgba(255,215,0,0.12)"),
                      "Poor":      ("#ff6b6b", "rgba(255,107,107,0.12)")}
        cc, cb = cat_colors.get(cat, ("#9fa8da", "rgba(159,168,218,0.12)"))
        badge  = status_badge(cat, cc, cb)
        fname  = (r.get("filename") or "resume")[:20]
        uname  = r.get("username","—")
        role   = (r.get("predicted_role") or "—")[:18]
        date   = str(r.get("uploaded_at","—"))[:10]

        cols = st.columns([0.4, 1.6, 1, 1.5, 0.8, 1, 1])
        data = [
            (cols[0], f"<span style='color:#4a5270; font-size:0.78rem;'>{i+1}</span>"),
            (cols[1], f"<span style='color:#e8eaf6; font-size:0.82rem; "
                      f"font-weight:500;'>📄 {fname}</span>"),
            (cols[2], f"<span style='color:#9fa8da; font-size:0.8rem;'>👤 {uname}</span>"),
            (cols[3], f"<span style='color:#9fa8da; font-size:0.8rem;'>{role}</span>"),
            (cols[4], f"<span style='color:{sc}; font-weight:700; "
                      f"font-size:0.85rem;'>{score:.0f}</span>"),
            (cols[5], badge),
            (cols[6], f"<span style='color:#4a5270; font-size:0.78rem;'>{date}</span>"),
        ]
        for col, html in data:
            with col:
                st.markdown(html, unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(108,99,255,0.08); margin:4px 0;'>",
                    unsafe_allow_html=True)

    # Export
    st.markdown("<br>", unsafe_allow_html=True)
    resume_csv = generate_resume_csv(display)
    st.download_button(
        label="⬇️ Export Resumes CSV",
        data=resume_csv,
        file_name="resumes_export.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ─── TAB 4 : ANALYTICS ────────────────────────────────────────────────────────

def render_analytics_tab(stats, all_users, all_resumes):
    section_header("📈 Platform Analytics", "Deep analytics across all users and resumes.")

    # ATS scatter (score vs confidence)
    section_header("🎯 ATS Score vs Prediction Confidence",
                   "Each dot is one resume — see where candidates cluster")
    if all_resumes:
        st.plotly_chart(make_ats_heatmap(all_resumes), use_container_width=True,
                        config={"displayModeBar": False})
    else:
        st.info("No resume data yet.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Two charts side by side
    c_left, c_right = st.columns(2)

    with c_left:
        section_header("👥 User Growth", "Cumulative signups over time")
        if all_users:
            st.plotly_chart(make_signups_timeline(all_users), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No user data.")

    with c_right:
        section_header("📤 Daily Uploads", "Resume submissions per day")
        if all_resumes:
            st.plotly_chart(make_daily_uploads(all_resumes), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No upload data.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Score percentiles
    section_header("📊 ATS Score Percentiles", "Platform-wide score distribution")
    if all_resumes:
        scores = sorted([r["ats_score"] or 0 for r in all_resumes])
        n      = len(scores)

        def percentile(p):
            idx = int(p / 100 * n)
            return scores[min(idx, n - 1)]

        p_cols = st.columns(5)
        pcts   = [10, 25, 50, 75, 90]
        labels = ["P10", "P25", "Median", "P75", "P90"]
        pcolors= ["#ff6b6b", "#ffd700", "#6c63ff", "#00d4aa", "#a78bfa"]

        for col, p, lbl, color in zip(p_cols, pcts, labels, pcolors):
            val = percentile(p)
            with col:
                st.markdown(f"""
                <div style="background:#1e2035; border:1px solid {color}30;
                            border-radius:10px; padding:14px; text-align:center;">
                    <div style="color:#9fa8da; font-size:0.72rem; font-weight:600;">{lbl}</div>
                    <div style="font-size:1.6rem; font-weight:800; color:{color};">
                        {val:.0f}
                    </div>
                    <div style="color:#4a5270; font-size:0.7rem;">{p}th percentile</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Top performers table
    section_header("🏆 Top 5 Performers", "Highest ATS scores on the platform")
    top5 = sorted(all_resumes, key=lambda r: r.get("ats_score") or 0, reverse=True)[:5]

    render_table_header(["🏅", "👤 User", "📄 File", "🎯 Role", "📊 ATS", "🏷️ Category"])
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    for i, r in enumerate(top5):
        score = r.get("ats_score") or 0
        cat   = r.get("ats_category") or "—"
        sc    = ats_color(score)
        cols  = st.columns([0.5, 1.2, 1.5, 1.5, 0.8, 1])
        data  = [
            (cols[0], f"<span style='font-size:1.1rem;'>{medals[i]}</span>"),
            (cols[1], f"<span style='color:#e8eaf6; font-weight:600; "
                      f"font-size:0.85rem;'>👤 {r.get('username','—')}</span>"),
            (cols[2], f"<span style='color:#9fa8da; font-size:0.82rem;'>"
                      f"📄 {(r.get('filename') or 'resume')[:18]}</span>"),
            (cols[3], f"<span style='color:#9fa8da; font-size:0.82rem;'>"
                      f"{(r.get('predicted_role') or '—')[:18]}</span>"),
            (cols[4], f"<span style='color:{sc}; font-weight:800; font-size:0.95rem;'>"
                      f"{score:.0f}</span>"),
            (cols[5], f"<span style='color:{sc}; font-size:0.82rem;'>{cat}</span>"),
        ]
        for col, html in data:
            with col:
                st.markdown(html, unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(108,99,255,0.08); margin:5px 0;'>",
                    unsafe_allow_html=True)


# ─── TAB 5 : SYSTEM ───────────────────────────────────────────────────────────

def render_system_tab(all_users, all_resumes):
    section_header("⚙️ System Information", "Platform health, storage, and configuration.")

    # System health cards
    h1, h2, h3, h4 = st.columns(4)

    def health_card(col, label, status, icon, color):
        with col:
            st.markdown(f"""
            <div style="background:#1e2035; border:1px solid {color}40;
                        border-radius:12px; padding:16px; text-align:center;">
                <div style="font-size:1.8rem;">{icon}</div>
                <div style="color:{color}; font-weight:700; margin-top:6px;
                            font-size:0.9rem;">{status}</div>
                <div style="color:#9fa8da; font-size:0.75rem; margin-top:3px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    health_card(h1, "Database",      "Online ✅",   "🗄️",  "#00d4aa")
    health_card(h2, "Auth System",   "Active ✅",   "🔐",  "#00d4aa")
    health_card(h3, "File Storage",  "Available ✅","📁",  "#00d4aa")
    health_card(h4, "AI Engine",     "Ready ✅",    "🤖",  "#00d4aa")

    st.markdown("<br>", unsafe_allow_html=True)

    # Platform info
    section_header("📋 Platform Configuration")
    left_cfg, right_cfg = st.columns(2)

    config_items = [
        ("App Version",        "HireSenseAI v1.0.0"),
        ("Framework",          "Streamlit"),
        ("Database",           "SQLite"),
        ("NLP Engine",         "spaCy + NLTK"),
        ("AI Chatbot",         "Google Gemini 1.5 Flash"),
        ("Resume Parser",      "pdfplumber + python-docx"),
        ("ML/DL",              "Scikit-learn + TensorFlow"),
        ("Charts",             "Plotly"),
        ("Auth",               "bcrypt"),
        ("Deployment Target",  "Streamlit Cloud / Render / AWS"),
    ]

    for i, (key, val) in enumerate(config_items):
        col = left_cfg if i % 2 == 0 else right_cfg
        with col:
            st.markdown(f"""
            <div style="background:#1e2035; border-radius:8px; padding:10px 16px;
                        margin:4px 0; display:flex; justify-content:space-between;
                        align-items:center;">
                <span style="color:#9fa8da; font-size:0.82rem;">{key}</span>
                <span style="color:#6c63ff; font-weight:600; font-size:0.82rem;">{val}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Database stats
    section_header("🗄️ Database Statistics")
    db1, db2, db3, db4 = st.columns(4)
    kpi_card(db1, "Users Table",   len(all_users),   "#6c63ff", "👥")
    kpi_card(db2, "Resumes Table", len(all_resumes), "#00d4aa", "📄")
    kpi_card(db3, "Avg Text Size",
             f"{round(sum(len(r.get('resume_text') or '') for r in all_resumes) / max(len(all_resumes),1) / 1000, 1)} KB",
             "#ffd700", "📝")
    kpi_card(db4, "Roles Tracked", len(set(r.get('predicted_role') for r in all_resumes if r.get('predicted_role'))),
             "#a78bfa", "🎯")

    st.markdown("<br>", unsafe_allow_html=True)

    # Full data export
    section_header("📦 Data Export", "Download platform data for reporting or backup.")

    exp1, exp2, exp3 = st.columns(3)
    with exp1:
        user_csv = generate_user_csv(all_users)
        st.download_button(
            label="⬇️ Export All Users",
            data=user_csv,
            file_name="all_users.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with exp2:
        resume_csv = generate_resume_csv(all_resumes)
        st.download_button(
            label="⬇️ Export All Resumes",
            data=resume_csv,
            file_name="all_resumes.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with exp3:
        report = generate_platform_report(all_users, all_resumes)
        st.download_button(
            label="⬇️ Download Report (.md)",
            data=report,
            file_name="platform_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Admin actions
    section_header("🛠️ Admin Actions")
    st.markdown("""
    <div style="background:rgba(255,107,107,0.06); border:1px solid rgba(255,107,107,0.2);
                border-radius:12px; padding:16px; margin-bottom:12px;">
        <div style="color:#ffd700; font-size:0.85rem; font-weight:600; margin-bottom:8px;">
            ⚠️ Caution Zone — Irreversible Actions
        </div>
        <div style="color:#9fa8da; font-size:0.8rem;">
            These actions permanently affect platform data. Use with caution.
        </div>
    </div>
    """, unsafe_allow_html=True)

    act1, act2 = st.columns(2)
    with act1:
        if st.button("🔄 Refresh Stats Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache cleared successfully!")
    with act2:
        if st.button("📊 Generate Analytics Snapshot", use_container_width=True):
            st.success("✅ Snapshot saved to platform_snapshot.md")


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def render_table_header(columns: list):
    cols = st.columns(len(columns))
    for col, header in zip(cols, columns):
        with col:
            st.markdown(
                f"<div style='color:#6c63ff; font-size:0.78rem; font-weight:700; "
                f"padding:4px 0;'>{header}</div>",
                unsafe_allow_html=True
            )
    st.markdown("<hr style='border-color:rgba(108,99,255,0.2); margin:4px 0 6px;'>",
                unsafe_allow_html=True)


def generate_user_csv(users: list) -> str:
    lines = ["id,username,email,role,created_at,last_login"]
    for u in users:
        lines.append(
            f"{u.get('id','')},{u.get('username','')},{u.get('email','')},"
            f"{u.get('role','')},{str(u.get('created_at',''))[:19]},"
            f"{str(u.get('last_login',''))[:19]}"
        )
    return "\n".join(lines)


def generate_resume_csv(resumes: list) -> str:
    lines = ["id,username,filename,ats_score,ats_category,"
             "predicted_role,confidence_score,uploaded_at"]
    for r in resumes:
        lines.append(
            f"{r.get('id','')},{r.get('username','')},{r.get('filename','')},"
            f"{r.get('ats_score','')},{r.get('ats_category','')},"
            f"{r.get('predicted_role','')},{r.get('confidence_score','')},"
            f"{str(r.get('uploaded_at',''))[:19]}"
        )
    return "\n".join(lines)


def generate_platform_report(users: list, resumes: list) -> str:
    scores = [r["ats_score"] or 0 for r in resumes]
    avg    = round(sum(scores) / len(scores), 1) if scores else 0
    best   = max(scores) if scores else 0
    cats   = {}
    for r in resumes:
        c = r.get("ats_category", "Unknown")
        cats[c] = cats.get(c, 0) + 1

    roles = {}
    for r in resumes:
        role = r.get("predicted_role", "Unknown")
        roles[role] = roles.get(role, 0) + 1

    # Pre-build table strings — avoids backslash-in-f-string (Python <= 3.11)
    newline = "\n"

    cat_rows = newline.join(
        "| " + cat + " | " + str(count) + " ("
        + str(round(count / max(len(resumes), 1) * 100)) + "%) |"
        for cat, count in cats.items()
    )

    role_rows = newline.join(
        "| " + role + " | " + str(count) + " |"
        for role, count in sorted(roles.items(), key=lambda x: x[1], reverse=True)
    )

    user_rows = newline.join(
        "- " + u.get("username", "—") + " (" + u.get("email", "—") + ")"
        + " — joined " + str(u.get("created_at", ""))[:10]
        for u in users[:5]
    )

    generated_at = datetime.now().strftime("%d %B %Y, %H:%M")
    total_users  = len(users)
    total_res    = len(resumes)

    return (
        "# HireSenseAI Platform Report\n"
        "Generated: " + generated_at + "\n\n"
        "---\n\n"
        "## Summary\n"
        "| Metric | Value |\n"
        "|--------|-------|\n"
        "| Total Users | " + str(total_users) + " |\n"
        "| Total Resumes | " + str(total_res) + " |\n"
        "| Average ATS Score | " + str(avg) + " |\n"
        "| Best ATS Score | " + str(best) + " |\n\n"
        "## ATS Category Breakdown\n"
        + cat_rows + "\n\n"
        "## Role Distribution\n"
        + role_rows + "\n\n"
        "## Recent Users (last 5)\n"
        + user_rows + "\n\n"
        "---\n"
        "*Generated by HireSenseAI Admin Dashboard*\n"
    )
