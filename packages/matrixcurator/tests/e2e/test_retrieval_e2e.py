import pytest
import asyncio
from matrixcurator.modules.retrieval.services import vectorize_document, retrieve_context

try:
    from matrixcurator.modules.retrieval.repositories.sqlite import get_engine
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    HAS_SQLITE_VEC = True
except ImportError:
    HAS_SQLITE_VEC = False

@pytest.fixture(autouse=True)
def clean_db():
    if not HAS_SQLITE_VEC:
        yield
        return
    engine = get_engine()
    with Session(engine) as session:
        session.execute(text("DELETE FROM document_chunks_meta"))
        session.execute(text("DELETE FROM document_chunks_vec"))
        session.commit()
    yield
    with Session(engine) as session:
        session.execute(text("DELETE FROM document_chunks_meta"))
        session.execute(text("DELETE FROM document_chunks_vec"))
        session.commit()

@pytest.mark.asyncio
@pytest.mark.skipif(not HAS_SQLITE_VEC, reason="sqlite_vec is required")
async def test_e2e_parent_child_retrieval_workflow():
    document_id = "test_e2e_doc_1"
    
    # Mock json payload representing docling parse
    mock_docling_parses = [
        {
            "parser": "docling",
            "pages": [
                {"page": 1, "content": "This is the complete text of page one. It has multiple sentences to form a chunk."},
                {"page": 2, "content": "Here we have page two. The dinosaur fossils were found here."},
                {"page": 3, "content": "Page three concludes the report on paleontology."}
            ]
        }
    ]
    
    # Action 1 (Ingestion)
    # We want to ingest page 2 as relevant
    await vectorize_document(document_id, mock_docling_parses, pages=[2])
    
    engine = get_engine()
    with Session(engine) as session:
        count = session.execute(text("SELECT COUNT(*) FROM document_chunks_meta")).scalar()
        assert count > 0, "Chunks were not ingested into SQLite"
        
        # Check both docling and docling_relevant exist
        parsers = session.execute(text("SELECT DISTINCT parser_name FROM document_chunks_meta")).scalars().all()
        assert "docling" in parsers
        assert "docling_relevant" in parsers
        
    # Action 2 (Child Retrieval)
    query = "dinosaur fossils"
    context_child = await retrieve_context(query, document_id=document_id, parser_name="docling", full_page_retrieval=False)
    
    # Since the text is small, the child chunk might actually contain the whole sentence, but let's just assert it is returned
    assert "dinosaur fossils" in context_child
    
    # Action 3 (Parent Retrieval)
    context_parent = await retrieve_context(query, document_id=document_id, parser_name="docling", full_page_retrieval=True)
    
    # Should reconstruct the full page
    assert "Here we have page two. The dinosaur fossils were found here." in context_parent
    # Check deduplication
    assert context_parent.count("Here we have page two.") == 1
