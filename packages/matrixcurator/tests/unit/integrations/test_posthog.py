import pytest
from unittest.mock import patch, MagicMock
from matrixcurator.integrations.posthog import init_posthog, capture_event, DEFAULT_POSTHOG_KEY
import matrixcurator.integrations.posthog as posthog_module

@patch("matrixcurator.integrations.posthog.posthog")
@patch("matrixcurator.integrations.posthog.settings")
def test_posthog_default_maintainer_telemetry(mock_settings, mock_posthog):
    """Test Case: Default Maintainer Telemetry (Opt-Out = False, No User Keys)"""
    mock_settings.TELEMETRY_OPT_OUT = False
    mock_settings.POSTHOG_API_KEY = None
    mock_settings.POSTHOG_HOST = "https://app.posthog.com"

    init_posthog("test_app")

    assert mock_posthog.project_api_key == DEFAULT_POSTHOG_KEY
    assert mock_posthog.host == "https://app.posthog.com"
    assert mock_posthog.disabled is not True

@patch("matrixcurator.integrations.posthog.posthog")
@patch("matrixcurator.integrations.posthog.settings")
def test_posthog_complete_opt_out(mock_settings, mock_posthog):
    """Test Case: Complete Opt-Out (Opt-Out = True, No User Keys)"""
    mock_settings.TELEMETRY_OPT_OUT = True
    mock_settings.POSTHOG_API_KEY = None

    init_posthog("test_app")

    assert mock_posthog.disabled is True

@patch("matrixcurator.integrations.posthog.posthog")
@patch("matrixcurator.integrations.posthog.settings")
def test_posthog_byok_override(mock_settings, mock_posthog):
    """Test Case: BYOK Override (Opt-Out = True, User Keys Provided)"""
    mock_settings.TELEMETRY_OPT_OUT = True
    mock_settings.POSTHOG_API_KEY = "user_ph_key"
    mock_settings.POSTHOG_HOST = "https://app.posthog.com"

    init_posthog("test_app")

    assert mock_posthog.project_api_key == "user_ph_key"
    assert mock_posthog.host == "https://app.posthog.com"
    assert mock_posthog.disabled is not True

@patch("matrixcurator.integrations.posthog.posthog")
def test_posthog_network_failure_during_capture(mock_posthog):
    """Test Case: PostHog Network Failure During Capture"""
    mock_posthog.disabled = False
    mock_posthog.capture.side_effect = Exception("ConnectionError")

    # Should not raise an exception
    capture_event("test_event")
    
    mock_posthog.capture.assert_called_once()
