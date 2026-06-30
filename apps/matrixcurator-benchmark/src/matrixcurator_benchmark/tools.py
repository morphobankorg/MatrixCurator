# src/benchmark/benchmark_tools.py
import json
import asyncio
import pandas as pd
from typing import Any, Protocol
from lume import structlog

from matrixcurator_benchmark.config.main import settings

from matrixcurator.modules.tools.docling import parse_with_docling
from matrixcurator.modules.tools.pymupdf import parse_with_pymupdf
from matrixcurator.modules.tools.docx import parse_with_docx
from matrixcurator.modules.tools.txt import parse_with_txt

from matrixcurator_benchmark.core.decorators import benchmark, fixture
from matrixcurator_benchmark.core.exceptions import FailBenchmark, SkipBenchmark

logger = structlog.get_logger(__name__)


class ToolParser(Protocol):
    def invoke(self, args: dict[str, Any]) -> str: ...


from typing import Any, Protocol, List, Dict

@fixture(scope="session")
def docs_dict(fixture_parsed_cache: List[Dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for row in fixture_parsed_cache:
        key = row.get("id") or row.get("document_id")
        if key is not None:
            result[str(key)] = row
    return result


def skip_non_pdf(kwargs: dict[str, Any]) -> bool:
    doc_id = kwargs["dataset_item"].input.get("document_id")
    doc_row = kwargs["docs_dict"].get(doc_id, {})
    return doc_row.get("mime_type", "") != "application/pdf"


def skip_non_docx(kwargs: dict[str, Any]) -> bool:
    doc_id = kwargs["dataset_item"].input.get("document_id")
    doc_row = kwargs["docs_dict"].get(doc_id, {})
    return doc_row.get("mime_type", "") != "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def skip_non_txt(kwargs: dict[str, Any]) -> bool:
    doc_id = kwargs["dataset_item"].input.get("document_id")
    doc_row = kwargs["docs_dict"].get(doc_id, {})
    return doc_row.get("mime_type", "") != "text/plain"


async def _execute_tool_benchmark(
    dataset_item: Any,
    tool_name: str,
    parser: ToolParser,
    default_ext: str,
    requires_pages: bool,
    docs_dict: dict[str, Any],
    langfuse_trace: Any,
) -> None:
    input_data = dataset_item.input
    document_id = input_data.get("document_id")
    pages = input_data.get("pages")
    if pages is None:
        pages = [1]
    elif hasattr(pages, "__len__") and len(pages) == 0:
        pages = [1]

    doc_row = docs_dict.get(document_id)
    if not doc_row:
        raise SkipBenchmark(f"Document {document_id} not found in parquet data.")

    # Retrieve pre-parsed text from the DataFrame cache directly
    pre_parsed_text = doc_row.get("text")

    is_missing = False
    if pre_parsed_text is None:
        is_missing = True
    elif isinstance(pre_parsed_text, (list, dict, tuple)):
        is_missing = len(pre_parsed_text) == 0
    elif isinstance(pre_parsed_text, str):
        is_missing = not pre_parsed_text.strip()
    elif pd.isna(pre_parsed_text):
        is_missing = True

    if is_missing:
        raise FailBenchmark(f"{tool_name} parsing failed: missing text in parquet cache for doc {document_id}")

    try:
        if isinstance(pre_parsed_text, str):
            parses = json.loads(pre_parsed_text)
        elif isinstance(pre_parsed_text, (list, tuple)):
            parses = list(pre_parsed_text)
        else:
            raise FailBenchmark(f"{tool_name} parsing failed: Unsupported type {type(pre_parsed_text)} for parsed text")
            
        if not isinstance(parses, list):
            if parses is None:
                parses = []
            else:
                parses = [parses]
                
        parser_name = tool_name.lower()
        for parse_obj in parses:
            if parse_obj.get("parser") == parser_name:
                parsed_pages = parse_obj.get("pages") or []
                
                if requires_pages:
                    content_list = []
                    missing_pages = False
                    for p in pages:
                        page_match = next(
                            (pg for pg in parsed_pages if isinstance(pg, dict) and str(pg.get("page")) == str(p)), None
                        )
                        if page_match:
                            content_list.append(page_match.get("content", ""))
                        else:
                            missing_pages = True
                            break

                    if not missing_pages and content_list:
                        result = "\n\n".join(content_list)
                        langfuse_trace(result)
                        return
                else:
                    sorted_pages = sorted(
                        [pg for pg in parsed_pages if isinstance(pg, dict)], key=lambda x: x.get("page", 0)
                    )
                    content_list = [pg.get("content", "") for pg in sorted_pages]
                    if content_list:
                        result = "\n\n".join(content_list)
                        langfuse_trace(result)
                        return
                        
        raise FailBenchmark(f"{tool_name} parsing failed: Could not find valid parsed content for required pages.")
    except Exception as e:
        logger.warning(
            "Failed to load pre-parsed text for document %s: %s", document_id, e
        )
        raise FailBenchmark(f"{tool_name} parsing failed: {str(e)}")


@benchmark(dataset_name="character_states", skip_if=skip_non_pdf)
async def benchmark_tool_docling(
    dataset_item: Any, docs_dict: dict[str, Any], langfuse_trace: Any
) -> None:
    await _execute_tool_benchmark(
        dataset_item=dataset_item,
        tool_name="Docling",
        parser=parse_with_docling,  # type: ignore
        default_ext="pdf",
        requires_pages=True,
        docs_dict=docs_dict,
        langfuse_trace=langfuse_trace,
    )


@benchmark(dataset_name="character_states", skip_if=skip_non_pdf)
async def benchmark_tool_pymupdf(
    dataset_item: Any, docs_dict: dict[str, Any], langfuse_trace: Any
) -> None:
    await _execute_tool_benchmark(
        dataset_item=dataset_item,
        tool_name="PyMuPDF",
        parser=parse_with_pymupdf,  # type: ignore
        default_ext="pdf",
        requires_pages=True,
        docs_dict=docs_dict,
        langfuse_trace=langfuse_trace,
    )


@benchmark(dataset_name="character_states", skip_if=skip_non_docx)
async def benchmark_tool_docx(
    dataset_item: Any, docs_dict: dict[str, Any], langfuse_trace: Any
) -> None:
    await _execute_tool_benchmark(
        dataset_item=dataset_item,
        tool_name="DOCX",
        parser=parse_with_docx,  # type: ignore
        default_ext="docx",
        requires_pages=False,
        docs_dict=docs_dict,
        langfuse_trace=langfuse_trace,
    )


@benchmark(dataset_name="character_states", skip_if=skip_non_txt)
async def benchmark_tool_txt(
    dataset_item: Any, docs_dict: dict[str, Any], langfuse_trace: Any
) -> None:
    await _execute_tool_benchmark(
        dataset_item=dataset_item,
        tool_name="TXT",
        parser=parse_with_txt,  # type: ignore
        default_ext="txt",
        requires_pages=False,
        docs_dict=docs_dict,
        langfuse_trace=langfuse_trace,
    )
