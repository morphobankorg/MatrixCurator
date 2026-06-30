import json
import pandas as pd
from typing import Any, Dict
import structlog
import functools

from matrixcurator_benchmark.exceptions import FailBenchmark, SkipBenchmark
from matrixcurator_benchmark.services import run_dataset_benchmark

logger = structlog.get_logger(__name__)

async def _execute_tool_benchmark(
    item: Any,
    trace: Any,
    tool_name: str,
    requires_pages: bool,
    docs_dict: Dict[str, Any],
    expected_mime: str,
) -> None:
    input_data = item.input
    
    document_id = None
    pages = None
    if isinstance(input_data, dict):
        document_id = input_data.get("document_id")
        pages = input_data.get("pages")
    elif hasattr(input_data, "document_id"):
        document_id = getattr(input_data, "document_id", None)
        pages = getattr(input_data, "pages", None)
    elif isinstance(input_data, str):
        try:
            parsed = json.loads(input_data)
            if isinstance(parsed, dict):
                document_id = parsed.get("document_id")
                pages = parsed.get("pages")
        except Exception:
            pass

    doc_row = docs_dict.get(document_id)
    if not doc_row:
        raise SkipBenchmark(f"Document {document_id} not found in parquet data.")
        
    if doc_row.get("mime_type", "") != expected_mime:
        raise SkipBenchmark(f"Skipping {document_id} because mime_type != {expected_mime}")
        
    if pages is None:
        pages = [1]
    elif hasattr(pages, "__len__") and len(pages) == 0:
        pages = [1]

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
                        trace.update(output=result)
                        return
                else:
                    sorted_pages = sorted(
                        [pg for pg in parsed_pages if isinstance(pg, dict)], key=lambda x: x.get("page", 0)
                    )
                    content_list = [pg.get("content", "") for pg in sorted_pages]
                    if content_list:
                        result = "\n\n".join(content_list)
                        trace.update(output=result)
                        return
                        
        raise FailBenchmark(f"{tool_name} parsing failed: Could not find valid parsed content for required pages.")
    except SkipBenchmark:
        raise
    except FailBenchmark:
        raise
    except Exception as e:
        logger.warning(
            "Failed to load pre-parsed text for document %s: %s", document_id, e
        )
        raise FailBenchmark(f"{tool_name} parsing failed: {str(e)}")


async def process_docling(item: Any, trace: Any, docs_dict: Dict[str, Any]) -> None:
    await _execute_tool_benchmark(
        item=item,
        trace=trace,
        tool_name="Docling",
        requires_pages=True,
        docs_dict=docs_dict,
        expected_mime="application/pdf",
    )


async def process_pymupdf(item: Any, trace: Any, docs_dict: Dict[str, Any]) -> None:
    await _execute_tool_benchmark(
        item=item,
        trace=trace,
        tool_name="PyMuPDF",
        requires_pages=True,
        docs_dict=docs_dict,
        expected_mime="application/pdf",
    )


async def process_docx(item: Any, trace: Any, docs_dict: Dict[str, Any]) -> None:
    await _execute_tool_benchmark(
        item=item,
        trace=trace,
        tool_name="DOCX",
        requires_pages=False,
        docs_dict=docs_dict,
        expected_mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


async def process_txt(item: Any, trace: Any, docs_dict: Dict[str, Any]) -> None:
    await _execute_tool_benchmark(
        item=item,
        trace=trace,
        tool_name="TXT",
        requires_pages=False,
        docs_dict=docs_dict,
        expected_mime="text/plain",
    )


async def run_tools_benchmarks(limit: int, workers: int, docs_dict: Dict[str, Any]) -> None:
    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_tool_docling",
        process_fn=functools.partial(process_docling, docs_dict=docs_dict),
        limit=limit,
        workers=workers
    )

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_tool_pymupdf",
        process_fn=functools.partial(process_pymupdf, docs_dict=docs_dict),
        limit=limit,
        workers=workers
    )

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_tool_docx",
        process_fn=functools.partial(process_docx, docs_dict=docs_dict),
        limit=limit,
        workers=workers
    )

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_tool_txt",
        process_fn=functools.partial(process_txt, docs_dict=docs_dict),
        limit=limit,
        workers=workers
    )
