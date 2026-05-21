"""
Skill Gap Analysis Module
Compares candidate skills with required skills for predicted job roles.
"""

from typing import Dict, List
from utils.prediction_engine import JOB_ROLES, get_role_requirements


def analyze_skill_gap(candidate_skills: List[str], role: str) -> Dict:
    """
    Compare candidate skills against role requirements.
    Returns gap analysis with match percentage and recommendations.
    """
    candidate_set = set(s.lower() for s in candidate_skills)
    role_requirements = get_role_requirements(role)

    # Gather all required skills
    core_skills = [s.lower() for s in role_requirements.get("core_skills", [])]
    advanced_skills = [s.lower() for s in role_requirements.get("advanced_skills", [])]
    tools = [s.lower() for s in role_requirements.get("tools", [])]

    all_required = list(set(core_skills + advanced_skills + tools))

    # Compare
    existing = [s for s in all_required if s in candidate_set]
    missing = [s for s in all_required if s not in candidate_set]

    # Match percentage
    if all_required:
        match_pct = round(len(existing) / len(all_required) * 100, 1)
    else:
        match_pct = 0.0

    # Priority scoring: core > tools > advanced
    critical_missing = [s for s in core_skills if s not in candidate_set]
    tool_missing = [s for s in tools if s not in candidate_set]
    advanced_missing = [s for s in advanced_skills if s not in candidate_set]

    # Skill strength per category
    skill_categories = analyze_by_category(candidate_skills)

    return {
        "role": role,
        "existing_skills": existing,
        "missing_skills": missing,
        "critical_missing": critical_missing,
        "tool_missing": tool_missing,
        "advanced_missing": advanced_missing,
        "match_percentage": match_pct,
        "total_required": len(all_required),
        "total_matched": len(existing),
        "learning_resources": get_learning_resources(critical_missing + tool_missing),
        "skill_categories": skill_categories,
        "readiness_level": get_readiness_level(match_pct),
    }


def get_readiness_level(match_pct: float) -> Dict:
    """Classify candidate readiness for the role."""
    if match_pct >= 80:
        return {
            "level": "Job Ready",
            "color": "#00ff88",
            "message": "You meet most requirements. Apply now!",
            "emoji": "🟢"
        }
    elif match_pct >= 60:
        return {
            "level": "Almost Ready",
            "color": "#ffd700",
            "message": "A few more skills needed. 1-3 months away.",
            "emoji": "🟡"
        }
    elif match_pct >= 40:
        return {
            "level": "Learning Phase",
            "color": "#ff8c00",
            "message": "Invest 3-6 months to upskill. Keep learning!",
            "emoji": "🟠"
        }
    else:
        return {
            "level": "Beginner",
            "color": "#ff4444",
            "message": "6-12 months of focused learning needed.",
            "emoji": "🔴"
        }


def analyze_by_category(skills: List[str]) -> Dict:
    """Analyze skill strength by category."""
    from utils.resume_parser import SKILLS_DB

    skill_set = set(s.lower() for s in skills)
    result = {}

    for category, cat_skills in SKILLS_DB.items():
        matched = [s for s in cat_skills if s in skill_set]
        result[category] = {
            "matched": len(matched),
            "total": len(cat_skills),
            "skills": matched,
            "percentage": round(len(matched) / len(cat_skills) * 100, 1) if cat_skills else 0
        }

    return result


def get_learning_resources(missing_skills: List[str]) -> List[Dict]:
    """Get learning resources for missing skills."""
    resource_map = {
        "python": {"platform": "Coursera", "course": "Python for Everybody", "url": "https://coursera.org/specializations/python"},
        "machine learning": {"platform": "Coursera", "course": "ML by Andrew Ng", "url": "https://coursera.org/learn/machine-learning"},
        "docker": {"platform": "Docker Docs", "course": "Docker Getting Started", "url": "https://docs.docker.com/get-started"},
        "aws": {"platform": "AWS Training", "course": "AWS Cloud Practitioner", "url": "https://aws.amazon.com/training"},
        "sql": {"platform": "SQLZoo", "course": "SQL Tutorial", "url": "https://sqlzoo.net"},
        "react": {"platform": "React Docs", "course": "React Official Tutorial", "url": "https://react.dev/learn"},
        "kubernetes": {"platform": "KodeKloud", "course": "Kubernetes for Beginners", "url": "https://kodekloud.com"},
        "tensorflow": {"platform": "TensorFlow", "course": "TF Official Tutorials", "url": "https://tensorflow.org/tutorials"},
        "postgresql": {"platform": "PostgreSQL", "course": "Official Tutorial", "url": "https://postgresql.org/docs/tutorial"},
        "git": {"platform": "GitHub", "course": "Git & GitHub Crash Course", "url": "https://github.com/git-guides"},
        "linux": {"platform": "Linux Foundation", "course": "Introduction to Linux", "url": "https://training.linuxfoundation.org"},
        "power bi": {"platform": "Microsoft Learn", "course": "Power BI Learning Path", "url": "https://learn.microsoft.com/en-us/power-bi"},
    }

    resources = []
    for skill in missing_skills[:8]:  # Limit to 8
        skill_lower = skill.lower()
        for key, resource in resource_map.items():
            if key in skill_lower or skill_lower in key:
                resources.append({
                    "skill": skill,
                    "platform": resource["platform"],
                    "course": resource["course"],
                    "url": resource["url"]
                })
                break
        else:
            # Generic resource
            resources.append({
                "skill": skill,
                "platform": "YouTube / Udemy",
                "course": f"{skill.title()} Complete Course",
                "url": f"https://www.youtube.com/results?search_query={skill.replace(' ', '+')}+tutorial"
            })

    return resources
