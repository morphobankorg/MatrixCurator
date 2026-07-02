import os
import pytest
from unittest.mock import patch, MagicMock

from matrixcurator.integrations.langfuse import get_langfuse_client, flush_langfuse_client
import matrixcurator.integrations.langfuse as lf_module

@pytest.fixture(autouse=True)
def reset_langfuse_singleton():
    """Reset the singleton between tests."""
    lf_module._langfuse_client = None
    yield
    lf_module._langfuse_client = None


def test_get_langfuse_client_no_keys():
    """Test that it returns None if public_key is not configured."""
    with patch("matrixcurator.integrations.langfuse.settings") as mock_settings:
        mock_settings.langfuse_public_key = None
        client = get_langfuse_client()
        assert client is None


@patch.dict(os.environ, {}, clear=True)
def test_get_langfuse_client_sets_environ():
    """Test that missing environment variables are set from settings."""
    with patch("matrixcurator.integrations.langfuse.settings") as mock_settings:
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "http://test.langfuse"
        
        with patch("matrixcurator.integrations.langfuse.Langfuse") as mock_lf_class:
            client = get_langfuse_client()
            
            assert os.environ["LANGFUSE_PUBLIC_KEY"] == "pk-test"
            assert os.environ["LANGFUSE_SECRET_KEY"] == "sk-test"
            assert os.environ["LANGFUSE_HOST"] == "http://test.langfuse"
            
            mock_lf_class.assert_called_once_with(
                public_key="pk-test",
                secret_key="sk-test",
                host="http://test.langfuse"
            )


@patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "env-pk", "LANGFUSE_SECRET_KEY": "env-sk"}, clear=True)
def test_get_langfuse_client_respects_existing_environ():
    """Test that existing environment variables are not overwritten."""
    with patch("matrixcurator.integrations.langfuse.settings") as mock_settings:
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "http://test.langfuse"
        
        with patch("matrixcurator.integrations.langfuse.Langfuse"):
            client = get_langfuse_client()
            
            assert os.environ["LANGFUSE_PUBLIC_KEY"] == "env-pk"
            assert os.environ["LANGFUSE_SECRET_KEY"] == "env-sk"
            assert os.environ["LANGFUSE_HOST"] == "http://test.langfuse"


def test_get_langfuse_client_singleton():
    """Test that multiple calls return the same instance."""
    with patch("matrixcurator.integrations.langfuse.settings") as mock_settings:
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "http://test.langfuse"
        
        with patch("matrixcurator.integrations.langfuse.Langfuse") as mock_lf_class:
            mock_lf_class.return_value = MagicMock()
            
            client1 = get_langfuse_client()
            client2 = get_langfuse_client()
            
            assert client1 is client2
            mock_lf_class.assert_called_once()


def test_flush_langfuse_client():
    """Test that flush works safely."""
    # When None, it shouldn't raise
    flush_langfuse_client()
    
    with patch("matrixcurator.integrations.langfuse.settings") as mock_settings:
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "http://test.langfuse"
        
        with patch("matrixcurator.integrations.langfuse.Langfuse") as mock_lf_class:
            mock_client = MagicMock()
            mock_lf_class.return_value = mock_client
            
            get_langfuse_client()
            flush_langfuse_client()
            
            mock_client.flush.assert_called_once()
