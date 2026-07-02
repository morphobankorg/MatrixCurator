# src/modules/agent/nodes.py
import json
from typing import Any, Dict
from litellm import completion
from langgraph.types import Command
from matrixcurator.modules.state import AgentState
from matrixcurator.exceptions import ContextLengthExceededError
from pydantic import BaseModel, Field


class CharacterStateOutput(BaseModel):
    character_index: int = Field(description="The index of the character")
    character_name: str = Field(description="The name of the character")
    states: Dict[str, str] = Field(
        description="A dictionary mapping state numbers (as strings) to state descriptions"
    )


def llm_error_handler(state: AgentState, error: Exception) -> Command:
    """Fallback error handler for LLM nodes."""
    print(f"Error in LLM node: {error}")
    return Command(
        update={
            "current_model": "gemini/gemini-1.5-flash",  # Fallback model
            "errors": [f"LLM Error: {str(error)}"],
        },
        goto="extractor_agent",
    )


def extractor_agent(state: AgentState) -> Dict[str, Any]:
    """Extracts character data using LLM."""
    context = state.get("context", "")
    char_idx = state.get("character_index")
    model = state.get("current_model", "gemini/gemini-1.5-pro")

    if not context:
        return {"extracted_data": None, "errors": ["Empty context provided."]}

    if len(context) > 1000000:  # Arbitrary large limit for safety
        raise ContextLengthExceededError("Context too large for extraction.")

    prompt = f"""
    Extract the character state information for character index {char_idx} from the following text.
    Return the data in a structured format.
    
    Text:
    {context[:50000]} # Truncate for safety in this example
    """

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=CharacterStateOutput,
            max_retries=2,
        )

        # Parse the structured output
        content = response.choices[0].message.content
        if isinstance(content, str):
            data = json.loads(content)
        else:
            data = content  # If it's already a dict/pydantic model

        if isinstance(data, BaseModel):
            data = data.model_dump()

        return {"extracted_data": data, "attempts": state.get("attempts", 0) + 1}
    except Exception as e:
        raise e  # Let the retry policy or error handler catch it


def evaluator_agent(state: AgentState) -> Dict[str, Any]:
    """Evaluates the extracted data."""
    data = state.get("extracted_data")
    if not data:
        return {"evaluation_score": 0}

    # Simple heuristic evaluation for now
    score = 10
    if not data.get("character_name"):
        score -= 5
    if not data.get("states"):
        score -= 5

    return {"evaluation_score": score}


def supervisor_node(state: AgentState) -> Command:
    """Routes between agents based on state."""
    data = state.get("extracted_data")
    score = state.get("evaluation_score", 0)
    attempts = state.get("attempts", 0)

    MAX_ATTEMPTS = 3

    if not data and attempts < MAX_ATTEMPTS:
        return Command(goto="extractor_agent")

    if data and score < 8 and attempts < MAX_ATTEMPTS:
        return Command(goto="extractor_agent")

    return Command(goto="__end__")
