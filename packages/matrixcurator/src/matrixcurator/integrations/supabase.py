# src/integrations/supabase.py
from supabase import create_client, Client
from matrixcurator.config.main import settings


def get_supabase_client() -> Client:
    """
    Returns a configured Supabase client using the settings.
    Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to be set.
    """
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment"
        )

    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# Singleton instance
supabase_client = None


def get_client() -> Client:
    global supabase_client
    if supabase_client is None:
        supabase_client = get_supabase_client()
    return supabase_client
