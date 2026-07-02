# src/benchmark/modules/dataset/services.py
import os
import json
import asyncio
import fitz
from typing import Any, List, Dict

from tqdm.asyncio import tqdm
from langfuse import Langfuse
from lume import structlog

from matrixcurator.modules.tools.docling import parse_with_docling
from matrixcurator.modules.tools.pymupdf import parse_with_pymupdf
from matrixcurator.modules.tools.docx import parse_with_docx
from matrixcurator.modules.tools.txt import parse_with_txt
from matrixcurator.utils.concurrency import AsyncRateLimiter

from matrixcurator_benchmark.config.main import settings

logger = structlog.get_logger(__name__)


async def preparse_documents(
    parquet_repository: Any, file_path: str, force: bool = False, limit: int | None = None, no_cache: bool = False
) -> List[Dict[str, Any]]:
    """Loads documents.parquet, iterates over rows, parses missing text using extractors, and saves back to the original file."""
    
    if os.path.exists(file_path):
        docs = parquet_repository.read_documents(file_path)
    else:
        logger.error(f"Missing {file_path}. Cannot pre-parse.")
        return []

    if not docs:
        return docs

    process_docs = docs[:limit] if limit else docs

    needs_save = False

    if no_cache:
        logger.info("no_cache is True: Resetting text field in all loaded documents.")
        for row in process_docs:
            row["text"] = None
        needs_save = True
        try:
            parquet_repository.write_documents(docs, file_path)
            logger.info(f"Saved reset documents to {file_path}")
            needs_save = False
        except Exception as e:
            logger.warning(f"Failed to save reset documents to {file_path}: {e}")

    for row in process_docs:
        if "text" not in row:
            row["text"] = None

    needs_save = False

    for row in tqdm(process_docs, desc="Pre-parsing documents"):
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
                parquet_repository.write_documents(docs, file_path)
                logger.info(f"Saved intermediate parsed document {document_id} to {file_path}")
                needs_save = False
                continue

            pymupdf_pages = []
            docling_pages = []
            doc_needs_update = False

            async def process_page(page_num: int):
                pymupdf_content = get_existing_page_content("pymupdf", page_num)
                docling_content = get_existing_page_content("docling", page_num)
                
                pymupdf_text = pymupdf_content
                docling_text = docling_content
                
                pymupdf_task = None
                docling_task = None
                
                if pymupdf_content is None:
                    pymupdf_task = parse_with_pymupdf.ainvoke({
                        "file_content": file_bytes,
                        "filename": filename,
                        "pages": [page_num],
                    })
                
                if docling_content is None:
                    docling_task = parse_with_docling.ainvoke({
                        "file_content": file_bytes,
                        "filename": filename,
                        "pages": [page_num],
                    })

                if pymupdf_task or docling_task:
                    results = await asyncio.gather(
                        pymupdf_task if pymupdf_task else asyncio.sleep(0),
                        docling_task if docling_task else asyncio.sleep(0),
                        return_exceptions=True
                    )
                    
                    if pymupdf_task:
                        res = results[0]
                        if isinstance(res, Exception):
                            logger.exception("PyMuPDF failed on %s page %s", document_id, page_num)
                            pymupdf_text = f"Error: {str(res)}"
                        else:
                            pymupdf_text = res
                            
                    if docling_task:
                        res = results[1]
                        if isinstance(res, Exception):
                            logger.exception("Docling failed on %s page %s", document_id, page_num)
                            docling_text = f"Error: {str(res)}"
                        else:
                            docling_text = res

                return (page_num, pymupdf_text, docling_text, pymupdf_content is None or docling_content is None)

            tasks = [process_page(page_num) for page_num in range(1, total_pages + 1)]
            results = await asyncio.gather(*tasks)

            for page_num, pymupdf_text, docling_text, was_updated in results:
                pymupdf_pages.append({"page": page_num, "content": pymupdf_text})
                docling_pages.append({"page": page_num, "content": docling_text})
                if was_updated:
                    doc_needs_update = True

            pymupdf_pages.sort(key=lambda x: x["page"])
            docling_pages.sort(key=lambda x: x["page"])

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
                    docx_text = await parse_with_docx.ainvoke({"file_content": file_bytes, "filename": filename})
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
                    txt_text = await parse_with_txt.ainvoke({"file_content": file_bytes, "filename": filename})
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
                parquet_repository.write_documents(docs, file_path)
                logger.info(f"Saved intermediate parsed document {document_id} to {file_path}")
                needs_save = False
            except Exception as e:
                logger.warning(f"Failed to cache document {document_id}: {e}")

    if needs_save:
        parquet_repository.write_documents(docs, file_path)
        logger.info(f"Saved parsed documents to {file_path}")
    
    return process_docs


async def sync_datasets(
    parquet_repository: Any, langfuse_repository: Any, client: Langfuse, docs: List[Dict[str, Any]]
) -> None:
    """Reads parquets and unconditionally pushes all rows to Langfuse using the injected langfuse_repository module."""

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
    chars = parquet_repository.read_character_states(chars_path)

    limiter = AsyncRateLimiter(settings=settings.langfuse_rate_limit) if settings.langfuse_rate_limit else None

    valid_doc_ids = {str(d.get("id", d.get("document_id", f"idx_{i}"))) for i, d in enumerate(docs)}

    filtered_chars = []
    for row in chars:
        if str(row.get("document_id")) in valid_doc_ids:
            filtered_chars.append(row)
    chars = filtered_chars

    # Push to 'documents' dataset
    logger.info("Uploading documents to Langfuse")
    for idx, row in tqdm(enumerate(docs), total=len(docs), desc="Syncing Documents Dataset"):
        document_id = str(row.get("id", row.get("document_id", f"idx_{idx}")))

        # Get parsed text directly from the dataframe row
        text_content = row.get("text", [])
        pages_set = set()
        character_count = 0
        
        if isinstance(text_content, list) and len(text_content) > 0:
            first_parser = text_content[0]
            if isinstance(first_parser, dict) and "pages" in first_parser:
                for pg in first_parser.get("pages", []):
                    if isinstance(pg, dict):
                        pages_set.add(pg.get("page", 0))
                        character_count += len(str(pg.get("content", "")))
        
        expected_output = {
            "pages": sorted(list(pages_set)),
            "character_count": character_count
        }

        item = {
            "id": f"Doc-{document_id}",
            "input": {
                "id": f"Doc-{document_id}",
                "filename": row.get("filename", ""),
                "mimetype": row.get("mime_type", ""),
            },
            "expected_output": json.dumps(expected_output),
            "metadata": {"source_row_index": idx},
        }
        if limiter:
            await limiter.acquire()
        await langfuse_repository.upsert_dataset_item(client, "documents", item)

    # Push to 'character_states' dataset
    logger.info("Uploading character states to Langfuse")
    for idx, row in tqdm(enumerate(chars), total=len(chars), desc="Syncing Character States Dataset"):
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

        document_id = str(row.get("document_id", "unknown"))
        item_name = f"Doc-{document_id}-Char-{char_index}"
        
        input_data = {
            "id": item_name,
            "document_id": document_id,
            "character_index": char_index,
        }
        character_data["states"] = states_data

        item = {
            "id": item_name,
            "input": input_data,
            "expected_output": json.dumps({"character": character_data}),
            "metadata": {"source_row_index": idx, "name": item_name},
        }
        if limiter:
            await limiter.acquire()
        await langfuse_repository.upsert_dataset_item(client, "character_states", item)

    logger.info("Dataset sync complete")
