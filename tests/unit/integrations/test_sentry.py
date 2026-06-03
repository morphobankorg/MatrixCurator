import pytest
from unittest.mock import patch
from src.integrations.sentry import init_sentry, DEFAULT_SENTRY_DSN

@patch("src.integrations.sentry.sentry_sdk.init")
@patch("src.integrations.sentry.settings")
def test_sentry_default_maintainer_telemetry(mock_settings, mock_sentry_init):
    """Test Case: Default Maintainer Telemetry (Opt-Out = False, No User Keys)"""
    mock_settings.TELEMETRY_OPT_OUT = False
    mock_settings.SENTRY_DSN = None
    mock_settings.DEBUG = False

    init_sentry("test_app")

    mock_sentry_init.assert_called_once_with(
        dsn=DEFAULT_SENTRY_DSN,
        traces_sample_rate=1.0,
        environment="production",
        server_name="test_app"
    )

@patch("src.integrations.sentry.sentry_sdk.init")
@patch("src.integrations.sentry.settings")
def test_sentry_complete_opt_out(mock_settings, mock_sentry_init):
    """Test Case: Complete Opt-Out (Opt-Out = True, No User Keys)"""
    mock_settings.TELEMETRY_OPT_OUT = True
    mock_settings.SENTRY_DSN = None

    init_sentry("test_app")

    mock_sentry_init.assert_not_called()

@patch("src.integrations.sentry.sentry_sdk.init")
@patch("src.integrations.sentry.settings")
def test_sentry_byok_override(mock_settings, mock_sentry_init):
    """Test Case: BYOK Override (Opt-Out = True, User Keys Provided)"""
    mock_settings.TELEMETRY_OPT_OUT = True
    mock_settings.SENTRY_DSN = "https://user-dsn@sentry.io/1"
    mock_settings.DEBUG = False

    init_sentry("test_app")

    mock_sentry_init.assert_called_once_with(
        dsn="https://user-dsn@sentry.io/1",
        traces_sample_rate=1.0,
        environment="production",
        server_name="test_app"
    )
