import fitz  # PyMuPDF
import asyncio
from langchain_core.tools import tool
from matrixcurator.exceptions import DocumentParseError
from matrixcurator.utils.concurrency import AsyncRateLimiter, AsyncConcurrencyManager
from matrixcurator.config.main import settings

_manager = None

def get_manager() -> AsyncConcurrencyManager:
    global _manager
    if _manager is None:
        limiter = AsyncRateLimiter(settings=settings.pymupdf_rate_limit)
        _manager = AsyncConcurrencyManager(rate_limiter=limiter)
    return _manager


@tool
async def parse_with_pymupdf(
    file_content: bytes, filename: str, pages: list[int] | None = None
) -> str:
    """Use this tool to parse PDF files using PyMuPDF. It is fast and works well for standard text-heavy PDFs."""
    async with get_manager():

        def _parse():
            try:
                doc = fitz.open(stream=file_content, filetype="pdf")
                text = ""
                
                if pages is not None:
                    for p in pages:
                        if 1 <= p <= len(doc):
                            text += doc[p - 1].get_text()
                else:
                    for page in doc:
                        text += page.get_text()
                return text
            except Exception as e:
                raise DocumentParseError(f"Failed to parse PDF with PyMuPDF: {str(e)}") from e

        return await asyncio.to_thread(_parse)
