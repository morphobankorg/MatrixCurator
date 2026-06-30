# src/benchmark/benchmark_retrieval.py
from typing import Any

from matrixcurator_benchmark.core.decorators import benchmark
from matrixcurator_benchmark.core.exceptions import FailBenchmark, SkipBenchmark

from matrixcurator.modules.retrieval.services import (
    retrieve_context,
)
import structlog

logger = structlog.get_logger(__name__)

PARSERS = ["docling", "pymupdf", "docx", "txt"]


async def _execute_retrieval_benchmark(
    dataset_item: Any,
    parser_name: str,
    valid_docs_per_parser: dict[str, set[str] | None],
    langfuse_trace: Any,
) -> None:
    input_data = dataset_item.input
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

    langfuse_trace(retrieved_context)


@benchmark(dataset_name="character_states")
async def benchmark_retrieval_docling(
    dataset_item, valid_docs_per_parser, fixture_vector_cache, langfuse_trace
):
    await _execute_retrieval_benchmark(
        dataset_item, "docling", valid_docs_per_parser, langfuse_trace
    )


@benchmark(dataset_name="character_states")
async def benchmark_retrieval_pymupdf(
    dataset_item, valid_docs_per_parser, fixture_vector_cache, langfuse_trace
):
    await _execute_retrieval_benchmark(
        dataset_item, "pymupdf", valid_docs_per_parser, langfuse_trace
    )


@benchmark(dataset_name="character_states")
async def benchmark_retrieval_docx(
    dataset_item, valid_docs_per_parser, fixture_vector_cache, langfuse_trace
):
    await _execute_retrieval_benchmark(
        dataset_item, "docx", valid_docs_per_parser, langfuse_trace
    )


@benchmark(dataset_name="character_states")
async def benchmark_retrieval_txt(
    dataset_item, valid_docs_per_parser, fixture_vector_cache, langfuse_trace
):
    await _execute_retrieval_benchmark(
        dataset_item, "txt", valid_docs_per_parser, langfuse_trace
    )
