import asyncio
from langchain_core.tools import tool
from matrixcurator.exceptions import DocumentParseError
from matrixcurator.utils.concurrency import AsyncRateLimiter, AsyncConcurrencyManager
from matrixcurator.config.main import settings

_manager = None

def get_manager() -> AsyncConcurrencyManager:
    global _manager
    if _manager is None:
        limiter = AsyncRateLimiter(settings=settings.txt_rate_limit)
        _manager = AsyncConcurrencyManager(rate_limiter=limiter)
    return _manager


@tool
async def parse_with_txt(file_content: bytes, filename: str) -> str:
    """Use this tool to parse plain text (TXT) files."""
    async with get_manager():

        def _parse():
            try:
                return file_content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    return file_content.decode("latin-1")
                except Exception as e:
                    raise DocumentParseError(f"Failed to parse TXT: {str(e)}") from e
            except Exception as e:
                raise DocumentParseError(f"Failed to parse TXT: {str(e)}") from e

        return await asyncio.to_thread(_parse)
