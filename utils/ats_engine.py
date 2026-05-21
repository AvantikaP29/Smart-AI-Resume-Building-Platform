"""
ATS Score Engine
Calculates ATS (Applicant Tracking System) score for resumes.
Scores based on: skills, experience, education, certifications, formatting, keywords.
"""

from typing import Dict, List, Tuple


# ─── SCORING WEIGHTS ──────────────────────────────────────────────────────────

WEIGHTS = {
    "skills": 35,
    "experience": 20,
    "education": 15,
    "contact_info": 10,
    "certifications": 10,
    "formatting": 10,
}

# Minimum skill counts expected per seniority
EXPERIENCE_SCORE_MAP = {
    0: 30,
    1: 50,
    2: 65,
    3: 75,
    5: 90,
    8: 100,
}

EDUCATION_SCORE_MAP = {
    "PHD": 100, "PH.D": 100,
    "MTECH": 90, "M.TECH": 90, "MASTER": 90, "MBA": 85, "M.SC": 80, "MSC": 80,
    "BTECH": 70, "B.TECH": 70, "B.E": 70, "BACHELOR": 70, "B.SC": 65, "BSC": 65,
    "DIPLOMA": 50, "12TH": 30, "HSC": 30,
}


def score_skills(skills: List[str], total_expected: int = 10) -> Tuple[float, str]:
    """Score based on number and diversity of skills."""
    count = len(skills)
    raw = min(count / total_expected, 1.0) * 100
    if raw >= 80:
        note = "Excellent skill diversity"
    elif raw >= 60:
        note = "Good skill set"
    elif raw >= 40:
        note = "Average skills - add more technical skills"
    else:
        note = "Low skill count - add relevant skills"
    return raw, note


def score_experience(exp_years: float) -> Tuple[float, str]:
    """Score based on years of experience."""
    if exp_years is None:
        return 20.0, "Experience not clearly stated - mention years explicitly"

    score = 20.0
    for years, s in sorted(EXPERIENCE_SCORE_MAP.items()):
        if exp_years >= years:
            score = s

    if exp_years >= 5:
        note = "Strong experience"
    elif exp_years >= 2:
        note = "Good experience level"
    elif exp_years >= 1:
        note = "Some experience - add more details"
    else:
        note = "Entry level - highlight projects and internships"
    return score, note


def score_education(education: List[str]) -> Tuple[float, str]:
    """Score based on highest education level found."""
    best_score = 0
    best_deg = ""
    for deg in education:
        s = EDUCATION_SCORE_MAP.get(deg.upper(), 0)
        if s > best_score:
            best_score = s
            best_deg = deg

    if best_score == 0:
        return 40.0, "Education not clearly mentioned"
    note = f"Education: {best_deg.title()}"
    return float(best_score), note


def score_contact_info(parsed: Dict) -> Tuple[float, str]:
    """Score based on completeness of contact information."""
    score = 0
    missing = []

    if parsed.get("email"):
        score += 30
    else:
        missing.append("email")

    if parsed.get("phone"):
        score += 25
    else:
        missing.append("phone")

    if parsed.get("linkedin"):
        score += 25
    else:
        missing.append("LinkedIn")

    if parsed.get("github"):
        score += 20
    else:
        missing.append("GitHub")

    if missing:
        note = f"Missing: {', '.join(missing)}"
    else:
        note = "Complete contact information"

    return float(score), note


def score_certifications(certs: List[str]) -> Tuple[float, str]:
    """Score based on certifications."""
    count = len(certs)
    if count == 0:
        return 10.0, "No certifications found - add relevant certs"
    elif count == 1:
        return 50.0, "1 certification found"
    elif count >= 2:
        return 80.0 + min(count * 5, 20), f"{count} certifications found"
    return 10.0, ""


def score_formatting(parsed: Dict) -> Tuple[float, str]:
    """Score based on resume length and formatting quality."""
    word_count = parsed.get("word_count", 0)
    score = 50.0
    notes = []

    if 300 <= word_count <= 800:
        score = 90.0
        notes.append("Good resume length")
    elif 200 <= word_count < 300:
        score = 70.0
        notes.append("Resume slightly short - expand experience/projects")
    elif word_count > 800:
        score = 70.0
        notes.append("Resume too long - aim for 1-2 pages")
    else:
        score = 40.0
        notes.append("Resume too short - add more details")

    if parsed.get("name"):
        score = min(score + 5, 100)
    else:
        notes.append("Name not detected at top of resume")

    return score, "; ".join(notes) if notes else "Standard formatting"


