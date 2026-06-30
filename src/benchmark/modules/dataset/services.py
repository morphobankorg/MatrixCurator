# src/benchmark/modules/dataset/services.py
import os
import json
import asyncio
import fitz
from typing import Any, List, Dict

from tqdm import tqdm
from langfuse import Langfuse
from lume import structlog

from matrixcurator.modules.tools.docling import parse_with_docling
from matrixcurator.modules.tools.pymupdf import parse_with_pymupdf
from matrixcurator.modules.tools.docx import parse_with_docx
from matrixcurator.modules.tools.txt import parse_with_txt

from src.benchmark.config.main import settings

logger = structlog.get_logger(__name__)


def preparse_documents(
    parquet_repo: Any, file_path: str, force: bool = False, limit: int | None = None
) -> List[Dict[str, Any]]:
    """Loads documents.parquet, iterates over rows, parses missing text using extractors, and saves to cache."""
    cache_dir = settings.parsed_cache_dir
    os.makedirs(cache_dir, exist_ok=True)
    cached_docs_path = os.path.join(cache_dir, "documents.parquet")

    if not force and os.path.exists(cached_docs_path):
        import pyarrow.parquet as pq
        docs = pq.read_table(cached_docs_path).to_pylist()
    elif os.path.exists(file_path):
        docs = parquet_repo.read_documents(file_path)
        parquet_repo.write_documents(docs, cached_docs_path)
    else:
        logger.error(f"Missing {file_path}. Cannot pre-parse.")
        return []

    if not docs:
        return docs

    if limit:
        docs = docs[:limit]

    for row in docs:
        if "text" not in row:
            row["text"] = None

    needs_save = False

    for row in tqdm(docs, desc="Pre-parsing documents"):
        document_id = row.get("id", row.get("document_id"))
        mime_type = row.get("mime_type", "")
        filename = row.get("filename", "")
        file_bytes = row.get("file_bytes")

        existing_text = row.get("text")
        
        is_missing = False
        if existing_text is None:
            is_missing = True
        elif isinstance(existing_text, (list, dict, tuple)):
            is_missing = len(existing_text) == 0
        elif isinstance(existing_text, str):
            is_missing = not existing_text.strip()

        existing_parses = []
        if not is_missing:
            if isinstance(existing_text, str):
                try:
                    existing_parses = json.loads(existing_text)
                except Exception:
                    pass
            elif isinstance(existing_text, (list, tuple)):
                existing_parses = list(existing_text)
                
        if not isinstance(existing_parses, list):
            if existing_parses is None:
                existing_parses = []
            else:
                existing_parses = [existing_parses]
        
        def get_existing_page_content(parser_name: str, page_num: int) -> str | None:
            for parse_obj in existing_parses:
                if not isinstance(parse_obj, dict):
                    continue
                if parse_obj.get("parser") == parser_name:
                    parsed_pages = parse_obj.get("pages") or []
                    
                    for pg in parsed_pages:
                        if isinstance(pg, dict) and pg.get("page") == page_num:
                            content = pg.get("content", "")
                            if not str(content).startswith("Error:"):
                                return content
            return None

        updated_parses: list[dict[str, Any]] = []

        if mime_type == "application/pdf":
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                total_pages = doc.page_count
                doc.close()
            except Exception as e:
                logger.exception("Failed to get page count for PDF %s", document_id)
                updated_parses.append({"parser": "pymupdf", "pages": [{"page": 1, "content": f"Error: {str(e)}"}]})
                updated_parses.append({"parser": "docling", "pages": [{"page": 1, "content": f"Error: {str(e)}"}]})
                row["text"] = updated_parses
                parquet_repo.write_documents(docs, cached_docs_path)
                logger.info(f"Saved intermediate parsed document {document_id} to {cached_docs_path}")
                needs_save = False
                continue

            pymupdf_pages = []
            docling_pages = []
            doc_needs_update = False

            for page_num in range(1, total_pages + 1):
                # PyMuPDF
                pymupdf_content = get_existing_page_content("pymupdf", page_num)
                if pymupdf_content is not None:
                    pymupdf_text = pymupdf_content
                else:
                    doc_needs_update = True
                    try:
                        pymupdf_text = parse_with_pymupdf.invoke({
                            "file_content": file_bytes,
                            "filename": filename,
                            "pages": [page_num],
                        })
                    except Exception as e:
                        logger.exception("PyMuPDF failed on %s page %s", document_id, page_num)
                        pymupdf_text = f"Error: {str(e)}"
                pymupdf_pages.append({"page": page_num, "content": pymupdf_text})

                # Docling
                docling_content = get_existing_page_content("docling", page_num)
                if docling_content is not None:
                    docling_text = docling_content
                else:
                    doc_needs_update = True
                    try:
                        docling_text = parse_with_docling.invoke({
                            "file_content": file_bytes,
                            "filename": filename,
                            "pages": [page_num],
                        })
                    except Exception as e:
                        logger.exception("Docling failed on %s page %s", document_id, page_num)
                        docling_text = f"Error: {str(e)}"
                docling_pages.append({"page": page_num, "content": docling_text})

            if not doc_needs_update and existing_parses:
                updated_parses = existing_parses
            else:
                for p in existing_parses:
                    if isinstance(p, dict) and p.get("parser") not in ["pymupdf", "docling"]:
                        updated_parses.append(p)
                updated_parses.append({"parser": "pymupdf", "pages": pymupdf_pages})
                updated_parses.append({"parser": "docling", "pages": docling_pages})
                needs_save = True

        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            docx_content = get_existing_page_content("docx", 1)
            if docx_content is not None:
                updated_parses = existing_parses
            else:
                try:
                    docx_text = parse_with_docx.invoke({"file_content": file_bytes, "filename": filename})
                except Exception as e:
                    logger.exception("DOCX parser failed on %s", document_id)
                    docx_text = f"Error: {str(e)}"
                for p in existing_parses:
                    if p.get("parser") != "docx":
                        updated_parses.append(p)
                updated_parses.append({"parser": "docx", "pages": [{"page": 1, "content": docx_text}]})
                needs_save = True

        elif mime_type == "text/plain":
            txt_content = get_existing_page_content("txt", 1)
            if txt_content is not None:
                updated_parses = existing_parses
            else:
                try:
                    txt_text = parse_with_txt.invoke({"file_content": file_bytes, "filename": filename})
                except Exception as e:
                    logger.exception("TXT parser failed on %s", document_id)
                    txt_text = f"Error: {str(e)}"
                for p in existing_parses:
                    if p.get("parser") != "txt":
                        updated_parses.append(p)
                updated_parses.append({"parser": "txt", "pages": [{"page": 1, "content": txt_text}]})
                needs_save = True
        else:
            if not existing_parses:
                logger.warning("Unknown mime_type %s for %s", mime_type, document_id)
                updated_parses.append({"parser": "unknown", "pages": [{"page": 1, "content": f"Unsupported mime_type: {mime_type}"}]})
                needs_save = True
            else:
                updated_parses = existing_parses

        if updated_parses and updated_parses != existing_parses:
            row["text"] = updated_parses
            try:
                parquet_repo.write_documents(docs, cached_docs_path)
                logger.info(f"Saved intermediate parsed document {document_id} to {cached_docs_path}")
                needs_save = False
            except Exception as e:
                logger.warning(f"Failed to cache document {document_id}: {e}")

    if needs_save:
        parquet_repo.write_documents(docs, cached_docs_path)
        logger.info(f"Saved parsed documents to {cached_docs_path}")
    
    return docs


