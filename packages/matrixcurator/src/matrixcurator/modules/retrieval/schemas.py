from typing import TypedDict, Optional, List


class ChunkMetadata(TypedDict, total=False):
    parser_name: str
    chunk_index: int
    total_chunks: int


class DocumentChunk(TypedDict):
    id: str
    document_id: str
    content: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]]
