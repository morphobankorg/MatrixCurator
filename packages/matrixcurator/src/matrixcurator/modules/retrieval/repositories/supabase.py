from typing import List
from matrixcurator.integrations.supabase import get_client
from matrixcurator.modules.retrieval.schemas import DocumentChunk


def insert_chunks(chunks: List[DocumentChunk]) -> None:
    """
    Inserts document chunks into the Supabase document_chunks table.
    """
    client = get_client()
    data_to_insert = []
    for chunk in chunks:
        data_to_insert.append(
            {
                "id": chunk.get("id"),
                "document_id": chunk.get("document_id"),
                "content": chunk.get("content"),
                "metadata": chunk.get("metadata", {}),
                "embedding": chunk.get("embedding"),
            }
        )

    if data_to_insert:
        client.table("document_chunks").upsert(data_to_insert).execute()


def query_similar_chunks(
    embedding: List[float],
    match_threshold: float = 0.7,
    match_count: int = 5,
    document_id: str = None,
    parser_name: str = None,
) -> List[DocumentChunk]:
    """
    Queries similar chunks using the pgvector match_documents RPC.
    """
    client = get_client()

    params = {
        "query_embedding": embedding,
        "match_threshold": match_threshold,
        "match_count": match_count,
    }

    if document_id:
        params["filter_document_id"] = document_id

    if parser_name:
        params["filter_parser_name"] = parser_name

    result = client.rpc("match_documents", params).execute()

    chunks = []
    for row in result.data:
        chunks.append(
            {
                "id": row.get("id"),
                "document_id": row.get("document_id"),
                "content": row.get("content"),
                "metadata": row.get("metadata", {}),
                "embedding": None,  # We don't necessarily need the embedding back
            }
        )

    return chunks
