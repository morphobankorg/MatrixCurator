from typing import Any
from langfuse import Langfuse
from lume import structlog

logger = structlog.get_logger(__name__)

def setup_evaluators(langfuse_repository: Any, client: Langfuse) -> None:
    """Sets up evaluation rules and configs via the injected Langfuse evaluation repository."""
    logger.info("Setting up Langfuse Evaluators and Score Config")

    categories = [
        {"label": "Complete Recall", "value": 1.0},
        {"label": "Recall Failure", "value": 0.0},
        {"label": "Partial Recall", "value": 0.5},
        {"label": "Semantic Corruption", "value": 0.25},
        {"label": "Low Context Precision", "value": 0.1},
    ]

    score_config_id = langfuse_repository.create_score_config(
        client,
        name="Semantic Recall",
        categories=categories,
        description="Score to measure semantic entailment using LLM-as-a-judge.",
    )

    evaluator_name = "Semantic Recall"
    prompt_text = (
        "You are an expert morphological analyst and precise data-extraction judge. Your task is to evaluate if the semantic morphological information from the `Expected Output` is accurately and fully represented within the raw `Extracted Output`.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. The `Expected Output` is JSON containing a morphological character's index, name, and its states.\n"
        "2. The `Extracted Output` is raw, unstructured text (either from a full page parse or a retrieved vector chunk). DO NOT penalize for lacking JSON structure.\n"
        "3. Ignore OCR artifacts, minor typos, or formatting errors in the `Extracted Output` as long as the semantic meaning remains identical.\n\n"
        "SCORING RUBRIC:\n"
        '- "Complete Recall": The extracted text contains the exact character name (or clear synonym) AND all of its defined states perfectly.\n'
        '- "Partial Recall": The extracted text contains the character name but is missing 1 or more states, OR the states are present but the character name is cut off/missing.\n'
        '- "Semantic Corruption": The text contains the character, but the states are mixed up with another character, or the text contradicts the expected output.\n'
        '- "Low Context Precision": The text is a massive dump of data where the character is barely mentioned, obscured by overwhelming noise, or the text retrieved is completely irrelevant to the morphological data.\n'
        '- "Recall Failure": The character and its states are completely absent from the text.\n\n'
        "Expected Output:\n"
        "{{expected_output}}\n\n"
        "Extracted Output:\n"
        "{{output}}\n\n"
        "Carefully analyze the semantic overlap and assign the most appropriate category based strictly on the rubric above.\n"
    )

    cat_labels = [c["label"] for c in categories]
    try:
        langfuse_repository.create_evaluator(
            client,
            evaluator_name=evaluator_name,
            prompt_text=prompt_text,
            score_config_id=score_config_id,
            categories=cat_labels,
        )

        langfuse_repository.bind_evaluation_rule(
            client,
            rule_name="Semantic Recall",
            evaluator_name=evaluator_name,
            dataset_name="character_states",
        )
    except Exception as e:
        logger.warning("Failed to setup evaluator: %s", str(e))
