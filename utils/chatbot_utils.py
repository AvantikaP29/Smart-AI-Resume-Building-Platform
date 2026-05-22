import os
import requests
import streamlit as st
from typing import Dict, Optional

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
    """Sends the user prompt to the Gemini API securely."""
    try:
        # Retrieve the key from Streamlit secrets
        raw_key = st.secrets.get("GEMINI_API_KEY", None)
        if not raw_key:
            return "⚠️ Gemini API key is missing in Streamlit Secrets."

        # Clean the string completely BEFORE inserting it into the URL
        target_key = str(raw_key).strip()

        # FIXED URL: Removed the accidental trailing string injection
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={target_key}"
        
        headers = {"Content-Type": "application/json"}
        system_context = build_system_prompt()
        
        data = {
            "contents": [{
                "role": "user",
                "parts": [{"text": f"{system_context}\n\nUser Question: {prompt}"}]
            }]
        }

        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"❌ API Error ({response.status_code}): {response.text}"
            
    except Exception as e:
        return f"❌ Connectivity Error: {str(e)}"

def get_fallback_response(prompt: str, *args, **kwargs) -> str:
    return "⚠️ The chatbot is currently experiencing technical difficulties connectivity-side."
