import pytest
from unittest.mock import patch
import importlib
import src.integrations.langfuse

@patch("src.config.main.settings")
@patch("langfuse.Langfuse")
def test_langfuse_no_maintainer_key(mock_langfuse_class, mock_settings):
    """Test Case: Langfuse MUST NOT initialize without user keys (Privacy constraint)"""
    mock_settings.LANGFUSE_PUBLIC_KEY = None
    mock_settings.LANGFUSE_SECRET_KEY = None
    
    # Reload module to trigger initialization logic
    importlib.reload(src.integrations.langfuse)
    
    mock_langfuse_class.assert_not_called()
    assert src.integrations.langfuse.get_langfuse_client() is None

@patch("src.config.main.settings")
@patch("langfuse.Langfuse")
def test_langfuse_user_keys_provided(mock_langfuse_class, mock_settings):
    """Test Case: Langfuse initializes when user keys are provided"""
    mock_settings.LANGFUSE_PUBLIC_KEY = "user_pk"
    mock_settings.LANGFUSE_SECRET_KEY = "user_sk"
    mock_settings.LANGFUSE_HOST = "https://cloud.langfuse.com"
    
    # Reload module to trigger initialization logic
    importlib.reload(src.integrations.langfuse)
    
    mock_langfuse_class.assert_called_once_with(
        public_key="user_pk",
        secret_key="user_sk",
        host="https://cloud.langfuse.com",
        debug=False
    )
    assert src.integrations.langfuse.get_langfuse_client() is not None
