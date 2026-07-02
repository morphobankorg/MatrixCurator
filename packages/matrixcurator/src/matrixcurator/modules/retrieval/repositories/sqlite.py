from typing import List, Optional
import json
from sqlalchemy import create_engine, text, Column, String, Text
from sqlalchemy.orm import declarative_base, Session
import sqlite_vec

from matrixcurator.config.main import settings
from matrixcurator.modules.retrieval.schemas import DocumentChunk
from litellm import embedding

Base = declarative_base()


def _get_embedding_dimension() -> int:
    """Dynamically determine the embedding dimension of the configured model."""
    try:
        response = embedding(model=settings.embedding_model, input=["test"])
        return len(response.data[0]["embedding"])
    except Exception:
        # Fallback to 768 if the API call fails or is not configured
        return 768


class DocumentChunkMeta(Base):
    __tablename__ = "document_chunks_meta"

    id = Column(String, primary_key=True)
    document_id = Column(String, index=True)
    parser_name = Column(String, index=True, nullable=True)
    content = Column(Text)
    metadata_json = Column(Text)


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        db_path = settings.sqlite_db_path
        # sqlite:///{db_path}
        _engine = create_engine(f"sqlite:///{db_path}")

        # Load sqlite-vec extension
        with _engine.connect() as conn:
            # Need raw dbapi connection to enable extension loading
            dbapi_conn = conn.connection.dbapi_connection
            dbapi_conn.enable_load_extension(True)
            sqlite_vec.load(dbapi_conn)
            dbapi_conn.enable_load_extension(False)

        Base.metadata.create_all(_engine)

        with _engine.connect() as conn:
            # Check if the virtual table already exists
            result = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='document_chunks_vec'"
                )
            ).fetchone()
            if not result:
                # Dynamically fetch the required dimension for the current model
                dim = _get_embedding_dimension()
                conn.execute(
                    text(f"""
                    CREATE VIRTUAL TABLE document_chunks_vec USING vec0(
                        id TEXT PRIMARY KEY,
                        embedding FLOAT[{dim}]
                    )
                """)
                )
    return _engine


def insert_chunks(chunks: List[DocumentChunk]) -> None:
    if not chunks:
        return

    engine = get_engine()
    with Session(engine) as session:
        for chunk in chunks:
            # Insert meta
            parser_name = chunk.get("metadata", {}).get("parser_name")
            meta = DocumentChunkMeta(
                id=chunk["id"],
                document_id=chunk["document_id"],
                parser_name=parser_name,
                content=chunk["content"],
                metadata_json=json.dumps(chunk.get("metadata", {})),
            )
            session.merge(meta)

            # Insert vector
            embedding = json.dumps(chunk["embedding"])  # vec0 accepts JSON arrays
            session.execute(
                text("""
                INSERT OR REPLACE INTO document_chunks_vec (id, embedding)
                VALUES (:id, :emb)
            """),
                {"id": chunk["id"], "emb": embedding},
            )

        session.commit()


def delete_chunks_by_document(document_ids: List[str]) -> None:
    if not document_ids:
        return

    engine = get_engine()
    with Session(engine) as session:
        for chunk_id in range(0, len(document_ids), 100):
            batch = document_ids[chunk_id : chunk_id + 100]
            
            # Use tuple parameter expansion for the IN clause
            bind_params = {f"doc_{i}": doc_id for i, doc_id in enumerate(batch)}
            in_clause = ", ".join([f":{k}" for k in bind_params.keys()])
            
            # Delete vectors first
            session.execute(
                text(f"""
                DELETE FROM document_chunks_vec 
                WHERE id IN (
                    SELECT id FROM document_chunks_meta 
                    WHERE document_id IN ({in_clause})
                )
                """),
                bind_params
            )
            
            # Delete meta
            session.execute(
                text(f"DELETE FROM document_chunks_meta WHERE document_id IN ({in_clause})"),
                bind_params
            )
            
        session.commit()


def query_similar_chunks(
    embedding: List[float],
    match_threshold: float = 0.7,
    match_count: int = 5,
    document_id: Optional[str] = None,
    parser_name: Optional[str] = None,
) -> List[DocumentChunk]:
    engine = get_engine()

    with Session(engine) as session:
        emb_json = json.dumps(embedding)

        # We construct the WHERE clause dynamically based on filters
        query_sql = """
            SELECT m.id, m.document_id, m.content, m.metadata_json
            FROM document_chunks_vec v
            JOIN document_chunks_meta m ON v.id = m.id
            WHERE vec_distance_cosine(v.embedding, :query_emb) <= :threshold
        """
        params = {
            "query_emb": emb_json,
            "threshold": 1.0
            - match_threshold,  # Cosine distance = 1 - cosine similarity
            "limit": match_count,
        }

        if document_id:
            query_sql += " AND m.document_id = :doc_id"
            params["doc_id"] = document_id

        if parser_name:
            query_sql += " AND m.parser_name = :parser"
            params["parser"] = parser_name

        query_sql += (
            " ORDER BY vec_distance_cosine(v.embedding, :query_emb) LIMIT :limit"
        )

        result = session.execute(text(query_sql), params)

        chunks = []
        for row in result:
            chunks.append(
                {
                    "id": row.id,
                    "document_id": row.document_id,
                    "content": row.content,
                    "metadata": json.loads(row.metadata_json)
                    if row.metadata_json
                    else {},
                    "embedding": None,
                }
            )

        return chunks
