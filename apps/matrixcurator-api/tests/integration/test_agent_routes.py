import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from apps.fastapi.src.main import app
from apps.fastapi.src.dependencies import get_client

client = TestClient(app)

def test_extract_data_success():
    mock_client = MagicMock()
    mock_client.extract_characters = AsyncMock()
    app.dependency_overrides[get_client] = lambda: mock_client
    # Arrange
    mock_client.extract_characters.return_value = {
        "extracted_states": [{
            "character_index": 1,
            "character_name": "Eye color",
            "states": {"0": "blue"}
        }],
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
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["extracted_states"]) == 1
    assert data["extracted_states"][0]["character_name"] == "Eye color"
    assert len(data["errors"]) == 0

def test_extract_data_failure():
    mock_client = MagicMock()
    mock_client.extract_characters = AsyncMock()
    app.dependency_overrides[get_client] = lambda: mock_client
    
    # Arrange
    mock_client.extract_characters.side_effect = Exception("Graph execution failed")
    
    payload = {
        "context": "Eye color is blue (0).",
        "character_indices": [1],
        "model_provider": "test-model"
    }
    
    # Act
    response = client.post("/api/v1/agent/extract", json=payload)
    
    # Assert
    assert response.status_code == 500, response.text
    data = response.json()
    assert "Graph execution failed" in data["detail"]

def test_extract_data_validation_error():
    payload = {
        "context": "Missing indices"
        # character_indices is required
    }
    
    response = client.post("/api/v1/agent/extract", json=payload)
    
    assert response.status_code == 422 # Unprocessable Entity
