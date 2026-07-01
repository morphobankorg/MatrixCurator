import io
import asyncio
import atexit
from langchain_core.tools import tool
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.document import InputFormat
from docling.datamodel.base_models import DocumentStream
from docling.pipeline.vlm_pipeline import VlmPipelineOptions
from matrixcurator.integrations.docling import McpVlmPipeline
from matrixcurator.exceptions import DocumentParseError
from typing import Optional
from matrixcurator.utils.concurrency import AsyncRateLimiter, AsyncConcurrencyManager
from matrixcurator.config.main import settings

_manager = None
_converter = None

def get_manager() -> AsyncConcurrencyManager:
    global _manager
    if _manager is None:
        limiter = AsyncRateLimiter(settings=settings.docling_rate_limit)
        _manager = AsyncConcurrencyManager(rate_limiter=limiter)
    return _manager

def get_converter() -> DocumentConverter:
    global _converter
    if _converter is None:
        pipeline_options = VlmPipelineOptions()
        pipeline_options.enable_remote_services = True

        _converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=McpVlmPipeline, pipeline_options=pipeline_options
                )
            }
        )
    return _converter


@tool
async def parse_with_docling(
    file_content: bytes, filename: str, pages: list[int] | None = None
) -> str:
    """Use this tool to parse complex documents (PDF, DOCX, HTML, etc.) using Docling. It is slower but highly accurate for complex layouts, tables, and reading order."""
    async with get_manager():
        def _parse():
            try:
                buf = io.BytesIO(file_content)
                stream = DocumentStream(name=filename, stream=buf)
                
                converter = get_converter()
                
                convert_kwargs = {}
                if pages:
                    convert_kwargs["page_range"] = (min(pages), max(pages))
                    
                result = converter.convert(stream, **convert_kwargs)
                return result.document.export_to_markdown()
            except Exception as e:
                raise DocumentParseError(
                    f"Failed to parse document with Docling: {str(e)}"
                ) from e

        return await asyncio.to_thread(_parse)


def _cleanup_converter():
    """Destroy the DocumentConverter singleton before Python starts tearing down modules."""
    global _converter
    if _converter is not None:
        _converter = None


atexit.register(_cleanup_converter)
