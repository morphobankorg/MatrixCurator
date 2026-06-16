import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions
from docling.models.inference_engines.vlm.base import VlmEngineInput

from matrixcurator.integrations.docling import McpVlmEngine
from matrixcurator.integrations.mcp import mcp_session_var

@pytest.fixture
def mock_mcp_session():
    session = AsyncMock()
    
    # Create a mock MCP result
    mock_result = MagicMock()
    mock_result.role = "assistant"
    
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "MCP Docling Response"
    mock_result.content = [mock_content]
    
    session.create_message.return_value = mock_result
    return session

@pytest.fixture
def mock_vlm_input():
    input_data = MagicMock(spec=VlmEngineInput)
    input_data.prompt = "Describe this image"
    input_data.temperature = 0.5
    input_data.max_new_tokens = 100
    
    # Mock PIL Image
    mock_image = MagicMock()
    mock_image.copy.return_value = mock_image
    mock_image.convert.return_value = mock_image
    input_data.image = mock_image
    
    return input_data

@patch("matrixcurator.integrations.docling.ApiVlmEngine.predict_batch")
def test_mcp_vlm_engine_without_session(mock_super_predict, mock_vlm_input):
    # Arrange
    options = ApiVlmOptions(url="http://localhost:8000")
    engine = McpVlmEngine(enable_remote_services=True, options=options)
    
    mock_super_predict.return_value = [MagicMock()]
    
    # Act
    result = engine.predict_batch([mock_vlm_input])
    
    # Assert
    mock_super_predict.assert_called_once_with([mock_vlm_input])
    assert len(result) == 1

@patch("matrixcurator.integrations.docling.ApiVlmEngine.predict_batch")
def test_mcp_vlm_engine_fallback(mock_super_predict, mock_vlm_input, mock_mcp_session):
    # Arrange
    options = ApiVlmOptions(url="http://localhost:8000")
    engine = McpVlmEngine(enable_remote_services=True, options=options)
    
    mock_mcp_session.create_message.side_effect = Exception("MCP Error")
    token = mcp_session_var.set(mock_mcp_session)
    
    mock_super_predict.return_value = [MagicMock()]
    
    try:
        # Act
        result = engine.predict_batch([mock_vlm_input])
        
        # Assert
        mock_super_predict.assert_called_once_with([mock_vlm_input])
        assert len(result) == 1
    finally:
        mcp_session_var.reset(token)
