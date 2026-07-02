import uuid
import asyncio
from typing import List, Optional, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from litellm import aembedding
from litellm.exceptions import RateLimitError, APIConnectionError, APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from matrixcurator.modules.retrieval.schemas import DocumentChunk
from matrixcurator.config.main import settings


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError)),
)
async def _fetch_embeddings_with_retry(texts: list[str]):
    return await aembedding(model=settings.embedding_model, input=texts)


def _get_insert_chunks():
    if settings.retrieval_backend == "sqlite":
        from matrixcurator.modules.retrieval.repositories.sqlite import (
            insert_chunks as _sqlite_insert,
        )

        return _sqlite_insert
    else:
        from matrixcurator.modules.retrieval.repositories.supabase import (
            insert_chunks as _supabase_insert,
        )

        return _supabase_insert


def _get_query_similar_chunks():
    if settings.retrieval_backend == "sqlite":
        from matrixcurator.modules.retrieval.repositories.sqlite import (
            query_similar_chunks as _sqlite_query,
        )

        return _sqlite_query
    else:
        from matrixcurator.modules.retrieval.repositories.supabase import (
            query_similar_chunks as _supabase_query,
        )

        return _supabase_query


def chunk_text(
    text: str,
    document_id: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    parser_name: Optional[str] = None,
    page: Optional[int] = None,
    page_content: Optional[str] = None,
) -> List[DocumentChunk]:
    """
    Splits text into chunks using Langchain's RecursiveCharacterTextSplitter.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )

    texts = text_splitter.split_text(text)

    chunks = []
    for i, chunk_text in enumerate(texts):
        meta = {"chunk_index": i, "total_chunks": len(texts)}
        if parser_name:
            meta["parser_name"] = parser_name
        if page is not None:
            meta["page"] = page
        if page_content is not None:
            meta["page_content"] = page_content

        chunks.append(
            {
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "content": chunk_text,
                "metadata": meta,
                "embedding": None,
            }
        )

    return chunks


async def embed_and_store_chunks(chunks: List[DocumentChunk]) -> None:
    """
    Gets embeddings for a list of chunks and stores them in the active backend in batches.
    """
    if not chunks:
        return

    batch_size = 100
    insert_fn = _get_insert_chunks()

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [chunk["content"] for chunk in batch]

        # We use retry-wrapped aembedding for async liteLLM embedding
        response = await _fetch_embeddings_with_retry(texts)

        # response['data'] contains the embeddings in the same order
        for j, data in enumerate(response.data):
            batch[j]["embedding"] = data["embedding"]

        insert_fn(batch)

        # Add a brief sleep between batches to help respect API rate limits
        if i + batch_size < len(chunks):
            await asyncio.sleep(0.5)


async def retrieve_context(
    query: str,
    match_count: int = 5,
    document_id: Optional[str] = None,
    parser_name: Optional[str] = None,
    full_page_retrieval: bool = False,
    append_page_metadata: bool = False,
) -> str:
    """
    Embeds the query, searches the active backend, and returns concatenated context.
    """
    response = await _fetch_embeddings_with_retry([query])
    query_embedding = response.data[0]["embedding"]

    query_fn = _get_query_similar_chunks()

    kwargs = {
        "embedding": query_embedding,
        "match_count": match_count,
        "document_id": document_id,
    }

    if parser_name and settings.retrieval_backend == "sqlite":
        kwargs["parser_name"] = parser_name
    elif parser_name:
        # Supabase
        kwargs["parser_name"] = parser_name

    similar_chunks = query_fn(**kwargs)

    if not similar_chunks:
        return ""

    if full_page_retrieval:
        # Deduplicate by page number and return full page content
        pages = {}
        for chunk in similar_chunks:
            meta = chunk.get("metadata", {})
            page = meta.get("page")
            content = meta.get("page_content")

            # If parent page info is missing, fallback to chunk content
            if page is None or content is None:
                pages[chunk["id"]] = chunk["content"]
            else:
                pages[page] = content

        # Sort by keys (if possible) to ensure consistent order
        sorted_keys = sorted(list(pages.keys()), key=lambda x: (isinstance(x, str), x))
        
        pages_retrieved = [k for k in sorted_keys if isinstance(k, int)]
        context = "\n\n".join([pages[k] for k in sorted_keys])
    else:
        # Concatenate the contents of the retrieved chunks
        retrieved_page_numbers = set()
        for chunk in similar_chunks:
            page = chunk.get("metadata", {}).get("page")
            if page is not None and isinstance(page, int):
                retrieved_page_numbers.add(page)
        pages_retrieved = sorted(list(retrieved_page_numbers))
        
        context = "\n\n".join([chunk["content"] for chunk in similar_chunks])

    if append_page_metadata:
        pages_report = f"\n\n--- METADATA ---\nPages Retrieved: {pages_retrieved}"
        context += pages_report

    return context


async def vectorize_document(
    document_id: str, text: List[Dict[str, Any]], pages: Optional[List[int]] = None
) -> None:
    """
    Parses a document's texts and ingests them into the vector store.
    Supports targeted page-level subsetting and adds Parent Page metadata for semantic recall.
    """
    for parse_data in text:
        parser = parse_data.get("parser")
        pages_data = parse_data.get("pages", [])
        if not isinstance(pages_data, list):
            continue

        all_chunks = []
        for page_obj in pages_data:
            if not isinstance(page_obj, dict):
                continue

            page_num = page_obj.get("page")
            content = page_obj.get("content")

            if not content:
                continue

            page_chunks = chunk_text(
                content,
                document_id,
                parser_name=parser,
                page=page_num,
                page_content=content,
            )
            all_chunks.extend(page_chunks)

        await embed_and_store_chunks(all_chunks)

        if parser == "docling" and pages and isinstance(pages, list):
            import structlog
            logger = structlog.get_logger(__name__)
            logger.info("Ingesting docling_relevant subset", document_id=document_id, target_pages=pages)
            
            relevant_chunks = []
            for page_obj in pages_data:
                if not isinstance(page_obj, dict):
                    continue

                page_num = page_obj.get("page")
                if page_num not in pages:
                    continue

                content = page_obj.get("content")
                if not content:
                    continue

                page_chunks = chunk_text(
                    content,
                    document_id,
                    parser_name="docling_relevant",
                    page=page_num,
                    page_content=content,
                )
                relevant_chunks.extend(page_chunks)

            await embed_and_store_chunks(relevant_chunks)
