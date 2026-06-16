import os
from typing import List

def get_available_models() -> List[str]:
    """
    Returns a curated list of litellm-compatible model strings based on the 
    provider API keys currently configured in the environment.
    """
    available_models = []
    
    # OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        available_models.extend([
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "o1-preview",
            "o1-mini"
        ])
        
    # Google Gemini
    if os.environ.get("GEMINI_API_KEY"):
        available_models.extend([
            "gemini/gemini-1.5-flash-8b",
            "gemini/gemini-1.5-flash",
            "gemini/gemini-1.5-pro",
            "gemini/gemini-2.0-flash-exp"
        ])
        
    # Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        available_models.extend([
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229"
        ])
        
    # Groq
    if os.environ.get("GROQ_API_KEY"):
        available_models.extend([
            "groq/llama3-8b-8192",
            "groq/llama3-70b-8192",
            "groq/mixtral-8x7b-32768"
        ])
        
    return available_models
