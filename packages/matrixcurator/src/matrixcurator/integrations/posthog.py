import posthog
from matrixcurator.config.main import settings
import logging

# Maintainer's default PostHog Key for anonymous usage tracking
DEFAULT_POSTHOG_KEY = "phc_example_maintainer_key" # Replace with actual maintainer key if desired

def init_posthog(app_name: str) -> None:
    """
    Initializes PostHog for product analytics.
    Respects TELEMETRY_OPT_OUT and supports Bring-Your-Own-Keys.
    """
    key_to_use = None

    if settings.TELEMETRY_OPT_OUT:
        # If opted out, ONLY use user-provided Key (if any)
        if settings.POSTHOG_API_KEY:
            key_to_use = settings.POSTHOG_API_KEY
    else:
        # If not opted out, use user-provided Key, fallback to maintainer default
        key_to_use = settings.POSTHOG_API_KEY or DEFAULT_POSTHOG_KEY

    if key_to_use:
        posthog.project_api_key = key_to_use
        posthog.host = settings.POSTHOG_HOST
        
        # Silent Failure: Prevent PostHog from logging network errors to stdout/stderr
        # This is crucial for air-gapped environments
        posthog.on_error = lambda e: None
        
        # Also silence the internal posthog logger
        ph_logger = logging.getLogger("posthog")
        ph_logger.setLevel(logging.CRITICAL)
    else:
        posthog.disabled = True

def capture_event(event_name: str, properties: dict = None) -> None:
    """
    Safely captures a PostHog event if PostHog is enabled.
    """
    if not posthog.disabled:
        props = properties or {}
        # Use a generic distinct_id for anonymous telemetry unless specified
        distinct_id = props.pop("distinct_id", "anonymous_user")
        try:
            posthog.capture(distinct_id, event_name, properties=props)
        except Exception:
            # Failsafe to ensure it never crashes the app
            pass
