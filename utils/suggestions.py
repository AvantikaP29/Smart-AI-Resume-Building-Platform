"""
Resume Suggestion Engine
Provides AI-based resume improvement suggestions.
"""

from typing import Dict, List


def generate_suggestions(parsed: Dict, ats_report: Dict, predicted_role: str) -> List[Dict]:
    """
    Generate categorized resume improvement suggestions.
    Returns list of suggestion dicts with category, priority, and message.
    """
    suggestions = []

    # ── Contact & Profile ──────────────────────────────────────────────────
    if not parsed.get("linkedin"):
        suggestions.append({
            "category": "Profile",
            "priority": "High",
            "icon": "🔗",
            "title": "Add LinkedIn Profile",
            "detail": "Recruiters verify LinkedIn. Add: linkedin.com/in/yourname"
        })
    if not parsed.get("github"):
        suggestions.append({
            "category": "Profile",
            "priority": "High",
            "icon": "💻",
            "title": "Add GitHub Profile",
            "detail": "GitHub shows real work. Add: github.com/yourusername"
        })
    if not parsed.get("email"):
        suggestions.append({
            "category": "Contact",
            "priority": "Critical",
            "icon": "📧",
            "title": "Add Email Address",
            "detail": "Email is mandatory. Ensure it's visible at the top."
        })

    # ── Skills ────────────────────────────────────────────────────────────
    skill_count = len(parsed.get("skills", []))
    if skill_count < 6:
        suggestions.append({
            "category": "Skills",
            "priority": "High",
            "icon": "🛠️",
            "title": "Add More Technical Skills",
            "detail": f"Only {skill_count} skills detected. Target roles require 10-15+ skills."
        })

    # ── Certifications ───────────────────────────────────────────────────
    if not parsed.get("certifications"):
        suggestions.append({
            "category": "Certifications",
            "priority": "Medium",
            "icon": "🏆",
            "title": "Add Certifications",
            "detail": f"Boost credibility with certs relevant to {predicted_role}."
        })

    # ── Resume Length & Content ───────────────────────────────────────────
    wc = parsed.get("word_count", 0)
    if wc < 300:
        suggestions.append({
            "category": "Content",
            "priority": "High",
            "icon": "📝",
            "title": "Expand Resume Content",
            "detail": f"Only {wc} words found. Add experience details, projects, achievements."
        })
    elif wc > 900:
        suggestions.append({
            "category": "Formatting",
            "priority": "Medium",
            "icon": "✂️",
            "title": "Trim Resume to 1-2 Pages",
            "detail": "ATS prefers concise resumes. Focus on last 5 years of experience."
        })

    # ── Experience ────────────────────────────────────────────────────────
    if parsed.get("experience_years") is None:
        suggestions.append({
            "category": "Experience",
            "priority": "High",
            "icon": "⏱️",
            "title": "Mention Years of Experience",
            "detail": "E.g., '3+ years of experience in Python development'"
        })

    # ── ATS Optimization ──────────────────────────────────────────────────
    missing_kw = ats_report.get("missing_keywords", [])
    if missing_kw:
        suggestions.append({
            "category": "ATS Keywords",
            "priority": "High",
            "icon": "🔑",
            "title": "Add Missing ATS Keywords",
            "detail": f"Add these keywords: {', '.join(missing_kw[:5])}"
        })

    # ── Achievements ──────────────────────────────────────────────────────
    raw_text = parsed.get("raw_text", "").lower()
    achievement_words = ["%", "improved", "increased", "reduced", "saved", "delivered", "achieved"]
    has_achievements = any(w in raw_text for w in achievement_words)
    if not has_achievements:
        suggestions.append({
            "category": "Content",
            "priority": "Medium",
            "icon": "📊",
            "title": "Add Measurable Achievements",
            "detail": "Use numbers: 'Improved API performance by 40%', 'Led team of 5 engineers'"
        })

    # ── Summary Section ───────────────────────────────────────────────────
    summary_words = ["summary", "objective", "profile", "about"]
    has_summary = any(w in raw_text for w in summary_words)
    if not has_summary:
        suggestions.append({
            "category": "Structure",
            "priority": "Medium",
            "icon": "📋",
            "title": "Add Professional Summary",
            "detail": "A 3-4 line summary at the top catches recruiter attention immediately."
        })

    # ── Action Verbs ──────────────────────────────────────────────────────
    action_verbs = ["developed", "implemented", "designed", "built", "led", "optimized", "created"]
    has_verbs = any(v in raw_text for v in action_verbs)
    if not has_verbs:
        suggestions.append({
            "category": "Content",
            "priority": "Low",
            "icon": "✍️",
            "title": "Use Strong Action Verbs",
            "detail": "Start bullet points with: Developed, Implemented, Designed, Optimized, Led"
        })

    # Sort by priority
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    suggestions.sort(key=lambda x: priority_order.get(x["priority"], 4))

    return suggestions
