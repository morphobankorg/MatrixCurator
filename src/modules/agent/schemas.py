from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ExtractRequest(BaseModel):
    context: str
    character_indices: List[int]
    model_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    user_id: Optional[str] = "default_user"

class ExtractResponse(BaseModel):
    extracted_states: List[Dict[str, Any]]
    errors: List[str]
