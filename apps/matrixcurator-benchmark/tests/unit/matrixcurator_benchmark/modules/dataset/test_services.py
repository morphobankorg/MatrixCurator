import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from matrixcurator_benchmark.modules.dataset.services import preparse_documents, sync_datasets
from matrixcurator.utils.concurrency import RateLimitConfig

@pytest.mark.asyncio
@patch("matrixcurator_benchmark.modules.dataset.services.os.makedirs")
@patch("matrixcurator_benchmark.modules.dataset.services.os.path.exists")
async def test_preparse_documents_realtime_saving(mock_exists, mock_makedirs):
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
        mock_tool.ainvoke = AsyncMock(return_value="parsed text")
        with patch("matrixcurator_benchmark.modules.dataset.services.parse_with_txt", mock_tool):
            # Call preparse_documents
            result = await preparse_documents(mock_repo, "dummy_path", force=True, limit=None)

            # Assert that to_parquet was called for each document updated
            # Plus once at the beginning to initialize the cache.
            # So it should be called exactly 3 times (1 init + 2 per document).
            assert mock_repo.write_documents.call_count == 3
            
            # Verify the records were updated
            assert result[0]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "parsed text"}]}]
            assert result[1]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "parsed text"}]}]

@pytest.mark.asyncio
@patch("matrixcurator_benchmark.modules.dataset.services.os.makedirs")
@patch("matrixcurator_benchmark.modules.dataset.services.os.path.exists")
async def test_preparse_documents_resilient_parsing(mock_exists, mock_makedirs):
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
        mock_tool.ainvoke = AsyncMock(return_value="parsed text")
        with patch("matrixcurator_benchmark.modules.dataset.services.parse_with_txt", mock_tool):
            # This should not raise an exception
            result = await preparse_documents(mock_repo, "dummy_path", force=True, limit=None)

            # Both rows should have been processed and overwritten with valid lists
            assert result[0]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "parsed text"}]}]
            assert result[1]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "parsed text"}]}]

@pytest.mark.asyncio
@patch("matrixcurator_benchmark.modules.dataset.services.os.makedirs")
@patch("matrixcurator_benchmark.modules.dataset.services.os.path.exists")
async def test_preparse_documents_null_pages_graceful(mock_exists, mock_makedirs):
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
        mock_tool.ainvoke = AsyncMock(return_value="fixed parsed text")
        with patch("matrixcurator_benchmark.modules.dataset.services.parse_with_txt", mock_tool):
            # This should not raise a TypeError: 'NoneType' object is not iterable
            result = await preparse_documents(mock_repo, "dummy_path", force=True, limit=None)

            # It should have re-parsed and fixed the null pages
            assert result[0]["text"] == [{"parser": "txt", "pages": [{"page": 1, "content": "fixed parsed text"}]}]


@pytest.mark.asyncio
async def test_sync_datasets_filters_character_states_by_document():
    mock_parquet_repo = MagicMock()
    # Characters array has states for doc1 and doc2
    mock_parquet_repo.read_character_states.return_value = [
        {"document_id": "doc1", "character": {"index": 1}},
        {"document_id": "doc2", "character": {"index": 2}},
        {"document_id": "doc3", "character": {"index": 3}}
    ]
    
    # We only supply doc1 and doc3 in the docs array
    docs = [
        {"id": "doc1", "text": []},
        {"document_id": "doc3", "text": []}
    ]
    
    mock_langfuse_repo = MagicMock()
    mock_langfuse_repo.upsert_dataset_item = AsyncMock()
    mock_client = MagicMock()
    
    await sync_datasets(mock_parquet_repo, mock_langfuse_repo, mock_client, docs)
    
    # Total upserts should be 2 docs + 2 char states (doc1 and doc3) = 4
    assert mock_langfuse_repo.upsert_dataset_item.call_count == 4
    
    # Check that doc2 character was filtered out
    char_call_args = [
        call[0] for call in mock_langfuse_repo.upsert_dataset_item.call_args_list
        if call[0][1] == "character_states"
    ]
    
    assert len(char_call_args) == 2
    assert char_call_args[0][2]["input"]["document_id"] == "doc1"
    assert char_call_args[1][2]["input"]["document_id"] == "doc3"


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.modules.dataset.services.AsyncRateLimiter", spec=True)
async def test_sync_datasets_sequential_and_schemas(mock_rate_limiter_cls):
    """
    Test that sync_datasets constructs the correct expected schemas for both datasets
    and respects rate limiting using AsyncRateLimiter.
    """
    mock_parquet_repo = MagicMock()
    
    # Mock Character States input
    mock_parquet_repo.read_character_states.return_value = [
        {
            "document_id": "doc1",
            "character": {"name": "m3 cristid obliqua", "index": 81},
            "states": [{"name": "State 1", "index": 0}],
            "pages": [1]
        }
    ]
    
    mock_langfuse_repo = MagicMock()
    mock_langfuse_repo.upsert_dataset_item = AsyncMock()
    
    mock_client = MagicMock()
    
    # Mock Documents input
    docs = [
        {
            "id": "doc1",
            "mime_type": "application/pdf",
            "filename": "test.pdf",
            "text": [
                {
                    "parser": "docling",
                    "pages": [
                        {"page": 1, "content": "12345"},
                        {"page": 2, "content": "67890"}
                    ]
                }
            ]
        }
    ]
    
    # Set the rate limit config directly
    from matrixcurator_benchmark.config.main import settings
    original_rate_limit = settings.langfuse_rate_limit
    settings.langfuse_rate_limit = RateLimitConfig(per_minute=100)
    
    mock_limiter = AsyncMock()
    mock_rate_limiter_cls.return_value = mock_limiter
    
    try:
        await sync_datasets(mock_parquet_repo, mock_langfuse_repo, mock_client, docs)
        
        # We expect 2 upserts (1 doc, 1 char state) and 2 acquire calls
        assert mock_langfuse_repo.upsert_dataset_item.call_count == 2
        assert mock_limiter.acquire.call_count == 2
        
        # Verify Documents schema
        doc_call_args = mock_langfuse_repo.upsert_dataset_item.call_args_list[0][0]
        assert doc_call_args[1] == "documents"
        doc_item = doc_call_args[2]
        assert doc_item["id"] == "Doc-doc1"
        assert doc_item["input"]["id"] == "Doc-doc1"
        assert doc_item["input"]["filename"] == "test.pdf"
        assert doc_item["input"]["mimetype"] == "application/pdf"
        
        import json
        expected_output = json.loads(doc_item["expected_output"])
        assert expected_output["pages"] == [1, 2]
        assert expected_output["character_count"] == 10  # 5 + 5 chars
        
        # Verify Character States schema
        char_call_args = mock_langfuse_repo.upsert_dataset_item.call_args_list[1][0]
        assert char_call_args[1] == "character_states"
        char_item = char_call_args[2]
        assert char_item["input"]["id"] == "Doc-doc1-Char-81"
        assert char_item["input"]["document_id"] == "doc1"
        assert char_item["input"]["character_index"] == 81
        
        char_expected_output = json.loads(char_item["expected_output"])
        assert "character" in char_expected_output
        assert char_expected_output["character"]["name"] == "m3 cristid obliqua"
        assert char_expected_output["character"]["index"] == 81
        assert len(char_expected_output["character"]["states"]) == 1
        assert char_expected_output["character"]["states"][0]["name"] == "State 1"
        
    finally:
        # Restore setting
        settings.langfuse_rate_limit = original_rate_limit
