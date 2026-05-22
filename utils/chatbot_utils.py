import os
import re
import requests
import streamlit as st
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


def get_gemini_response(prompt: str, *args, **kwargs) -> str:
    """
    Sends the user prompt to the Gemini API. 
    Uses *args and **kwargs so it never crashes no matter how modules/chatbot.py calls it.
    """
    try:
        # Pull directly from secure background secrets
        target_key = st.secrets.get("GEMINI_API_KEY", None)
            
        if not target_key:
            return "⚠️ Gemini API key is missing. Please verify GEMINI_API_KEY is configured in your Streamlit Secrets."

        # Clean any accidental spaces
        target_key = str(target_key).strip()

        # Reliable v1beta endpoint structure
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={target_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        system_context = build_system_prompt()
        
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

        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return "⚠️ API responded, but the message formatting structure was unexpected."
        else:
            return f"❌ API Error ({response.status_code}): {response.text}"

    except Exception as e:
        return f"❌ Connectivity Error: {str(e)}"


def get_fallback_response(prompt: str, *args, **kwargs) -> str:
    """Fallback handler that accepts any arguments to prevent crashes."""
    return "⚠️ The chatbot is currently experiencing technical difficulties connectivity-side."
