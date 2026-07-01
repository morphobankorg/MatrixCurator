import json
import pandas as pd
from typing import Any, Dict
import structlog
import functools

from matrixcurator_benchmark.services import run_dataset_benchmark

logger = structlog.get_logger(__name__)


def filter_tool_items(item: Any, expected_mime: str, docs_dict: Dict[str, Any]) -> bool:
    input_data = item.input
    
    document_id = None
    if isinstance(input_data, dict):
        document_id = input_data.get("document_id")
    elif hasattr(input_data, "document_id"):
        document_id = getattr(input_data, "document_id", None)
    elif isinstance(input_data, str):
        try:
            parsed = json.loads(input_data)
            if isinstance(parsed, dict):
                document_id = parsed.get("document_id")
        except Exception:
            pass

    doc_row = docs_dict.get(document_id)
    if not doc_row:
        return False
        
    if doc_row.get("mime_type", "") != expected_mime:
        return False
        
    return True


async def tool_task(
    *, 
    item: Any, 
    tool_name: str, 
    requires_pages: bool, 
    docs_dict: Dict[str, Any],
    **kwargs
) -> str:
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
        raise ValueError(f"Document {document_id} not found in parquet data.")
        
    if pages is None or (hasattr(pages, "__len__") and len(pages) == 0):
        # Resolve all available pages from the parsed text
        pre_parsed_text = doc_row.get("text")
        if isinstance(pre_parsed_text, str):
            try:
                parses = json.loads(pre_parsed_text)
            except Exception:
                parses = []
        elif isinstance(pre_parsed_text, (list, tuple)):
            parses = list(pre_parsed_text)
        else:
            parses = []
            
        all_pages = set()
        parser_name = tool_name.lower()
        if not isinstance(parses, list):
            if parses:
                parses = [parses]
            else:
                parses = []
                
        for parse_obj in parses:
            if parse_obj.get("parser") == parser_name:
                parsed_pages = parse_obj.get("pages") or []
                for pg in parsed_pages:
                    if isinstance(pg, dict) and pg.get("page") is not None:
                        all_pages.add(int(pg.get("page")))
        
        if all_pages:
            pages = sorted(list(all_pages))
        else:
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
        raise ValueError(f"{tool_name} parsing failed: missing text in parquet cache for doc {document_id}")

    try:
        if isinstance(pre_parsed_text, str):
            parses = json.loads(pre_parsed_text)
        elif isinstance(pre_parsed_text, (list, tuple)):
            parses = list(pre_parsed_text)
        else:
            raise ValueError(f"{tool_name} parsing failed: Unsupported type {type(pre_parsed_text)} for parsed text")
            
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
                        return "\n\n".join(content_list)
                else:
                    sorted_pages = sorted(
                        [pg for pg in parsed_pages if isinstance(pg, dict)], key=lambda x: x.get("page", 0)
                    )
                    content_list = [pg.get("content", "") for pg in sorted_pages]
                    if content_list:
                        return "\n\n".join(content_list)
                        
        raise ValueError(f"{tool_name} parsing failed: Could not find valid parsed content for required pages.")
    except Exception as e:
        logger.warning(
            "Failed to load pre-parsed text", document_id=document_id, error=str(e)
        )
        raise ValueError(f"{tool_name} parsing failed: {str(e)}")


async def run_tools_benchmarks(limit: int, workers: int, docs_dict: Dict[str, Any]) -> None:
    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_tool_docling",
        task_fn=functools.partial(
            tool_task, tool_name="Docling", requires_pages=True, docs_dict=docs_dict
        ),
        filter_fn=lambda item: filter_tool_items(item, "application/pdf", docs_dict),
        limit=limit,
        workers=workers
    )

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_tool_pymupdf",
        task_fn=functools.partial(
            tool_task, tool_name="PyMuPDF", requires_pages=True, docs_dict=docs_dict
        ),
        filter_fn=lambda item: filter_tool_items(item, "application/pdf", docs_dict),
        limit=limit,
        workers=workers
    )

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_tool_docx",
        task_fn=functools.partial(
            tool_task, tool_name="DOCX", requires_pages=False, docs_dict=docs_dict
        ),
        filter_fn=lambda item: filter_tool_items(
            item, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", docs_dict
        ),
        limit=limit,
        workers=workers
    )

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_tool_txt",
        task_fn=functools.partial(
            tool_task, tool_name="TXT", requires_pages=False, docs_dict=docs_dict
        ),
        filter_fn=lambda item: filter_tool_items(item, "text/plain", docs_dict),
        limit=limit,
        workers=workers
    )
