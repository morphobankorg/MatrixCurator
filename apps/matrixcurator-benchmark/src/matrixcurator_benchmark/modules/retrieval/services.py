import os
import asyncio
import numpy as np
from typing import Set, Tuple
import pandas as pd
from tqdm import tqdm
from lume import structlog
import ast

from matrixcurator.config.main import settings as core_settings
from matrixcurator_benchmark.config.main import settings as benchmark_settings
from matrixcurator.modules.retrieval.services import vectorize_document

logger = structlog.get_logger(__name__)


def auto_ingest_vectors(df_docs: pd.DataFrame, no_cache: bool = False) -> None:
    """
    Checks if SQLite db exists and is populated. If not, auto-ingests missing parsers/docs from the dataframe.
    """
    if core_settings.retrieval_backend != "sqlite":
        return

    from matrixcurator.modules.retrieval.repositories.sqlite import get_engine, delete_chunks_by_document
    from sqlalchemy.orm import Session
    from sqlalchemy import text

    if no_cache and not df_docs.empty:
        doc_ids = []
        for _, row in df_docs.iterrows():
            doc_id = row.get("id", row.get("document_id"))
            if doc_id:
                doc_ids.append(str(doc_id))
        
        if doc_ids:
            logger.info("no_cache is True: Deleting existing vector chunks for current documents")
            try:
                delete_chunks_by_document(doc_ids)
            except Exception as e:
                logger.error(f"Failed to delete existing vector chunks: {e}")

    existing_combinations: Set[Tuple[str, str]] = set()
    try:
        engine = get_engine()
        with Session(engine) as session:
            result = session.execute(
                text(
                    "SELECT DISTINCT document_id, parser_name FROM document_chunks_meta"
                )
            )
            for row in result:
                existing_combinations.add((str(row[0]), str(row[1])))
    except Exception as e:
        logger.info(f"Database validation failed, proceeding with auto-ingestion: {e}")

    if df_docs.empty:
        return

    limit_env = os.environ.get("BENCHMARK_DOCUMENT_LIMIT", "none")
    if limit_env.lower() not in ["all", "none", "0"]:
        try:
            limit = int(limit_env)
            df_docs = df_docs.head(limit)
        except ValueError:
            pass

    for _, row in tqdm(
        df_docs.iterrows(), total=len(df_docs), desc="Auto-Ingesting SQLite Vectors"
    ):
        doc_id = row.get("id", row.get("document_id"))
        if not doc_id:
            continue

        doc_id_str = str(doc_id)

        # Check if docling variants are already ingested
        if (doc_id_str, "docling") in existing_combinations and (
            doc_id_str,
            "docling_relevant",
        ) in existing_combinations:
            continue

        parses = row.get("text")
        if not parses or not isinstance(parses, list):
            logger.warning(
                f"Text column empty or invalid for document {doc_id_str}, skipping vector ingestion."
            )
            continue

        raw_pages = row.get("pages")
        pages = None

        def is_valid_pages(val):
            if val is None:
                return False
            if isinstance(val, float) and pd.isna(val):
                return False
            return True

        if is_valid_pages(raw_pages):
            if isinstance(raw_pages, str):
                try:
                    parsed = ast.literal_eval(raw_pages)
                    if isinstance(parsed, list):
                        pages = [int(p) for p in parsed]
                except (ValueError, SyntaxError):
                    logger.warning(
                        f"Failed to parse pages string '{raw_pages}' for doc {doc_id_str}"
                    )
            elif isinstance(raw_pages, (list, np.ndarray)):
                pages = [int(p) for p in raw_pages]

        logger.info(
            "Parsed relevant pages for ingestion",
            document_id=doc_id_str,
            raw_pages=raw_pages,
            parsed_pages=pages,
        )

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                import nest_asyncio

                nest_asyncio.apply()
                asyncio.run(vectorize_document(doc_id_str, parses, pages))
            else:
                asyncio.run(vectorize_document(doc_id_str, parses, pages))

            existing_combinations.add((doc_id_str, "docling"))
            existing_combinations.add((doc_id_str, "docling_relevant"))
        except Exception as e:
            logger.exception(f"Error auto-ingesting document {doc_id_str}: {e}")
