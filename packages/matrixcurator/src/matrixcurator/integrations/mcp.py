import contextvars
import logging
from typing import Any, Dict, List, Optional

from mcp.types import CreateMessageResult, ModelPreferences

logger = logging.getLogger(__name__)

# Context variable to store the active MCP session (client)
mcp_session_var: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar(
    "mcp_session", default=None
)

class MCPSamplingError(Exception):
    """Raised when MCP sampling fails."""
    pass

async def sample_message(
    session: Any,
    messages: List[Dict[str, Any]],
    model_preferences: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    include_context: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> CreateMessageResult:
    """
    Request a completion from the host LLM via MCP sampling.
    
    Args:
        session: The active MCP session (client).
        messages: The messages to send.
        model_preferences: Optional model preferences.
        system_prompt: Optional system prompt.
        include_context: Optional context inclusion strategy.
        temperature: Optional temperature.
        max_tokens: Optional max tokens.
        
    Returns:
        The CreateMessageResult from the MCP client.
        
    Raises:
        MCPSamplingError: If the sampling request fails.
    """
    try:
        # Convert standard messages to MCP messages
        mcp_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Handle complex content (e.g., images)
            if isinstance(content, list):
                mcp_content = []
                for item in content:
                    if item.get("type") == "text":
                        mcp_content.append({"type": "text", "text": item.get("text", "")})
                    elif item.get("type") == "image_url":
                        # MCP expects image data in base64
                        image_url = item.get("image_url", {}).get("url", "")
                        if image_url.startswith("data:image"):
                            # Extract base64 data
                            parts = image_url.split(",", 1)
                            if len(parts) == 2:
                                mime_type = parts[0].split(";")[0].split(":")[1]
                                data = parts[1]
                                mcp_content.append({
                                    "type": "image",
                                    "data": data,
                                    "mimeType": mime_type
                                })
                mcp_messages.append({"role": role, "content": mcp_content})
            else:
                mcp_messages.append({
                    "role": role,
                    "content": {"type": "text", "text": str(content)}
                })
                
        # Prepare model preferences if provided
        prefs = None
        if model_preferences:
            prefs = ModelPreferences(**model_preferences)
            
        # Call the MCP client
        result = await session.create_message(
            messages=mcp_messages,
            model_preferences=prefs,
            system_prompt=system_prompt,
            include_context=include_context,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return result
    except Exception as e:
        logger.warning(f"MCP sampling failed: {e}")
        raise MCPSamplingError(f"Failed to sample message via MCP: {e}") from e

