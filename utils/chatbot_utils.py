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
    """Sends the user prompt to the Gemini API using the standard v1beta API endpoint."""
    try:
        if not api_key:
            return "⚠️ Gemini API key is missing. Please check your system settings."

        # Using v1beta for reliable text generation formatting
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        system_context = build_system_prompt()
        
        # Standard structural payload expected by Google's API
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{system_context}\n\nUser Question: {prompt}"}
                    ]
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            try:
                # Target the exact nested response pathway returned by Google
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return "⚠️ API responded successfully, but the message formatting was unexpected."
        else:
            # Fall back to technical details if the key itself is rejected by Google
            return f"❌ API Error ({response.status_code}): {response.text}"

    except Exception as e:
        # If network times out or fails, trigger standard fallback message
        return get_fallback_response(prompt)


def get_fallback_response(prompt: str) -> str:
    """Fallback handler if the main Gemini response fails entirely."""
    return "⚠️ The chatbot is currently experiencing technical difficulties connectivity-side. Please double-check your Streamlit Secrets API key values."
