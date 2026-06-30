import os
import asyncio
from typing import Set, Tuple
import pandas as pd
from tqdm import tqdm
from lume import structlog

from matrixcurator.config.main import settings as core_settings
from matrixcurator_benchmark.config.main import settings as benchmark_settings
from matrixcurator.modules.retrieval.services import embed_and_store_chunks, chunk_text
import matrixcurator.modules.retrieval.repositories.sqlite as sqlite_repo

logger = structlog.get_logger(__name__)
PARSERS = ["docling", "pymupdf", "docx", "txt"]

def auto_ingest_vectors(df_docs: pd.DataFrame) -> None:
    """
    Checks if SQLite db exists and is populated. If not, auto-ingests missing parsers/docs from the dataframe.
    """
    if core_settings.retrieval_backend != "sqlite":
        return

    from matrixcurator.modules.retrieval.repositories.sqlite import get_engine
    from sqlalchemy.orm import Session
    from sqlalchemy import text

    existing_combinations: Set[Tuple[str, str]] = set()
    try:
        engine = get_engine()
        with Session(engine) as session:
            result = session.execute(
                text("SELECT DISTINCT document_id, parser_name FROM document_chunks_meta")
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
        parses = row.get("text")

        if not parses or not isinstance(parses, list):
            logger.warning(f"Text column empty or invalid for document {doc_id_str}, skipping vector ingestion.")
            continue

        try:
            for parse_data in parses:
                if not isinstance(parse_data, dict):
                    continue
                
                parser_name = parse_data.get("parser")
                if not parser_name or parser_name not in PARSERS:
                    continue

                if (doc_id_str, parser_name) in existing_combinations:
                    continue # Already ingested

                pages = parse_data.get("pages") or []
                full_text = "\n\n".join([page.get("content", "") for page in pages if isinstance(page, dict)])
                if not full_text.strip() or full_text.startswith("Error:"):
                    continue

                chunks = chunk_text(
                    text=full_text, document_id=doc_id_str, parser_name=parser_name
                )

                if not chunks:
                    continue

                tqdm.write(f"Ingesting {len(chunks)} chunks for document {doc_id_str} with parser {parser_name}")
                
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    asyncio.run(embed_and_store_chunks(chunks))
                else:
                    asyncio.run(embed_and_store_chunks(chunks))
                    
                existing_combinations.add((doc_id_str, parser_name))
        except Exception as e:
            logger.exception(f"Error auto-ingesting document {doc_id_str}: {e}")
