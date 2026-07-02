import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import dspy
from matrixcurator.integrations.dspy import configure_dspy
from matrixcurator.integrations.mcp import mcp_session_var

@pytest.fixture
def mock_mcp_session():
    session = AsyncMock()
    
    # Create a mock MCP result
    mock_result = MagicMock()
    mock_result.role = "assistant"
    
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "MCP DSPy Response"
    mock_result.content = [mock_content]
    
    session.create_message.return_value = mock_result
    return session

@patch("matrixcurator.integrations.dspy.DSPyInstrumentor")
def test_configure_dspy(mock_instrumentor):
    # Act
    configure_dspy("gpt-4")
    
    # Assert
    assert isinstance(dspy.settings.lm, dspy.LM)
    assert dspy.settings.lm.__class__.__name__ == "MCPAwareLM"

@pytest.mark.asyncio
@patch("dspy.LM.aforward")
async def test_mcp_aware_lm_aforward_with_session(mock_super_aforward, mock_mcp_session):
    # Arrange
    from matrixcurator.integrations.dspy import MCPAwareLM
    lm = MCPAwareLM("gpt-4")
    
    token = mcp_session_var.set(mock_mcp_session)
    
    try:
        # Act
        response = await lm.aforward(prompt="Hello")
        
        # Assert
        assert response["choices"][0]["message"]["content"] == "MCP DSPy Response"
        mock_mcp_session.create_message.assert_called_once()
        mock_super_aforward.assert_not_called()
    finally:
        mcp_session_var.reset(token)

@pytest.mark.asyncio
@patch("dspy.LM.aforward")
async def test_mcp_aware_lm_aforward_without_session(mock_super_aforward):
    # Arrange
    from matrixcurator.integrations.dspy import MCPAwareLM
    lm = MCPAwareLM("gpt-4")
    
    mock_super_aforward.return_value = {"choices": [{"message": {"content": "Native"}}]}
    
    # Act
    response = await lm.aforward(prompt="Hello")
    
    # Assert
    assert response["choices"][0]["message"]["content"] == "Native"
    mock_super_aforward.assert_called_once()

@pytest.mark.asyncio
@patch("dspy.LM.aforward")
async def test_mcp_aware_lm_aforward_fallback(mock_super_aforward, mock_mcp_session):
    # Arrange
    from matrixcurator.integrations.dspy import MCPAwareLM
    lm = MCPAwareLM("gpt-4")
    
    mock_mcp_session.create_message.side_effect = Exception("MCP Error")
    token = mcp_session_var.set(mock_mcp_session)
    
    mock_super_aforward.return_value = {"choices": [{"message": {"content": "Fallback"}}]}
    
    try:
        # Act
        response = await lm.aforward(prompt="Hello")
        
        # Assert
        assert response["choices"][0]["message"]["content"] == "Fallback"
        mock_mcp_session.create_message.assert_called_once()
        mock_super_aforward.assert_called_once()
    finally:
        mcp_session_var.reset(token)
