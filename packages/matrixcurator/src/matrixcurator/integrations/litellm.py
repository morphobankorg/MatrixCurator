import asyncio
import logging
import time
import uuid
from typing import Any

import litellm
from litellm import Choices, Message, ModelResponse, Usage

from matrixcurator.integrations.mcp import (
    MCPSamplingError,
    mcp_session_var,
    sample_message,
)

logger = logging.getLogger(__name__)


def _format_mcp_to_litellm(mcp_result: Any, model: str) -> ModelResponse:
    """Convert an MCP CreateMessageResult to a LiteLLM ModelResponse."""
    # Extract text content from MCP result
    content = ""
    if hasattr(mcp_result, "content"):
        for item in mcp_result.content:
            if getattr(item, "type", "") == "text":
                content += getattr(item, "text", "")

    # Create LiteLLM response structure
    message = Message(content=content, role=getattr(mcp_result, "role", "assistant"))
    choice = Choices(finish_reason="stop", index=0, message=message)

    # Create usage if available, otherwise mock it
    usage = Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    return ModelResponse(
        id=f"chatcmpl-{uuid.uuid4()}",
        choices=[choice],
        created=int(time.time()),
        model=getattr(mcp_result, "model", model),
        object="chat.completion",
        usage=usage,
    )


async def acompletion(*args, **kwargs) -> ModelResponse:
    """
    Universal async completion wrapper that intercepts calls for MCP sampling.
    Falls back to litellm.acompletion if no MCP session is active or if sampling fails.
    """
    session = mcp_session_var.get()
    if session is not None:
        try:
            messages = kwargs.get("messages", [])
            if not messages and len(args) > 1:
                messages = args[1]

            model = kwargs.get("model", "unknown")
            if not model and len(args) > 0:
                model = args[0]

            temperature = kwargs.get("temperature")
            max_tokens = kwargs.get("max_tokens")

            # Execute MCP sampling
            mcp_result = await sample_message(
                session=session,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Format and return
            return _format_mcp_to_litellm(mcp_result, model)

        except MCPSamplingError as e:
            logger.warning(
                f"MCP sampling failed, falling back to native litellm.acompletion: {e}"
            )
        except Exception as e:
            logger.warning(
                f"Unexpected error during MCP sampling, falling back to native litellm.acompletion: {e}"
            )

    # Fallback to native LiteLLM
    return await litellm.acompletion(*args, **kwargs)


def completion(*args, **kwargs) -> ModelResponse:
    """
    Universal sync completion wrapper that intercepts calls for MCP sampling.
    Falls back to litellm.completion if no MCP session is active or if sampling fails.
    """
    session = mcp_session_var.get()
    if session is not None:
        try:
            messages = kwargs.get("messages", [])
            if not messages and len(args) > 1:
                messages = args[1]

            model = kwargs.get("model", "unknown")
            if not model and len(args) > 0:
                model = args[0]

            temperature = kwargs.get("temperature")
            max_tokens = kwargs.get("max_tokens")

            # Execute MCP sampling synchronously
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                # If we're already in an event loop, we can't use run_until_complete
                # We should probably just fall back to native litellm in this edge case
                logger.warning(
                    "Cannot run sync MCP sampling inside an active event loop. Falling back to native litellm.completion."
                )
                return litellm.completion(*args, **kwargs)

            mcp_result = loop.run_until_complete(
                sample_message(
                    session=session,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )

            # Format and return
            return _format_mcp_to_litellm(mcp_result, model)

        except MCPSamplingError as e:
            logger.warning(
                f"MCP sampling failed, falling back to native litellm.completion: {e}"
            )
        except Exception as e:
            logger.warning(
                f"Unexpected error during MCP sampling, falling back to native litellm.completion: {e}"
            )

    # Fallback to native LiteLLM
    return litellm.completion(*args, **kwargs)
