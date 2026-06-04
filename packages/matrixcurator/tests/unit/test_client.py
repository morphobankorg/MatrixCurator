import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from matrixcurator.client import MatrixCuratorClient

@pytest.fixture
def client():
    with patch("matrixcurator.client.setup_logging"):
        return MatrixCuratorClient(app_name="test")

@patch("matrixcurator.client.parse_document")
@patch("matrixcurator.client.capture_event")
def test_parse_document(mock_capture, mock_parse, client):
    mock_parse.return_value = "parsed text"
    
    result = client.parse_document(b"content", "test.pdf")
    
    assert result == "parsed text"
    mock_parse.assert_called_once_with(b"content", "test.pdf")
    mock_capture.assert_called_once_with("document_parsed", {"filename": "test.pdf"})

@pytest.mark.asyncio
@patch("matrixcurator.client.agent_graph.ainvoke", new_callable=AsyncMock)
@patch("matrixcurator.client.capture_event")
async def test_extract_characters_success(mock_capture, mock_ainvoke, client):
    mock_ainvoke.return_value = {
        "extracted_data": {"character_index": 1, "states": {"0": "A"}},
        "errors": []
    }
    
    result = await client.extract_characters("context", [1])
    
    assert len(result["extracted_states"]) == 1
    assert result["extracted_states"][0]["character_index"] == 1
    assert len(result["errors"]) == 0
    mock_capture.assert_called_once()

@patch("matrixcurator.client.generate_document")
@patch("matrixcurator.client.capture_event")
def test_generate_nexus(mock_capture, mock_generate, client):
    mock_generate.return_value = b"updated nexus"
    
    result = client.generate_nexus("original", [{"character_index": 1}])
    
    assert result == b"updated nexus"
    mock_generate.assert_called_once_with(original_nexus="original", extracted_states=[{"character_index": 1}])
    mock_capture.assert_called_once_with("nexus_generated")
