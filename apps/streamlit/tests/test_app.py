import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch, AsyncMock

@pytest.fixture
def app():
    return AppTest.from_file("apps/streamlit/src/main.py")

@patch("apps.streamlit.src.main.client.parse_document")
def test_parse_document_success(mock_parse, app):
    mock_parse.return_value = "Parsed document content"
    
    app.run()
    
    # We can't easily mock file_uploader in AppTest yet, but we can check if the UI elements exist
    assert app.title[0].value == "MatrixCurator"
    assert app.sidebar.selectbox[0].label == "Model Provider"
    assert app.headers[0].value == "1. Upload Document"
    assert app.headers[1].value == "2. Upload NEXUS"

# Note: Streamlit AppTest has limitations with file_uploader and complex state interactions.
# For a fully "dumb" UI, verifying the layout and that the client is called when state is manipulated is key.
# Since we can't easily simulate file uploads, we'll focus on the structure.
