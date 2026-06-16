import pytest
from unittest.mock import AsyncMock, MagicMock

from matrixcurator.integrations.mcp import MCPSamplingError, sample_message

@pytest.mark.asyncio
async def test_sample_message_success():
    # Arrange
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_session.create_message.return_value = mock_result
    
    messages = [{"role": "user", "content": "Hello"}]
    
    # Act
    result = await sample_message(mock_session, messages)
    
    # Assert
    assert result == mock_result
    mock_session.create_message.assert_called_once()
    
    # Check the arguments passed to create_message
    call_args = mock_session.create_message.call_args[1]
    assert call_args["messages"] == [{"role": "user", "content": {"type": "text", "text": "Hello"}}]

@pytest.mark.asyncio
async def test_sample_message_with_images():
    # Arrange
    mock_session = AsyncMock()
    mock_session.create_message.return_value = MagicMock()
    
    messages = [
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": "What is this?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KGgo="}}
            ]
        }
    ]
    
    # Act
    await sample_message(mock_session, messages)
    
    # Assert
    call_args = mock_session.create_message.call_args[1]
    expected_content = [
        {"type": "text", "text": "What is this?"},
        {"type": "image", "data": "iVBORw0KGgo=", "mimeType": "png"}
    ]
    assert call_args["messages"][0]["content"] == expected_content

@pytest.mark.asyncio
async def test_sample_message_failure():
    # Arrange
    mock_session = AsyncMock()
    mock_session.create_message.side_effect = Exception("Connection lost")
    
    messages = [{"role": "user", "content": "Hello"}]
    
    # Act & Assert
    with pytest.raises(MCPSamplingError, match="Failed to sample message via MCP: Connection lost"):
        await sample_message(mock_session, messages)
