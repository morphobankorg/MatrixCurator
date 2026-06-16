import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from apps.fastapi.src.main import app
from apps.fastapi.src.dependencies import get_client
import io
from matrixcurator import DocumentParseError, NexusFormatError

client = TestClient(app)

@pytest.fixture
def sample_nexus():
    return """#NEXUS
BEGIN TAXA;
    DIMENSIONS NTAX=3;
    TAXLABELS
        Taxon_A
        Taxon_B
        Taxon_C
    ;
END;

BEGIN CHARACTERS;
    DIMENSIONS NCHAR=2;
    FORMAT DATATYPE=STANDARD MISSING=? GAP=- SYMBOLS="0 1";
    MATRIX
    Taxon_A 00
    Taxon_B 11
    Taxon_C 01
    ;
END;
"""

def test_parse_document_txt():
    mock_client = MagicMock()
    mock_client.parse_document.return_value = "This is a test document."
    app.dependency_overrides[get_client] = lambda: mock_client
    file_content = b"This is a test document."
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    
    response = client.post("/api/v1/document/parse", files=files)
    
    assert response.status_code == 200
    assert response.json()["text"] == "This is a test document."

def test_parse_document_unsupported():
    mock_client = MagicMock()
    mock_client.parse_document.side_effect = DocumentParseError("Unsupported file type")
    app.dependency_overrides[get_client] = lambda: mock_client
    file_content = b"fake image"
    files = {"file": ("test.png", io.BytesIO(file_content), "image/png")}
    
    response = client.post("/api/v1/document/parse", files=files)
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_generate_nexus(sample_nexus):
    mock_client = MagicMock()
    app.dependency_overrides[get_client] = lambda: mock_client
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
    
    mock_client.generate_nexus.return_value = b"updated nexus content with CHARSTATELABELS and 1 'Test Char' / 0 'A', 1 'B'"
    
    response = client.post("/api/v1/document/nexus", json=payload)
    
    assert response.status_code == 200
    assert "CHARSTATELABELS" in response.json()["updated_nexus"]
    assert "1 'Test Char' / 0 'A', 1 'B'" in response.json()["updated_nexus"]

def test_generate_nexus_invalid_payload():
    mock_client = MagicMock()
    mock_client.generate_nexus.side_effect = NexusFormatError("MATRIX block not found")
    app.dependency_overrides[get_client] = lambda: mock_client
    payload = {
        "original_nexus": "invalid nexus without m_a_t_r_i_x",
        "extracted_states": []
    }
    
    response = client.post("/api/v1/document/nexus", json=payload)
    
    assert response.status_code == 400
    assert "MATRIX block not found" in response.json()["detail"]