def get_ats_category(score: float) -> str:
    """Convert numeric score to ATS category."""
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Good"
    elif score >= 45:
        return "Average"
    else:
        return "Poor"


def calculate_ats_score(parsed: Dict) -> Dict:
    """
    Main ATS scoring function.
    Takes parsed resume dict, returns full ATS report.
    """
    # Individual scores
    skills_score, skills_note = score_skills(parsed.get("skills", []))
    exp_score, exp_note = score_experience(parsed.get("experience_years"))
    edu_score, edu_note = score_education(parsed.get("education", []))
    contact_score, contact_note = score_contact_info(parsed)
    cert_score, cert_note = score_certifications(parsed.get("certifications", []))
    fmt_score, fmt_note = score_formatting(parsed)

    # Weighted total
    total = (
        (skills_score * WEIGHTS["skills"] / 100) +
        (exp_score * WEIGHTS["experience"] / 100) +
        (edu_score * WEIGHTS["education"] / 100) +
        (contact_score * WEIGHTS["contact_info"] / 100) +
        (cert_score * WEIGHTS["certifications"] / 100) +
        (fmt_score * WEIGHTS["formatting"] / 100)
    )
    total = round(min(total, 100), 1)

    return {
        "total_score": total,
        "category": get_ats_category(total),
        "breakdown": {
            "Skills": {"score": round(skills_score, 1), "weight": WEIGHTS["skills"], "note": skills_note},
            "Experience": {"score": round(exp_score, 1), "weight": WEIGHTS["experience"], "note": exp_note},
            "Education": {"score": round(edu_score, 1), "weight": WEIGHTS["education"], "note": edu_note},
            "Contact Info": {"score": round(contact_score, 1), "weight": WEIGHTS["contact_info"], "note": contact_note},
            "Certifications": {"score": round(cert_score, 1), "weight": WEIGHTS["certifications"], "note": cert_note},
            "Formatting": {"score": round(fmt_score, 1), "weight": WEIGHTS["formatting"], "note": fmt_note},
        },
        "suggestions": generate_ats_suggestions(parsed, total),
        "missing_keywords": get_missing_keywords(parsed),
    }


def generate_ats_suggestions(parsed: Dict, score: float) -> List[str]:
    """Generate actionable ATS improvement suggestions."""
    suggestions = []

    if not parsed.get("linkedin"):
        suggestions.append("🔗 Add your LinkedIn profile URL to the resume")
    if not parsed.get("github"):
        suggestions.append("💻 Add your GitHub profile URL to showcase projects")
    if not parsed.get("email"):
        suggestions.append("📧 Ensure your email address is clearly visible")
    if not parsed.get("phone"):
        suggestions.append("📞 Add your phone number for recruiter contact")
    if len(parsed.get("skills", [])) < 8:
        suggestions.append("🛠️ Add more technical skills relevant to your target role")
    if not parsed.get("certifications"):
        suggestions.append("🏆 Add industry certifications (AWS, Google Cloud, etc.)")
    if parsed.get("word_count", 0) < 300:
        suggestions.append("📝 Expand your resume - aim for 400-700 words minimum")
    if parsed.get("experience_years") is None:
        suggestions.append("⏱️ Clearly mention years of experience in your summary")
    if score < 65:
        suggestions.append("🎯 Add measurable achievements (e.g., 'Improved performance by 40%')")
        suggestions.append("📊 Use action verbs: Developed, Implemented, Led, Optimized")
    if not parsed.get("education"):
        suggestions.append("🎓 Add your educational qualifications clearly")

    if not suggestions:
        suggestions.append("✅ Your resume is well-optimized! Minor tweaks can push it higher.")

    return suggestions


def get_missing_keywords(parsed: Dict) -> List[str]:
    """Identify missing high-value keywords based on skills found."""
    found = set(s.lower() for s in parsed.get("skills", []))
    important_keywords = [
        "git", "docker", "aws", "sql", "python", "javascript",
        "api", "agile", "scrum", "linux", "github", "rest"
    ]
    missing = [k for k in important_keywords if k not in found]
    return missing[:8]
