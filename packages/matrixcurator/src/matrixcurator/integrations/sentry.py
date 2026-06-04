import sentry_sdk
from matrixcurator.config.main import settings

# Maintainer's default Sentry DSN for anonymous crash reporting
DEFAULT_SENTRY_DSN = "https://example-public-key@o0.ingest.sentry.io/0" # Replace with actual maintainer DSN if desired

def init_sentry(app_name: str) -> None:
    """
    Initializes Sentry for error tracking.
    Respects TELEMETRY_OPT_OUT and supports Bring-Your-Own-Keys.
    """
    dsn_to_use = None

    if settings.TELEMETRY_OPT_OUT:
        # If opted out, ONLY use user-provided DSN (if any)
        if settings.SENTRY_DSN:
            dsn_to_use = settings.SENTRY_DSN
    else:
        # If not opted out, use user-provided DSN, fallback to maintainer default
        dsn_to_use = settings.SENTRY_DSN or DEFAULT_SENTRY_DSN

    if dsn_to_use:
        # Sentry Python SDK fails silently on network errors by default.
        sentry_sdk.init(
            dsn=dsn_to_use,
            traces_sample_rate=1.0,
            environment="production" if not settings.DEBUG else "development",
            server_name=app_name,
        )
