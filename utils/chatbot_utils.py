"""
AI Chatbot Utility
Career guidance chatbot using Google Gemini API.
Falls back to rule-based responses if API key not available.
"""
import os
import re
from typing import List, Dict, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def build_system_prompt(resume_context: Optional[Dict] = None) -> str:
    """Build chatbot system prompt with optional resume context."""
    base = """You are HireSenseAI Assistant — an expert career counselor and resume coach.
You help candidates with:
- Resume improvement and ATS optimization
- Career roadmaps and learning paths
- Interview preparation and tips
- Skill gap analysis and recommendations
- Job search strategies
- Project ideas for portfolio building

Be concise, actionable, and encouraging. Format responses with bullet points where helpful.
"""
    if resume_context:
        role = resume_context.get("predicted_role", "unknown")
        skills = ", ".join(resume_context.get("skills", [])[:10])
        ats = resume_context.get("ats_score", "N/A")
        base += f"""
Current candidate context:
- Predicted Role: {role}
- ATS Score: {ats}/100
- Detected Skills: {skills}

Tailor all advice to this candidate's profile.
"""
    return base


def get_gemini_response(
    messages: List[Dict],
    api_key: str,
    resume_context: Optional[Dict] = None
) -> str:
    """Get response from Google Gemini API."""
    if not GEMINI_AVAILABLE:
        return get_fallback_response(messages[-1]["content"] if messages else "")

    try:
        # Initialize configuration
        genai.configure(api_key=api_key)
        
        # Overriding the API client version explicitly to bypass the v1beta 404 issue permanently
        from google.generativeai import client
        api_client = client.get_default_api_client()
        api_client.api_version = "v1"
        
        # Initialize the model attached to the forced v1 client
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=build_system_prompt(resume_context)
        )

        # Build conversation history
        history = []
        for msg in messages[:-1]:
            history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]]
            })

        chat = model.start_chat(history=history)
        response = chat.send_message(messages[-1]["content"])
        return response.text

    except Exception as e:
        error_msg = str(e)
        if "API_KEY" in error_msg.upper() or "invalid" in error_msg.lower():
            return "⚠️ Invalid API key. Please check your Gemini API key in the sidebar settings."
        return f"⚠️ Error connecting to AI: {error_msg}\n\n{get_fallback_response(messages[-1]['content'])}"


def get_fallback_response(user_message: str) -> str:
    """Rule-based fallback responses for common career questions."""
    msg = user_message.lower()

    if any(w in msg for w in ["resume", "cv", "improve"]):
        return """Here are key resume improvement tips:

**Structure:**
• Use reverse chronological order
• Keep to 1-2 pages
• Use consistent formatting

**Content:**
• Add quantifiable achievements (e.g., "Increased performance by 35%")
• Use strong action verbs: Developed, Led, Implemented, Optimized
• Include LinkedIn and GitHub URLs

**ATS Optimization:**
• Mirror keywords from job descriptions
• Avoid tables and complex formatting
• Use standard section headers (Experience, Education, Skills)

**Skills Section:**
• List both technical and soft skills
• Include tools and technologies with version numbers where relevant"""

    elif any(w in msg for w in ["interview", "question", "prepare"]):
        return """**Interview Preparation Guide:**

**Behavioral Questions (STAR method):**
• Situation → Task → Action → Result
• "Tell me about a challenge you overcame..."
• "Describe your biggest achievement..."

**Technical Preparation:**
• Review data structures & algorithms (LeetCode)
• System design basics (for senior roles)
• Know your tech stack deeply

**Common Questions:**
• "Tell me about yourself" — 2-minute pitch
• "Why this company?" — Research thoroughly
• "Where do you see yourself in 5 years?"

**Day-of Tips:**
• Research the company beforehand
• Prepare 5 questions to ask the interviewer
• Test tech setup for virtual interviews"""

    elif any(w in msg for w in ["skill", "learn", "roadmap", "path"]):
        return """**Learning Roadmap Recommendations:**

**For Data Science:**
Python → Statistics → Pandas/NumPy → ML (scikit-learn) → Deep Learning → MLOps

**For Web Development:**
HTML/CSS → JavaScript → React → Node.js → Databases → Cloud

**For DevOps:**
Linux → Networking → Docker → Kubernetes → CI/CD → Terraform

**Top Learning Platforms:**
• 🎓 Coursera — University-level courses
• 💡 Udemy — Practical project-based courses
• 🔧 KodeKloud — Hands-on DevOps/Cloud
• 📚 freeCodeCamp — Free web development
• 🤖 fast.ai — Practical deep learning"""

    elif any(w in msg for w in ["salary", "pay", "compensation"]):
        return """**Salary Benchmarks (INR per annum — Lakhs Per Annum / LPA):**

| Role | Entry Level | Mid Level | Senior Level |
|------|-------------|-----------|--------------|
| Data Scientist | ₹6.5 Lakhs | ₹14.0 Lakhs | ₹24.0+ Lakhs |
| ML Engineer | ₹8.0 Lakhs | ₹16.5 Lakhs | ₹28.0+ Lakhs |
| Web Developer | ₹4.5 Lakhs | ₹9.5 Lakhs | ₹18.0+ Lakhs |
| DevOps Engineer | ₹6.0 Lakhs | ₹12.0 Lakhs | ₹22.0+ Lakhs |
| Cloud Engineer | ₹7.0 Lakhs | ₹13.5 Lakhs | ₹25.0+ Lakhs |

**Negotiation Tips:**
• Research market rates on AmbitionBox, Glassdoor, or Levels.fyi (India specific metrics)
• Do not reveal your current CTC or expected CTC figures in the initial HR rounds
• Evaluate the complete package component layout: Fixed Base Pay + Performance Variable Bonus + RSUs/Esops"""

    elif any(w in msg for w in ["project", "portfolio", "idea"]):
        return """**Portfolio Project Ideas by Role:**

**Data Science:**
• Customer churn prediction dashboard
• NLP sentiment analysis app
• Stock price forecasting model
• Image classification with CNN

**Web Development:**
• Full-stack e-commerce app
• Real-time chat application
• Portfolio website with blog
• REST API with authentication

**DevOps/Cloud:**
• Dockerized microservices app
• CI/CD pipeline on GitHub Actions
• Kubernetes cluster on cloud
• Infrastructure as Code with Terraform

**Tips:** Deploy everything! Use GitHub Pages, Vercel, Render, or AWS Free Tier."""

    else:
        return """Hello! I'm **HireSenseAI Assistant** 👋

I can help you with:
- 📄 **Resume Review** — "How can I improve my resume?"
- 🗺️ **Career Roadmap** — "What should I learn for Data Science?"
- 🎤 **Interview Prep** — "Common interview questions for ML Engineer"
- 💰 **Salary Info** — "What's the salary for a DevOps Engineer?"
- 💡 **Project Ideas** — "Portfolio project ideas for web development"
- 🏆 **Certifications** — "Best certifications for Cloud Engineer\""""
