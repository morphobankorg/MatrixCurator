from unittest.mock import patch, MagicMock

from src.benchmark.modules.dataset.services import preparse_documents

@patch("src.benchmark.modules.dataset.services.os.makedirs")
@patch("src.benchmark.modules.dataset.services.os.path.exists")
def test_preparse_documents_realtime_saving(mock_exists, mock_makedirs):
    """
    Test that preparse_documents calls to_parquet dynamically inside the loop
    when a document is updated, providing real-time resume capability.
    """
    # Setup mocks
    mock_exists.return_value = True
    
    # Create dummy records with 2 rows that need updating
    dummy_records = [
        {"id": "doc1", "mime_type": "text/plain", "filename": "file1.txt", "file_bytes": b"test1", "text": None},
        {"id": "doc2", "mime_type": "text/plain", "filename": "file2.txt", "file_bytes": b"test2", "text": None}
    ]
    
    mock_repo = MagicMock()
    mock_repo.read_documents.return_value = dummy_records

    # Mock pyarrow.parquet.read_table to return our dummy records
    mock_table = MagicMock()
    mock_table.to_pylist.return_value = dummy_records
    with patch("pyarrow.parquet.read_table", return_value=mock_table):
        mock_tool = MagicMock()
        mock_tool.invoke.return_value = "parsed text"
        with patch("src.benchmark.modules.dataset.services.parse_with_txt", mock_tool):
            # Call preparse_documents
            result = preparse_documents(mock_repo, "dummy_path", force=True, limit=None)

            # Assert that to_parquet was called for each document updated
            # Plus once at the beginning to initialize the cache.
            # So it should be called exactly 3 times (1 init + 2 per document).
            assert mock_repo.write_documents.call_count == 3
            
            # Verify the records were updated
            assert result[0]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "parsed text"}]}]
            assert result[1]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "parsed text"}]}]

@patch("src.benchmark.modules.dataset.services.os.makedirs")
@patch("src.benchmark.modules.dataset.services.os.path.exists")
def test_preparse_documents_resilient_parsing(mock_exists, mock_makedirs):
    """
    Test that preparse_documents gracefully handles edge case strings like 'null'
    and empty inputs without throwing NoneType iterability errors.
    """
    mock_exists.return_value = True
    
    # Create a dummy records with edge case 'text' fields
    dummy_records = [
        {"id": "doc1", "mime_type": "text/plain", "filename": "file1.txt", "file_bytes": b"test1", "text": "null"},
        {"id": "doc2", "mime_type": "text/plain", "filename": "file2.txt", "file_bytes": b"test2", "text": "[]"}
    ]
    
    mock_repo = MagicMock()
    mock_repo.read_documents.return_value = dummy_records

    mock_table = MagicMock()
    mock_table.to_pylist.return_value = dummy_records
    with patch("pyarrow.parquet.read_table", return_value=mock_table):
        mock_tool = MagicMock()
        mock_tool.invoke.return_value = "parsed text"
        with patch("src.benchmark.modules.dataset.services.parse_with_txt", mock_tool):
            # This should not raise an exception
            result = preparse_documents(mock_repo, "dummy_path", force=True, limit=None)

            # Both rows should have been processed and overwritten with valid lists
            assert result[0]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "parsed text"}]}]
            assert result[1]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "parsed text"}]}]


@patch("src.benchmark.modules.dataset.services.os.makedirs")
@patch("src.benchmark.modules.dataset.services.os.path.exists")
def test_preparse_documents_null_pages_graceful(mock_exists, mock_makedirs):
    """
    Test that preparse_documents does not crash when encountering explicit 'null' (None) pages
    in existing_parses, but correctly handles it and triggers a re-parse.
    """
    mock_exists.return_value = True
    
    # Create a dummy record where "pages" is explicitly None
    import json
    invalid_text = json.dumps([{"parser": "txt", "pages": None}])
    
    dummy_records = [
        {"id": "doc1", "mime_type": "text/plain", "filename": "file1.txt", "file_bytes": b"test1", "text": invalid_text},
    ]
    
    mock_repo = MagicMock()
    mock_repo.read_documents.return_value = dummy_records

    mock_table = MagicMock()
    mock_table.to_pylist.return_value = dummy_records
    with patch("pyarrow.parquet.read_table", return_value=mock_table):
        mock_tool = MagicMock()
        mock_tool.invoke.return_value = "fixed parsed text"
        with patch("src.benchmark.modules.dataset.services.parse_with_txt", mock_tool):
            # This should not raise a TypeError: 'NoneType' object is not iterable
            result = preparse_documents(mock_repo, "dummy_path", force=True, limit=None)

            # It should have re-parsed and fixed the null pages
            assert result[0]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "fixed parsed text"}]}]
