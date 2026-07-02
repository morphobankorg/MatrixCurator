import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from matrixcurator.modules.retrieval.services import chunk_text, embed_and_store_chunks, retrieve_context, vectorize_document
from matrixcurator.modules.retrieval.repositories.supabase import insert_chunks, query_similar_chunks

def test_chunk_text():
    text = "A" * 2000
    chunks = chunk_text(text, document_id="doc1", chunk_size=1000, chunk_overlap=100)
    assert len(chunks) > 1
    assert chunks[0]["document_id"] == "doc1"
    assert "content" in chunks[0]

@pytest.mark.asyncio
@patch('matrixcurator.modules.retrieval.services._fetch_embeddings_with_retry', new_callable=AsyncMock)
@patch('matrixcurator.modules.retrieval.services._get_insert_chunks')
async def test_embed_and_store_chunks(mock_get_insert, mock_fetch):
    mock_insert = MagicMock()
    mock_get_insert.return_value = mock_insert
    chunks = [{"id": "1", "document_id": "doc1", "content": "hello", "metadata": {}, "embedding": None}]
    
    # Mock litellm aembedding response
    mock_response = MagicMock()
    mock_response.data = [{"embedding": [0.1, 0.2, 0.3]}]
    mock_fetch.return_value = mock_response
    
    await embed_and_store_chunks(chunks)
    
    mock_fetch.assert_called_once()
    assert chunks[0]["embedding"] == [0.1, 0.2, 0.3]
    mock_insert.assert_called_once_with(chunks)

@pytest.mark.asyncio
@patch('matrixcurator.modules.retrieval.services._fetch_embeddings_with_retry', new_callable=AsyncMock)
@patch('matrixcurator.modules.retrieval.services._get_query_similar_chunks')
async def test_retrieve_context(mock_get_query, mock_fetch):
    mock_query = MagicMock()
    mock_get_query.return_value = mock_query
    
    # Mock embedding
    mock_response = MagicMock()
    mock_response.data = [{"embedding": [0.1, 0.2, 0.3]}]
    mock_fetch.return_value = mock_response
    
    # Mock query
    mock_query.return_value = [{"content": "Result 1"}, {"content": "Result 2"}]
    
    context = await retrieve_context("query")
    
    mock_fetch.assert_called_once()
    mock_query.assert_called_once_with(embedding=[0.1, 0.2, 0.3], match_count=5, document_id=None)
    assert context == "Result 1\n\nResult 2"

@pytest.mark.asyncio
@patch('matrixcurator.modules.retrieval.services._fetch_embeddings_with_retry', new_callable=AsyncMock)
@patch('matrixcurator.modules.retrieval.services._get_insert_chunks')
@patch('asyncio.sleep', new_callable=AsyncMock)
async def test_embed_and_store_chunks_batching(mock_sleep, mock_get_insert, mock_fetch):
    mock_insert = MagicMock()
    mock_get_insert.return_value = mock_insert
    
    # Create 250 chunks
    chunks = [{"id": str(i), "document_id": "doc1", "content": f"hello {i}", "metadata": {}, "embedding": None} for i in range(250)]
    
    def side_effect(texts):
        mock_response = MagicMock()
        mock_response.data = [{"embedding": [0.1] * len(text)} for text in texts]
        return mock_response
        
    mock_fetch.side_effect = side_effect
    
    await embed_and_store_chunks(chunks)
    
    # Should be called 3 times (100, 100, 50)
    assert mock_fetch.call_count == 3
    # Should have slept 2 times
    assert mock_sleep.call_count == 2
    # Should have inserted 3 times
    assert mock_insert.call_count == 3

@pytest.mark.asyncio
@patch('matrixcurator.modules.retrieval.services.aembedding', new_callable=AsyncMock)
@patch('matrixcurator.modules.retrieval.services._get_insert_chunks')
async def test_embed_and_store_chunks_rate_limit_retry(mock_get_insert, mock_aembedding):
    from litellm.exceptions import RateLimitError
    from matrixcurator.modules.retrieval.services import _fetch_embeddings_with_retry
    import httpx
    
    mock_insert = MagicMock()
    mock_get_insert.return_value = mock_insert
    chunks = [{"id": "1", "document_id": "doc1", "content": "hello", "metadata": {}, "embedding": None}]
    
    mock_response = MagicMock()
    mock_response.data = [{"embedding": [0.1, 0.2, 0.3]}]
    
    # Raise RateLimitError on first call, succeed on second
    mock_aembedding.side_effect = [
        RateLimitError("Rate limit", llm_provider="openai", model="model"),
        mock_response
    ]
    
    # We must reset the retry statistics for isolated test
    _fetch_embeddings_with_retry.retry.statistics.clear()
    
    await embed_and_store_chunks(chunks)
    
    assert mock_aembedding.call_count == 2
    assert chunks[0]["embedding"] == [0.1, 0.2, 0.3]
    mock_insert.assert_called_once()

