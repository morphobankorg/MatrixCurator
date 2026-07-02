from pydantic import BaseModel
from typing import List, Dict, Any


class ParseResponse(BaseModel):
    text: str


class NexusGenerateRequest(BaseModel):
    original_nexus: str
    extracted_states: List[Dict[str, Any]]


class NexusGenerateResponse(BaseModel):
    updated_nexus: str
