from typing import Any, Optional, Set
import structlog
import functools

from sqlalchemy import select
from sqlalchemy.orm import Session

from matrixcurator_benchmark.exceptions import FailBenchmark, SkipBenchmark
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


async def _execute_retrieval_benchmark(
    item: Any,
    trace: Any,
    parser_name: str,
    valid_docs_per_parser: dict[str, set[str] | None],
) -> None:
    input_data = item.input
    character_index = input_data.get("character_index", 1)

    character = input_data.get("character", {})
    char_name = character.get("name")

    if char_name:
        query = f"Character {character_index}: {char_name}"
    else:
        query = f"Character {character_index}"

    document_id = str(input_data.get("document_id"))

    if not document_id:
        raise FailBenchmark("No document ID provided in input.")

    valid_docs = valid_docs_per_parser.get(parser_name)
    if valid_docs is not None and document_id not in valid_docs:
        raise SkipBenchmark(
            f"Document {document_id} has no vectorized chunks for {parser_name}."
        )

    logger.debug(f"Retrieving context for {query} using parser {parser_name}")
    retrieved_context = await retrieve_context(
        query=query, document_id=document_id, parser_name=parser_name
    )

    trace.update(output=retrieved_context)


async def process_retrieval_docling(item: Any, trace: Any, valid_docs_per_parser: dict[str, set[str] | None]) -> None:
    await _execute_retrieval_benchmark(item, trace, "docling", valid_docs_per_parser)


async def process_retrieval_pymupdf(item: Any, trace: Any, valid_docs_per_parser: dict[str, set[str] | None]) -> None:
    await _execute_retrieval_benchmark(item, trace, "pymupdf", valid_docs_per_parser)


async def process_retrieval_docx(item: Any, trace: Any, valid_docs_per_parser: dict[str, set[str] | None]) -> None:
    await _execute_retrieval_benchmark(item, trace, "docx", valid_docs_per_parser)


async def process_retrieval_txt(item: Any, trace: Any, valid_docs_per_parser: dict[str, set[str] | None]) -> None:
    await _execute_retrieval_benchmark(item, trace, "txt", valid_docs_per_parser)


async def run_retrieval_benchmarks(limit: int, workers: int, docs_dict: dict[str, Any]) -> None:
    valid_docs_per_parser = {
        parser: _get_valid_document_ids_for_parser(parser)
        for parser in PARSERS
    }

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_retrieval_docling",
        process_fn=functools.partial(process_retrieval_docling, valid_docs_per_parser=valid_docs_per_parser),
        limit=limit,
        workers=workers
    )

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_retrieval_pymupdf",
        process_fn=functools.partial(process_retrieval_pymupdf, valid_docs_per_parser=valid_docs_per_parser),
        limit=limit,
        workers=workers
    )

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_retrieval_docx",
        process_fn=functools.partial(process_retrieval_docx, valid_docs_per_parser=valid_docs_per_parser),
        limit=limit,
        workers=workers
    )

    await run_dataset_benchmark(
        dataset_name="character_states",
        run_name="benchmark_retrieval_txt",
        process_fn=functools.partial(process_retrieval_txt, valid_docs_per_parser=valid_docs_per_parser),
        limit=limit,
        workers=workers
    )
