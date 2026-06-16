from unittest.mock import patch
import importlib
import matrixcurator.integrations.langfuse

@patch("matrixcurator.config.main.settings")
@patch("langfuse.Langfuse")
def test_langfuse_no_maintainer_key(mock_langfuse_class, mock_settings):
    """Test Case: Langfuse MUST NOT initialize without user keys (Privacy constraint)"""
    mock_settings.langfuse_public_key = None
    mock_settings.langfuse_secret_key = None
    
    # Reload module to trigger initialization logic
    importlib.reload(matrixcurator.integrations.langfuse)
    
    mock_langfuse_class.assert_not_called()
    assert matrixcurator.integrations.langfuse.get_langfuse_client() is None

@patch("matrixcurator.config.main.settings")
@patch("langfuse.Langfuse")
def test_langfuse_user_keys_provided(mock_langfuse_class, mock_settings):
    """Test Case: Langfuse initializes when user keys are provided"""
    mock_settings.langfuse_public_key = "user_pk"
    mock_settings.langfuse_secret_key = "user_sk"
    mock_settings.langfuse_host = "https://cloud.langfuse.com"
    
    # Reload module to trigger initialization logic
    importlib.reload(matrixcurator.integrations.langfuse)
    
    mock_langfuse_class.assert_called_once_with(
        public_key="user_pk",
        secret_key="user_sk",
        host="https://cloud.langfuse.com",
        debug=False
    )
    assert matrixcurator.integrations.langfuse.get_langfuse_client() is not None
