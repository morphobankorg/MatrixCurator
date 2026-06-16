import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from matrixcurator.integrations.litellm import acompletion, completion
from matrixcurator.integrations.mcp import mcp_session_var

@pytest.fixture
def mock_mcp_session():
    session = AsyncMock()
    
    # Create a mock MCP result
    mock_result = MagicMock()
    mock_result.role = "assistant"
    mock_result.model = "mcp-model"
    
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "MCP Response"
    mock_result.content = [mock_content]
    
    session.create_message.return_value = mock_result
    return session

@pytest.mark.asyncio
@patch("matrixcurator.integrations.litellm.litellm.acompletion")
async def test_acompletion_with_mcp_session(mock_litellm_acompletion, mock_mcp_session):
    # Arrange
    token = mcp_session_var.set(mock_mcp_session)
    
    try:
        # Act
        response = await acompletion(model="gpt-4", messages=[{"role": "user", "content": "Hi"}])
        
        # Assert
        assert response.choices[0].message.content == "MCP Response"
        assert response.model == "mcp-model"
        mock_mcp_session.create_message.assert_called_once()
        mock_litellm_acompletion.assert_not_called()
    finally:
        mcp_session_var.reset(token)

@pytest.mark.asyncio
@patch("matrixcurator.integrations.litellm.litellm.acompletion")
async def test_acompletion_without_mcp_session(mock_litellm_acompletion):
    # Arrange
    mock_litellm_acompletion.return_value = MagicMock()
    
    # Act
    await acompletion(model="gpt-4", messages=[{"role": "user", "content": "Hi"}])
    
    # Assert
    mock_litellm_acompletion.assert_called_once()

@pytest.mark.asyncio
@patch("matrixcurator.integrations.litellm.litellm.acompletion")
async def test_acompletion_mcp_fallback(mock_litellm_acompletion, mock_mcp_session):
    # Arrange
    mock_mcp_session.create_message.side_effect = Exception("MCP Error")
    token = mcp_session_var.set(mock_mcp_session)
    
    mock_litellm_acompletion.return_value = MagicMock()
    
    try:
        # Act
        await acompletion(model="gpt-4", messages=[{"role": "user", "content": "Hi"}])
        
        # Assert
        mock_mcp_session.create_message.assert_called_once()
        mock_litellm_acompletion.assert_called_once()
    finally:
        mcp_session_var.reset(token)

@patch("matrixcurator.integrations.litellm.litellm.completion")
def test_completion_without_mcp_session(mock_litellm_completion):
    # Arrange
    mock_litellm_completion.return_value = MagicMock()
    
    # Act
    completion(model="gpt-4", messages=[{"role": "user", "content": "Hi"}])
    
    # Assert
    mock_litellm_completion.assert_called_once()
