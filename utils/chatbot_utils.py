import os
import re
import requests
from typing import List, Dict, Optional

GEMINI_AVAILABLE = True

def build_system_prompt(resume_context: Optional[Dict] = None) -> str:
    """Build chatbot system prompt with optional resume context."""
    
    base = """You are HireSenseAI Assistant - an expert career counselor and resume coach.
You help candidates with:
- Resume improvement and ATS optimization
- Career roadmaps and learning paths
- Interview preparation and tips
- Skill gap analysis and recommendations
- Job search strategies
- Project ideas for portfolio building"""
    
    return base


def get_gemini_response(prompt: str, api_key: str) -> str:
    """Sends the user prompt to the Gemini API and returns the response."""
    try:
        INBUILT_KEY = api_key 
        
        if not INBUILT_KEY:
            return "⚠️ Gemini API key is missing. Please check your system settings."

        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={INBUILT_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Automatically build the system context guidelines
        system_context = build_system_prompt()
        
        data = {
            "contents": [{
                "parts": [{"text": f"{system_context}\n\nUser Question: {prompt}"}]
            }]
        }

        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"❌ API Error ({response.status_code}): {response.text}"

    except Exception as e:
        return f"❌ Python Error: {str(e)}"


def get_fallback_response(prompt: str) -> str:
    """Fallback handler if the main Gemini response fails."""
    return "⚠️ The chatbot is currently experiencing technical difficulties. Please try again in a moment."
