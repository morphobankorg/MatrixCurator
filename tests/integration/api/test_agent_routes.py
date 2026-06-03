import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app

client = TestClient(app)

@patch("src.modules.agent.router.agent_graph.ainvoke")
def test_extract_data_success(mock_ainvoke):
    # Arrange
    mock_ainvoke.return_value = {
        "extracted_data": {
            "character_index": 1,
            "character_name": "Eye color",
            "states": {"0": "blue"}
        },
        "errors": []
    }
    
    payload = {
        "context": "Eye color is blue (0).",
        "character_indices": [1],
        "model_provider": "test-model"
    }
    
    # Act
    response = client.post("/api/v1/agent/extract", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["extracted_states"]) == 1
    assert data["extracted_states"][0]["character_name"] == "Eye color"
    assert len(data["errors"]) == 0

@patch("src.modules.agent.router.agent_graph.ainvoke")
def test_extract_data_failure(mock_ainvoke):
    # Arrange
    mock_ainvoke.side_effect = Exception("Graph execution failed")
    
    payload = {
        "context": "Eye color is blue (0).",
        "character_indices": [1],
        "model_provider": "test-model"
    }
    
    # Act
    response = client.post("/api/v1/agent/extract", json=payload)
    
    # Assert
    assert response.status_code == 200 # The endpoint catches the error and returns it in the response body
    data = response.json()
    assert len(data["extracted_states"]) == 0
    assert len(data["errors"]) == 1
    assert "Failed to extract character 1: Graph execution failed" in data["errors"][0]

def test_extract_data_validation_error():
    payload = {
        "context": "Missing indices"
        # character_indices is required
    }
    
    response = client.post("/api/v1/agent/extract", json=payload)
    
    assert response.status_code == 422 # Unprocessable Entity
