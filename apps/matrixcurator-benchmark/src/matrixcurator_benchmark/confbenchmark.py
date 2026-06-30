# src/benchmark/confbenchmark.py
import os
import asyncio
import pandas as pd
from typing import Set, Optional, Any
from lume import structlog

from matrixcurator_benchmark.core.decorators import fixture
from matrixcurator.config.main import settings as core_settings
from matrixcurator_benchmark.config.main import settings as benchmark_settings
import matrixcurator.modules.retrieval.repositories.sqlite as sqlite_repo

from matrixcurator_benchmark.modules.dataset.services import preparse_documents, sync_datasets
from matrixcurator_benchmark.modules.evaluation.services import setup_evaluators
import matrixcurator_benchmark.modules.dataset.repositories.langfuse as dataset_langfuse_repository
import matrixcurator_benchmark.modules.evaluation.repositories.langfuse as evaluation_langfuse_repository
import matrixcurator_benchmark.modules.dataset.repositories.parquet as parquet_repo
from matrixcurator_benchmark.modules.retrieval.services import auto_ingest_vectors

logger = structlog.get_logger(__name__)

PARSERS = ["docling", "pymupdf", "docx", "txt"]

from typing import Set, Optional, Any, List, Dict

@fixture(scope="session")
async def fixture_parsed_cache(limit: int, no_cache: bool = False) -> List[Dict[str, Any]]:
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    docs_path = os.path.join(data_dir, "documents.parquet")
    
    # Run the pre-parser service
    df_docs = await preparse_documents(
        parquet_repo=parquet_repo,
        file_path=docs_path,
        limit=limit if limit > 0 else None,
        no_cache=no_cache
    )
    return df_docs


@fixture(scope="session")
def df_docs(fixture_parsed_cache):
    return fixture_parsed_cache


@fixture(scope="session")
def fixture_vector_cache(fixture_parsed_cache, no_cache: bool = False):
    """
    Checks if SQLite db exists and is populated. If not, auto-ingests missing parsers/docs.
    """
    if no_cache and os.path.exists(benchmark_settings.sqlite_cache_path):
        os.remove(benchmark_settings.sqlite_cache_path)
        logger.info(f"Deleted SQLite cache at {benchmark_settings.sqlite_cache_path}")

    core_settings.sqlite_db_path = benchmark_settings.sqlite_cache_path
    sqlite_repo._engine = None  # Clear cached engine

    auto_ingest_vectors(fixture_parsed_cache)


def _get_valid_document_ids_for_parser(parser_name: str) -> Optional[Set[str]]:
    if core_settings.retrieval_backend == "sqlite":
        from matrixcurator.modules.retrieval.repositories.sqlite import get_engine
        from sqlalchemy.orm import Session
        from sqlalchemy import text

        try:
            engine = get_engine()
            with Session(engine) as session:
                result = session.execute(
                    text(
                        "SELECT DISTINCT document_id FROM document_chunks_meta WHERE parser_name = :parser"
                    ),
                    {"parser": parser_name},
                )
                return {str(row[0]) for row in result}
        except Exception as e:
            logger.error(
                f"Failed to query valid documents for parser {parser_name}: {e}"
            )
            return None
    return None


@fixture(scope="session")
def valid_docs_per_parser(fixture_vector_cache):
    return {parser: _get_valid_document_ids_for_parser(parser) for parser in PARSERS}


@fixture(scope="session")
async def fixture_synced_langfuse(skip_sync: bool, lf_client: Any, fixture_parsed_cache):
    if not skip_sync and lf_client:
        await sync_datasets(parquet_repo, dataset_langfuse_repository, lf_client, fixture_parsed_cache)
        setup_evaluators(evaluation_langfuse_repository, lf_client)
    return True
