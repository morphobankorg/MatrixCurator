from typing import Annotated, List, Dict, Any, Optional
from langgraph.graph import MessagesState
from dataclasses import dataclass
import operator


@dataclass
class ContextSchema:
    model_provider: str
    fallback_model: str
    user_id: str


class AgentState(MessagesState):
    character_index: int
    context: str
    extracted_data: Optional[Dict[str, Any]]
    evaluation_score: int
    attempts: int
    current_model: str
    errors: Annotated[List[str], operator.add]
