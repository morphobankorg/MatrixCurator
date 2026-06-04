# src/integrations/langfuse.py
from langfuse import Langfuse
from matrixcurator.config.main import settings
import logging

# Initialize Langfuse client
langfuse_client = None

if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    # We only initialize Langfuse if the user explicitly provides their keys.
    # We do NOT provide a default maintainer key for Langfuse to protect user privacy.
    
    # Silent Failure: Ensure Langfuse doesn't spam logs on network errors
    langfuse_logger = logging.getLogger("langfuse")
    langfuse_logger.setLevel(logging.CRITICAL)
    
    langfuse_client = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
        debug=False,
    )

def get_langfuse_client():
    return langfuse_client
