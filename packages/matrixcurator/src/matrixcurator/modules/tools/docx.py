import io
import asyncio
from langchain_core.tools import tool
from matrixcurator.exceptions import DocumentParseError
from matrixcurator.utils.concurrency import AsyncRateLimiter, AsyncConcurrencyManager
from matrixcurator.config.main import settings

# Absolute import to avoid circular dependency with the file name
import docx as python_docx

_manager = None

def get_manager() -> AsyncConcurrencyManager:
    global _manager
    if _manager is None:
        limiter = AsyncRateLimiter(settings=settings.docx_rate_limit)
        _manager = AsyncConcurrencyManager(rate_limiter=limiter)
    return _manager


@tool
async def parse_with_docx(file_content: bytes, filename: str) -> str:
    """Use this tool to parse DOCX (Microsoft Word) files."""
    async with get_manager():
        def _parse():
            try:
                doc = python_docx.Document(io.BytesIO(file_content))
                text = []
                for para in doc.paragraphs:
                    text.append(para.text)
                return "\n".join(text)
            except Exception as e:
                raise DocumentParseError(f"Failed to parse DOCX: {str(e)}") from e

        return await asyncio.to_thread(_parse)
