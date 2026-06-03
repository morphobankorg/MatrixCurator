import pytest
from fastapi.testclient import TestClient
from src.main import app
import io

client = TestClient(app)

def test_parse_document_txt():
    file_content = b"This is a test document."
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    
    response = client.post("/api/v1/document/parse", files=files)
    
    assert response.status_code == 200
    assert response.json()["text"] == "This is a test document."

def test_parse_document_unsupported():
    file_content = b"fake image"
    files = {"file": ("test.png", io.BytesIO(file_content), "image/png")}
    
    response = client.post("/api/v1/document/parse", files=files)
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_generate_nexus(sample_nexus):
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
    
    response = client.post("/api/v1/document/nexus", json=payload)
    
    assert response.status_code == 200
    assert "CHARSTATELABELS" in response.json()["updated_nexus"]
    assert "1 'Test Char' / 0 'A', 1 'B'" in response.json()["updated_nexus"]

def test_generate_nexus_invalid_payload():
    payload = {
        "original_nexus": "invalid nexus without m_a_t_r_i_x",
        "extracted_states": []
    }
    
    response = client.post("/api/v1/document/nexus", json=payload)
    
    assert response.status_code == 400
    assert "MATRIX block not found" in response.json()["detail"]
