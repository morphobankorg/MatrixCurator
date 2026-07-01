import json
from typing import Any, Optional, Set, Dict
import structlog
import functools

from sqlalchemy import select
from sqlalchemy.orm import Session

from matrixcurator_benchmark.services import run_dataset_benchmark
from matrixcurator.modules.retrieval.services import retrieve_context
from matrixcurator.modules.retrieval.repositories import sqlite

logger = structlog.get_logger(__name__)

PARSERS = ["docling", "pymupdf", "docx", "txt"]

def _get_valid_document_ids_for_parser(parser_name: str) -> Optional[Set[str]]:
    engine = sqlite.get_engine()
    with Session(engine) as session:
        result = session.execute(
            select(sqlite.DocumentChunkMeta.document_id)
            .where(sqlite.DocumentChunkMeta.parser_name == parser_name)
            .distinct()
        ).scalars().all()
        return set(result) if result else None


def filter_retrieval_items(item: Any, parser_name: str, valid_docs_per_parser: Dict[str, Optional[Set[str]]]) -> bool:
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

    if not document_id:
        return False
        
    document_id = str(document_id)
    valid_docs = valid_docs_per_parser.get(parser_name)
    if valid_docs is not None and document_id not in valid_docs:
        return False
        
    return True


async def retrieval_task(*, item: Any, parser_name: str, **kwargs) -> Any:
    input_data = item.input
    
    character_index = 1
    char_name = None
    document_id = None
    
    if isinstance(input_data, dict):
        character_index = input_data.get("character_index", 1)
        character = input_data.get("character", {})
        char_name = character.get("name")
        document_id = str(input_data.get("document_id"))
    elif hasattr(input_data, "document_id"):
        character_index = getattr(input_data, "character_index", 1)
        character = getattr(input_data, "character", {})
        char_name = character.get("name")
        document_id = str(getattr(input_data, "document_id"))
    elif isinstance(input_data, str):
        try:
            parsed = json.loads(input_data)
            if isinstance(parsed, dict):
                character_index = parsed.get("character_index", 1)
                character = parsed.get("character", {})
                char_name = character.get("name")
                document_id = str(parsed.get("document_id"))
        except Exception:
            pass

    if char_name:
        query = f"Character {character_index}: {char_name}"
    else:
        query = f"Character {character_index}"

    if not document_id:
        raise ValueError("No document ID provided in input.")

    logger.debug(f"Retrieving context for {query} using parser {parser_name}")
    retrieved_context = await retrieve_context(
        query=query, document_id=document_id, parser_name=parser_name
    )

    return retrieved_context


async def run_retrieval_benchmarks(limit: int, workers: int, docs_dict: Dict[str, Any]) -> None:
    valid_docs_per_parser = {
        parser: _get_valid_document_ids_for_parser(parser)
        for parser in PARSERS
    }

    for parser_name in PARSERS:
        await run_dataset_benchmark(
            dataset_name="character_states",
            run_name=f"benchmark_retrieval_{parser_name}",
            task_fn=functools.partial(retrieval_task, parser_name=parser_name),
            filter_fn=lambda item, p=parser_name: filter_retrieval_items(item, p, valid_docs_per_parser),
            limit=limit,
            workers=workers
        )
