from typing import List, Optional
from pydantic import BaseModel
from matrixcurator.integrations.litellm import acompletion
from matrixcurator.config.main import settings


# Output schemas for Structured Data Extraction
class StateModel(BaseModel):
    index: int
    name: str


class CharacterModel(BaseModel):
    index: int
    name: str


class CharacterStateModel(BaseModel):
    character: CharacterModel
    states: List[StateModel]


class ExtractionResult(BaseModel):
    character_states: List[CharacterStateModel]


async def extract_characters_and_states(
    text: str, indices: Optional[List[int]] = None
) -> ExtractionResult:
    """
    Extracts character and state information from text using normal prompting (PROMPT_ENGINEERING strategy).
    """
    model = settings.get_model_for_tier(1)

    prompt = (
        "Extract the characters and their associated states from the following text."
    )
    if indices:
        prompt += f" Pay special attention to character indices: {indices}."

    prompt += "\n\nText:\n" + text

    messages = [
        {
            "role": "system",
            "content": "You are a morphological matrix extraction tool. Extract the characters and their states accurately.",
        },
        {"role": "user", "content": prompt},
    ]

    # We use response_format to enforce Pydantic structured output
    response = await acompletion(
        model=model,
        messages=messages,
        response_format=ExtractionResult,
    )

    # The parsed object is usually in response.choices[0].message.content if it's string
    # But with response_format, some providers support tool calling or strict JSON parsing.
    # Litellm supports Pydantic models directly for providers like OpenAI via instructor or native.
    content = response.choices[0].message.content
    if isinstance(content, str):
        return ExtractionResult.model_validate_json(content)

    return content  # If it returned a model directly
