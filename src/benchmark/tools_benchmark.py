# src/benchmark/tools_benchmark.py
import os
import json
import asyncio
import pandas as pd
from typing import Any
from python_logging import get_logger
from langfuse import Langfuse

from matrixcurator.modules.tools.docling import parse_with_docling
from matrixcurator.modules.tools.pymupdf import parse_with_pymupdf
from matrixcurator.modules.tools.docx import parse_with_docx
from matrixcurator.modules.tools.txt import parse_with_txt
from matrixcurator.config.main import settings
from .confbenchmark import setup

logger = get_logger(__name__)

def _execute_parser_task(
    *,
    item: Any,
    docs_dict: dict[str, dict[str, Any]],
    cache: dict[tuple[str, tuple[int, ...]], str],
    parser: Any,
    expected_mime_type: str,
    tool_name: str,
    default_ext: str,
    requires_pages: bool = True
) -> str:
    """Generic execution task for all parsers to enforce DRY and O(1) lookups."""
    input_data = item.input
    document_id = input_data.get("document_id")
    pages = input_data.get("pages", [1])
    
    cache_key = (document_id, tuple(pages))
    if cache_key in cache:
        return cache[cache_key]
        
    doc_row = docs_dict.get(document_id)
    if not doc_row:
        return "Document not found"
        
    mime_type = doc_row.get('mime_type', '')
    if mime_type != expected_mime_type:
        return f"Skipped: Not a {default_ext.upper()} file"
    
    file_bytes = doc_row.get('file_bytes')
    filename = doc_row.get('filename', f"doc_{document_id}.{default_ext}")
    
    try:
        invoke_args = {"file_content": file_bytes, "filename": filename}
        if requires_pages:
            invoke_args["pages"] = pages
            
        result = parser.invoke(invoke_args)
        cache[cache_key] = result
        return result
    except Exception as e:
        logger.exception("%s parsing failed for document %s", tool_name, document_id)
        return f"{tool_name} parsing failed: {str(e)}"

def docling_task(*, item: Any, docs_dict: dict[str, dict[str, Any]], cache: dict[tuple[str, tuple[int, ...]], str], **kwargs) -> str:
    return _execute_parser_task(
        item=item, docs_dict=docs_dict, cache=cache,
        parser=parse_with_docling, expected_mime_type='application/pdf', 
        tool_name='Docling', default_ext='pdf'
    )

def pymupdf_task(*, item: Any, docs_dict: dict[str, dict[str, Any]], cache: dict[tuple[str, tuple[int, ...]], str], **kwargs) -> str:
    return _execute_parser_task(
        item=item, docs_dict=docs_dict, cache=cache,
        parser=parse_with_pymupdf, expected_mime_type='application/pdf', 
        tool_name='PyMuPDF', default_ext='pdf'
    )

def docx_task(*, item: Any, docs_dict: dict[str, dict[str, Any]], cache: dict[tuple[str, tuple[int, ...]], str], **kwargs) -> str:
    return _execute_parser_task(
        item=item, docs_dict=docs_dict, cache=cache,
        parser=parse_with_docx, expected_mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
        tool_name='DOCX', default_ext='docx', requires_pages=False
    )

def txt_task(*, item: Any, docs_dict: dict[str, dict[str, Any]], cache: dict[tuple[str, tuple[int, ...]], str], **kwargs) -> str:
    return _execute_parser_task(
        item=item, docs_dict=docs_dict, cache=cache,
        parser=parse_with_txt, expected_mime_type='text/plain', 
        tool_name='TXT', default_ext='txt', requires_pages=False
    )

def process_benchmark(langfuse: Langfuse, dataset: Any, df_docs: pd.DataFrame):
    if 'id' in df_docs.columns:
        docs_dict = df_docs.set_index('id').to_dict(orient='index')
    else:
        docs_dict = {}

    pdf_ids = set(df_docs[df_docs['mime_type'] == 'application/pdf']['id'].astype(str)) if 'mime_type' in df_docs.columns and 'id' in df_docs.columns else set()
    docx_ids = set(df_docs[df_docs['mime_type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']['id'].astype(str)) if 'mime_type' in df_docs.columns and 'id' in df_docs.columns else set()
    txt_ids = set(df_docs[df_docs['mime_type'] == 'text/plain']['id'].astype(str)) if 'mime_type' in df_docs.columns and 'id' in df_docs.columns else set()

    docling_cache: dict[tuple[str, tuple[int, ...]], str] = {}
    pymupdf_cache: dict[tuple[str, tuple[int, ...]], str] = {}
    docx_cache: dict[tuple[str, tuple[int, ...]], str] = {}
    txt_cache: dict[tuple[str, tuple[int, ...]], str] = {}

    original_items = list(dataset.items)

    try:
        pdf_items = [item for item in original_items if str(item.input.get("document_id")) in pdf_ids]
        if pdf_items:
            dataset.items = pdf_items
            logger.info("Running Docling Parser Benchmark")
            dataset.run_experiment(
                name="Parser-Docling-Run",
                description="Tools Benchmark for Docling",
                task=lambda *, item, **kwargs: docling_task(item=item, docs_dict=docs_dict, cache=docling_cache)
            )

            logger.info("Running PyMuPDF Parser Benchmark")
            dataset.run_experiment(
                name="Parser-PyMuPDF-Run",
                description="Tools Benchmark for PyMuPDF",
                task=lambda *, item, **kwargs: pymupdf_task(item=item, docs_dict=docs_dict, cache=pymupdf_cache)
            )
        else:
            logger.info("Skipping PDF Parser Benchmarks: No application/pdf files found in dataset.")
        
        docx_items = [item for item in original_items if str(item.input.get("document_id")) in docx_ids]
        if docx_items:
            dataset.items = docx_items
            logger.info("Running DOCX Parser Benchmark")
            dataset.run_experiment(
                name="Parser-DOCX-Run",
                description="Tools Benchmark for DOCX",
                task=lambda *, item, **kwargs: docx_task(item=item, docs_dict=docs_dict, cache=docx_cache)
            )
        else:
            logger.info("Skipping DOCX Parser Benchmark: No DOCX files found in dataset.")
        
        txt_items = [item for item in original_items if str(item.input.get("document_id")) in txt_ids]
        if txt_items:
            dataset.items = txt_items
            logger.info("Running TXT Parser Benchmark")
            dataset.run_experiment(
                name="Parser-TXT-Run",
                description="Tools Benchmark for TXT",
                task=lambda *, item, **kwargs: txt_task(item=item, docs_dict=docs_dict, cache=txt_cache)
            )
        else:
            logger.info("Skipping TXT Parser Benchmark: No text/plain files found in dataset.")
    finally:
        dataset.items = original_items

def run_tools_benchmark():
    langfuse, dataset = setup()
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    docs_path = os.path.join(data_dir, "documents.parquet")
    logger.info("Loading documents parquet", path=docs_path)
    df_docs = pd.read_parquet(docs_path)

    process_benchmark(langfuse, dataset, df_docs)
    
    langfuse.flush()
    logger.info("Tools Benchmark completed")

if __name__ == "__main__":
    run_tools_benchmark()
