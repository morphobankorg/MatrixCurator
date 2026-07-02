import pytest
from unittest.mock import patch

from matrixcurator.config.main import settings

@pytest.fixture
def temp_sqlite_db(tmp_path):
    db_path = tmp_path / "test.sqlite"
    # Overwrite setting for the test
    original_path = settings.sqlite_db_path
    settings.sqlite_db_path = str(db_path)
    
    # We must clear the cached engine in the module
    import matrixcurator.modules.retrieval.repositories.sqlite as sqlite_repository
    sqlite_repository._engine = None
    
    with patch("matrixcurator.modules.retrieval.repositories.sqlite._get_embedding_dimension", return_value=3072):
        yield
    
    settings.sqlite_db_path = original_path
    sqlite_repository._engine = None

def test_insert_and_query_sqlite_vector(temp_sqlite_db):
    from matrixcurator.modules.retrieval.repositories.sqlite import insert_chunks, query_similar_chunks
    
    # Needs to ensure vector schema can handle dummy floats
    # Let's insert two chunks with different parsers
    dummy_embedding = [0.1] * 3072
    chunks = [
        {
            "id": "chunk_1",
            "document_id": "doc_1",
            "content": "This is docling content",
            "metadata": {"parser_name": "docling"},
            "embedding": dummy_embedding
        },
        {
            "id": "chunk_2",
            "document_id": "doc_1",
            "content": "This is pymupdf content",
            "metadata": {"parser_name": "pymupdf"},
            "embedding": dummy_embedding
        }
    ]
    
    insert_chunks(chunks)
    
    # Query without parser
    results = query_similar_chunks(embedding=dummy_embedding, match_threshold=0.5, match_count=5)
    assert len(results) == 2
    
    # Query with parser
    results_docling = query_similar_chunks(embedding=dummy_embedding, match_threshold=0.5, match_count=5, parser_name="docling")
    assert len(results_docling) == 1
    assert results_docling[0]["content"] == "This is docling content"

def test_delete_chunks_by_document(temp_sqlite_db):
    from matrixcurator.modules.retrieval.repositories.sqlite import insert_chunks, query_similar_chunks, delete_chunks_by_document
    
    dummy_embedding = [0.1] * 3072
    chunks = [
        {
            "id": "chunk_1",
            "document_id": "doc_1",
            "content": "doc 1 chunk",
            "metadata": {"parser_name": "docling"},
            "embedding": dummy_embedding
        },
        {
            "id": "chunk_2",
            "document_id": "doc_2",
            "content": "doc 2 chunk",
            "metadata": {"parser_name": "docling"},
            "embedding": dummy_embedding
        }
    ]
    
    insert_chunks(chunks)
    
    results_before = query_similar_chunks(embedding=dummy_embedding, match_threshold=0.5, match_count=5)
    assert len(results_before) == 2
    
    delete_chunks_by_document(["doc_1"])
    
    results_after = query_similar_chunks(embedding=dummy_embedding, match_threshold=0.5, match_count=5)
    assert len(results_after) == 1
    assert results_after[0]["document_id"] == "doc_2"
