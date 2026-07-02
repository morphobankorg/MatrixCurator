from pydantic import BaseModel
from typing import TypedDict, List, Dict, Any, Optional


class ExtractRequest(BaseModel):
    context: str
    character_indices: List[int]
    model_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    user_id: Optional[str] = "default_user"


class ExtractResponse(BaseModel):
    extracted_states: List[Dict[str, Any]]
    errors: List[str]


# Domain-driven schemas for Agent State (aligns with Parquet structures)
class Character(TypedDict):
    index: int
    name: str


class State(TypedDict):
    index: int
    name: str


class CharacterState(TypedDict):
    character: Character
    states: List[State]
    score: Optional[int]
    evaluator_reasoning: Optional[str]
    status: str  # "pending", "extracting", "evaluating", "human_review", "approved", "failed"


class Document(TypedDict):
    file_bytes: Optional[bytes]
    filename: Optional[str]
    mime_type: Optional[str]
    inferred_pages: Optional[List[int]]  # The "section" inferred for the splicer
    total_characters: Optional[int]  # Guessed total number of characters
    discovery_confidence: Optional[float]  # Confidence of the inference
    text: List[
        Dict[str, str]
    ]  # Maps parser name to spliced text e.g., [{"parser": "docling", "text": "..."}]
    status: str  # "pending", "discovering", "parsing", "parsed", "error"
