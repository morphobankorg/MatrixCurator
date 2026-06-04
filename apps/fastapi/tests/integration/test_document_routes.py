import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from apps.fastapi.src.main import app
import io
from matrixcurator.exceptions import DocumentParseError, NexusFormatError

client = TestClient(app)

@patch("apps.fastapi.src.routers.document.client.parse_document")
def test_parse_document_txt(mock_parse):
    mock_parse.return_value = "This is a test document."
    file_content = b"This is a test document."
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    
    response = client.post("/api/v1/document/parse", files=files)
    
    assert response.status_code == 200
    assert response.json()["text"] == "This is a test document."

@patch("apps.fastapi.src.routers.document.client.parse_document")
def test_parse_document_unsupported(mock_parse):
    mock_parse.side_effect = DocumentParseError("Unsupported file type")
    file_content = b"fake image"
    files = {"file": ("test.png", io.BytesIO(file_content), "image/png")}
    
    response = client.post("/api/v1/document/parse", files=files)
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

@patch("apps.fastapi.src.routers.document.client.generate_nexus")
def test_generate_nexus(mock_generate, sample_nexus):
    payload = {
        "original_nexus": sample_nexus,
        "extracted_states": [
            {
                "character_index": 1,
                "character_name": "Test Char",
                "states": {"0": "A", "1": "B"}
            }
        ]
    }
    
    mock_generate.return_value = b"updated nexus content with CHARSTATELABELS and 1 'Test Char' / 0 'A', 1 'B'"
    
    response = client.post("/api/v1/document/nexus", json=payload)
    
    assert response.status_code == 200
    assert "CHARSTATELABELS" in response.json()["updated_nexus"]
    assert "1 'Test Char' / 0 'A', 1 'B'" in response.json()["updated_nexus"]

@patch("apps.fastapi.src.routers.document.client.generate_nexus")
def test_generate_nexus_invalid_payload(mock_generate):
    mock_generate.side_effect = NexusFormatError("MATRIX block not found")
    payload = {
        "original_nexus": "invalid nexus without m_a_t_r_i_x",
        "extracted_states": []
    }
    
    response = client.post("/api/v1/document/nexus", json=payload)
    
    assert response.status_code == 400
    assert "MATRIX block not found" in response.json()["detail"]
