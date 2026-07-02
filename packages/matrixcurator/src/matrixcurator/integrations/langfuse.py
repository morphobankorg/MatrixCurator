import os
from typing import Optional
from lume import langfuse
from langfuse import Langfuse
from matrixcurator.config.main import settings

_langfuse_client: Optional[Langfuse] = None

def get_langfuse_client() -> Optional[Langfuse]:
    """
    Returns a configured Langfuse client singleton.
    Reads configuration from matrixcurator.config.main.settings,
    overrides os.environ keys dynamically if missing,
    and initializes the Langfuse client securely.
    """
    global _langfuse_client
    
    if _langfuse_client is not None:
        return _langfuse_client

    if not settings.langfuse_public_key:
        return None

    # Override os.environ to ensure @observe works
    if "LANGFUSE_PUBLIC_KEY" not in os.environ and settings.langfuse_public_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    if "LANGFUSE_SECRET_KEY" not in os.environ and settings.langfuse_secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    if "LANGFUSE_HOST" not in os.environ and settings.langfuse_host:
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host

    _langfuse_client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    return _langfuse_client

def flush_langfuse_client() -> None:
    """
    Safely flushes the active Langfuse client singleton.
    """
    global _langfuse_client
    if _langfuse_client is not None:
        _langfuse_client.flush()
