from langfuse import Langfuse
from src.config.main import settings

# Initialize Langfuse client
langfuse_client = None

if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    langfuse_client = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST
    )

def get_langfuse_client():
    return langfuse_client