async def sync_datasets(
    parquet_repo: Any, langfuse_repo: Any, client: Langfuse, docs: List[Dict[str, Any]]
) -> None:
    """Reads parquets and unconditionally pushes all rows to Langfuse using the injected langfuse_repo module."""

    chars_path = settings.character_states_parquet_path

    logger.info("Creating documents dataset")
    client.create_dataset(
        name="documents",
        description="Dataset containing raw document data and extracted pages.",
    )

    logger.info("Creating character_states dataset")
    client.create_dataset(
        name="character_states",
        description="Dataset containing morphological character states tied to document pages.",
    )

    logger.info("Reading character states parquet file")
    chars = parquet_repo.read_character_states(chars_path)

    # Push to 'documents' dataset
    logger.info("Uploading documents to Langfuse")
    doc_tasks = []
    for idx, row in enumerate(docs):
        document_id = str(row.get("id", row.get("document_id", f"idx_{idx}")))

        # Get parsed text directly from the dataframe row
        text_content = row.get("text", [])
        if isinstance(text_content, (list, dict)):
            text_json = json.dumps(text_content)
        else:
            text_json = json.dumps({"text": text_content})

        item = {
            "id": f"Doc-{document_id}",
            "input": {
                "document_id": document_id,
                "mime_type": row.get("mime_type", ""),
                "filename": row.get("filename", ""),
            },
            "expected_output": text_json,
            "metadata": {"source_row_index": idx},
        }
        doc_tasks.append(langfuse_repo.upsert_dataset_item(client, "documents", item))

    if doc_tasks:
        # Use simple chunking to avoid overwhelming the event loop and Langfuse
        chunk_size = 50
        for i in tqdm(
            range(0, len(doc_tasks), chunk_size), desc="Syncing Documents Dataset"
        ):
            await asyncio.gather(*doc_tasks[i : i + chunk_size])

    # Push to 'character_states' dataset
    logger.info("Uploading character states to Langfuse")
    char_tasks = []
    for idx, row in enumerate(chars):
        character_data = row.get("character", {})
        if isinstance(character_data, str):
            try:
                character_data = json.loads(character_data)
            except Exception:
                character_data = {}

        char_index = character_data.get("index", 1)
        states_data = row.get("states", [])
        if isinstance(states_data, str):
            try:
                states_data = json.loads(states_data)
            except Exception:
                states_data = []
        elif isinstance(states_data, (list, tuple)):
            states_data = list(states_data)

        pages = row.get("pages", [1])
        if isinstance(pages, str):
            pages = [int(p) for p in pages.split("-")] if "-" in pages else [int(pages)]
        elif isinstance(pages, (list, tuple)):
            pages = list(pages)

        document_id = str(row.get("document_id", "unknown"))
        input_data = {
            "character_index": char_index,
            "document_id": document_id,
            "pages": pages,
        }
        character_data["states"] = states_data

        item_name = f"Doc-{document_id}-Char-{char_index}"
        item = {
            "id": item_name,
            "input": input_data,
            "expected_output": json.dumps({"character": character_data}),
            "metadata": {"source_row_index": idx, "name": item_name},
        }
        char_tasks.append(
            langfuse_repo.upsert_dataset_item(client, "character_states", item)
        )

    if char_tasks:
        chunk_size = 50
        for i in tqdm(
            range(0, len(char_tasks), chunk_size),
            desc="Syncing Character States Dataset",
        ):
            await asyncio.gather(*char_tasks[i : i + chunk_size])

    logger.info("Dataset sync complete")