@patch('matrixcurator.modules.retrieval.repositories.supabase.get_client')
def test_insert_chunks_repository(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    chunks = [{"id": "1", "document_id": "doc1", "content": "hello", "metadata": {}, "embedding": [0.1]}]
    insert_chunks(chunks)
    
    mock_client.table.assert_called_once_with("document_chunks")
    mock_client.table().upsert.assert_called_once()

@patch('matrixcurator.modules.retrieval.repositories.supabase.get_client')
def test_query_similar_chunks_repository(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_result = MagicMock()
    mock_result.data = [{"id": "1", "document_id": "doc1", "content": "hello", "metadata": {}}]
    mock_client.rpc.return_value.execute.return_value = mock_result
    
    chunks = query_similar_chunks([0.1], match_threshold=0.5, match_count=2, document_id="doc1")
    
    mock_client.rpc.assert_called_once_with("match_documents", {
        "query_embedding": [0.1],
        "match_threshold": 0.5,
        "match_count": 2,
        "filter_document_id": "doc1"
    })
    
    assert len(chunks) == 1
    assert chunks[0]["content"] == "hello"


@pytest.mark.asyncio
@patch('matrixcurator.modules.retrieval.services.embed_and_store_chunks', new_callable=AsyncMock)
async def test_vectorize_document_parent_child_relevant(mock_embed):
    document_id = "doc_test"
    text_data = [
        {
            "parser": "docling",
            "pages": [
                {"page": 1, "content": "Page 1 Content"},
                {"page": 2, "content": "Page 2 Content"},
                {"page": 3, "content": "Page 3 Content"}
            ]
        }
    ]
    pages_subset = [1, 3]

    await vectorize_document(document_id, text_data, pages=pages_subset)

    assert mock_embed.call_count == 2
    
    # First call is for all pages
    all_chunks = mock_embed.call_args_list[0][0][0]
    assert len(all_chunks) > 0
    assert all(c["metadata"]["parser_name"] == "docling" for c in all_chunks)
    assert any(c["metadata"]["page"] == 2 for c in all_chunks)
    assert any("Page 2 Content" in c["metadata"]["page_content"] for c in all_chunks if c["metadata"]["page"] == 2)
    
    # Second call is for relevant pages only
    relevant_chunks = mock_embed.call_args_list[1][0][0]
    assert len(relevant_chunks) > 0
    assert all(c["metadata"]["parser_name"] == "docling_relevant" for c in relevant_chunks)
    assert all(c["metadata"]["page"] in [1, 3] for c in relevant_chunks)
    assert not any(c["metadata"]["page"] == 2 for c in relevant_chunks)


@pytest.mark.asyncio
@patch('matrixcurator.modules.retrieval.services._fetch_embeddings_with_retry', new_callable=AsyncMock)
@patch('matrixcurator.modules.retrieval.services._get_query_similar_chunks')
async def test_retrieve_context_parent_page(mock_get_query, mock_fetch):
    mock_query = MagicMock()
    mock_get_query.return_value = mock_query
    
    mock_response = MagicMock()
    mock_response.data = [{"embedding": [0.1, 0.2]}]
    mock_fetch.return_value = mock_response
    
    mock_query.return_value = [
        {
            "id": "chunk1",
            "content": "Short chunk 1",
            "metadata": {"page": 1, "page_content": "Full Page 1 Text"}
        },
        {
            "id": "chunk2",
            "content": "Short chunk 2",
            "metadata": {"page": 1, "page_content": "Full Page 1 Text"}
        },
        {
            "id": "chunk3",
            "content": "Short chunk 3",
            "metadata": {"page": 3, "page_content": "Full Page 3 Text"}
        }
    ]
    
    context = await retrieve_context("query", full_page_retrieval=True)
    
    # Deduplication and correct ordering by page number expected
    expected_context = "Full Page 1 Text\n\nFull Page 3 Text"
    assert context == expected_context

@pytest.mark.asyncio
@patch('matrixcurator.modules.retrieval.services._fetch_embeddings_with_retry', new_callable=AsyncMock)
@patch('matrixcurator.modules.retrieval.services._get_query_similar_chunks')
async def test_retrieve_context_with_metadata(mock_get_query, mock_fetch):
    mock_query = MagicMock()
    mock_get_query.return_value = mock_query
    
    mock_response = MagicMock()
    mock_response.data = [{"embedding": [0.1, 0.2]}]
    mock_fetch.return_value = mock_response
    
    mock_query.return_value = [
        {
            "id": "chunk1",
            "content": "Short chunk 1",
            "metadata": {"page": 1, "page_content": "Full Page 1 Text"}
        },
        {
            "id": "chunk2",
            "content": "Short chunk 2",
            "metadata": {"page": 1, "page_content": "Full Page 1 Text"}
        },
        {
            "id": "chunk3",
            "content": "Short chunk 3",
            "metadata": {"page": 3, "page_content": "Full Page 3 Text"}
        }
    ]
    
    context = await retrieve_context("query", full_page_retrieval=True, append_page_metadata=True)
    
    expected_context = "Full Page 1 Text\n\nFull Page 3 Text\n\n--- METADATA ---\nPages Retrieved: [1, 3]"
    assert context == expected_context

@pytest.mark.asyncio
@patch('matrixcurator.modules.retrieval.services._fetch_embeddings_with_retry', new_callable=AsyncMock)
@patch('matrixcurator.modules.retrieval.services._get_query_similar_chunks')
async def test_retrieve_context_chunk_with_metadata(mock_get_query, mock_fetch):
    mock_query = MagicMock()
    mock_get_query.return_value = mock_query
    
    mock_response = MagicMock()
    mock_response.data = [{"embedding": [0.1, 0.2]}]
    mock_fetch.return_value = mock_response
    
    mock_query.return_value = [
        {
            "id": "chunk1",
            "content": "Result 1",
            "metadata": {"page": 2}
        },
        {
            "id": "chunk2",
            "content": "Result 2",
            "metadata": {"page": 5}
        },
    ]
    
    context = await retrieve_context("query", full_page_retrieval=False, append_page_metadata=True)
    
    expected_context = "Result 1\n\nResult 2\n\n--- METADATA ---\nPages Retrieved: [2, 5]"
    assert context == expected_context
