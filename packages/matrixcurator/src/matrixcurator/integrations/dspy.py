import os
from typing import List, Optional, Dict, Any
import dspy
from openinference.instrumentation.dspy import DSPyInstrumentor
from matrixcurator.modules.schemas import CharacterState
from lume import structlog
from matrixcurator.config.main import settings
from matrixcurator.integrations.mcp import (
    MCPSamplingError,
    mcp_session_var,
    sample_message,
)

_logger = structlog.get_logger(__name__)


class MCPAwareLM(dspy.LM):
    """
    Custom DSPy LM that intercepts calls for MCP sampling.
    Falls back to native dspy.LM (LiteLLM) if no MCP session is active or if sampling fails.
    """

    def forward(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        session = mcp_session_var.get()
        if session is not None:
            try:
                import asyncio

                msgs = messages or [{"role": "user", "content": prompt}]
                temperature = kwargs.get("temperature", self.kwargs.get("temperature"))
                max_tokens = kwargs.get("max_tokens", self.kwargs.get("max_tokens"))

                # Execute MCP sampling synchronously
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                if loop.is_running():
                    _logger.warning(
                        "Cannot run sync MCP sampling inside an active event loop. Falling back to native dspy.LM."
                    )
                    return super().forward(prompt=prompt, messages=messages, **kwargs)

                mcp_result = loop.run_until_complete(
                    sample_message(
                        session=session,
                        messages=msgs,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                )

                # Extract text content
                content = ""
                if hasattr(mcp_result, "content"):
                    for item in mcp_result.content:
                        if getattr(item, "type", "") == "text":
                            content += getattr(item, "text", "")

                # Format response into the dictionary structure DSPy expects
                return {
                    "choices": [
                        {
                            "message": {
                                "content": content,
                                "role": getattr(mcp_result, "role", "assistant"),
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                }

            except MCPSamplingError as e:
                _logger.warning(
                    f"MCP sampling failed, falling back to native dspy.LM: {e}"
                )
            except Exception as e:
                _logger.warning(
                    f"Unexpected error during MCP sampling, falling back to native dspy.LM: {e}"
                )

        # Fallback to native dspy.LM
        return super().forward(prompt=prompt, messages=messages, **kwargs)

    async def aforward(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        session = mcp_session_var.get()
        if session is not None:
            try:
                msgs = messages or [{"role": "user", "content": prompt}]
                temperature = kwargs.get("temperature", self.kwargs.get("temperature"))
                max_tokens = kwargs.get("max_tokens", self.kwargs.get("max_tokens"))

                # Execute MCP sampling
                mcp_result = await sample_message(
                    session=session,
                    messages=msgs,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # Extract text content
                content = ""
                if hasattr(mcp_result, "content"):
                    for item in mcp_result.content:
                        if getattr(item, "type", "") == "text":
                            content += getattr(item, "text", "")

                # Format response into the dictionary structure DSPy expects
                return {
                    "choices": [
                        {
                            "message": {
                                "content": content,
                                "role": getattr(mcp_result, "role", "assistant"),
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                }

            except MCPSamplingError as e:
                _logger.warning(
                    f"MCP sampling failed, falling back to native dspy.LM: {e}"
                )
            except Exception as e:
                _logger.warning(
                    f"Unexpected error during MCP sampling, falling back to native dspy.LM: {e}"
                )

        # Fallback to native dspy.LM
        return await super().aforward(prompt=prompt, messages=messages, **kwargs)


def configure_dspy(model_name: Optional[str] = None):
    """Configures DSPy to use LiteLLM and enables Langfuse tracing."""
    model = model_name or getattr(settings, "DEFAULT_MODEL", "gemini/gemini-1.5-pro")

    # Configure DSPy to use LiteLLM via our MCPAwareLM wrapper
    # We pass the API key from settings if available, otherwise litellm will look for env vars
    api_key = None
    if "gemini" in model.lower():
        api_key = getattr(settings, "GEMINI_API_KEY", None)
    elif "gpt" in model.lower():
        api_key = getattr(settings, "OPENAI_API_KEY", None)
    elif "claude" in model.lower():
        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)

    lm = MCPAwareLM(model, api_key=api_key)
    dspy.settings.configure(lm=lm)

    # Enable Langfuse tracing
    if not getattr(settings, "TELEMETRY_OPT_OUT", False):
        DSPyInstrumentor().instrument()

    _logger.info(f"Configured DSPy with model: {model}")


class CharacterExtraction(dspy.Signature):
    """Extract the character state information for a specific character index from the document text."""

    document_text: str = dspy.InputField(desc="The parsed text of the document")
    character_index: int = dspy.InputField(desc="The index of the character to extract")
    previous_errors: Optional[str] = dspy.InputField(
        desc="Errors from previous extraction attempts, if any"
    )

    character_name: str = dspy.OutputField(desc="The name of the extracted character")
    states: List[CharacterState] = dspy.OutputField(
        desc="A list of states for the character"
    )


class ExtractionEvaluation(dspy.Signature):
    """Evaluate the quality and accuracy of the extracted character data against the source document text."""

    document_text: str = dspy.InputField(desc="The parsed text of the document")
    extracted_data: Dict[str, Any] = dspy.InputField(
        desc="The extracted character data (name and states)"
    )

    score: int = dspy.OutputField(
        desc="A score from 1 to 10 indicating the quality of the extraction (10 is perfect)"
    )
    reasoning: str = dspy.OutputField(
        desc="Reasoning for the given score, highlighting any missing or incorrect information"
    )


class ExtractionModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(CharacterExtraction)

        # Try to load compiled weights if they exist
        weights_path = os.path.join(
            os.path.dirname(__file__), "..", "weights", "gemini-1.5-pro.json"
        )
        if os.path.exists(weights_path):
            try:
                self.load(weights_path)
                _logger.info(f"Loaded DSPy weights from {weights_path}")
            except Exception as e:
                _logger.warning(f"Failed to load DSPy weights: {e}")

    def forward(
        self,
        document_text: str,
        character_index: int,
        previous_errors: Optional[str] = None,
    ):
        return self.extract(
            document_text=document_text,
            character_index=character_index,
            previous_errors=previous_errors,
        )


class EvaluationModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.evaluate = dspy.ChainOfThought(ExtractionEvaluation)

        # Try to load compiled weights if they exist
        weights_path = os.path.join(
            os.path.dirname(__file__), "..", "weights", "gemini-1.5-pro.json"
        )
        if os.path.exists(weights_path):
            try:
                self.load(weights_path)
                _logger.info(f"Loaded DSPy weights from {weights_path}")
            except Exception as e:
                _logger.warning(f"Failed to load DSPy weights: {e}")

    def forward(self, document_text: str, extracted_data: Dict[str, Any]):
        return self.evaluate(document_text=document_text, extracted_data=extracted_data)
