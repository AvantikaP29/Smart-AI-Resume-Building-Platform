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
    """Sends the user prompt to the Gemini API using secure background secrets directly."""
    try:
        # FORCE load directly from Streamlit secrets to prevent broken session variables from breaking it
        target_key = st.secrets.get("GEMINI_API_KEY", None)
            
        if not target_key:
            return "⚠️ Connection Error: The secret 'GEMINI_API_KEY' was not found in your Streamlit Advanced Settings -> Secrets panel."

        # Clean any accidental spaces or linebreaks
        target_key = str(target_key).strip()

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
            # THIS WILL PRINT THE EXACT REASON INSTEAD OF THE GENERIC FALLBACK
            return f"❌ Google API Rejection ({response.status_code}): {response.text}"
            
    except Exception as e:
        return f"❌ System Error: {str(e)}"

def get_fallback_response(prompt: str, *args, **kwargs) -> str:
    # Point directly to the diagnostic function response above
    return get_gemini_response(prompt)
