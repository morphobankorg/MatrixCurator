import pandas as pd
import langfuse
import structlog
from typing import Any, Dict

from matrixcurator_benchmark.modules.dataset import services as dataset_services
from matrixcurator_benchmark.modules.dataset.repositories import (
    parquet as parquet_repository,
    langfuse as dataset_langfuse_repository,
)
from matrixcurator_benchmark.modules.evaluation import services as evaluation_services
from matrixcurator_benchmark.modules.evaluation.repositories import (
    langfuse as evaluation_langfuse_repository,
)
from matrixcurator_benchmark.modules.retrieval import services as retrieval_services

logger = structlog.get_logger(__name__)

async def bootstrap_environment(
    limit: int, skip_sync: bool, no_cache: bool, targets: list[str] = None
) -> Dict[str, Any]:
    """Prepares and caches datasets before benchmarking.
    
    Args:
        limit (int): The maximum number of documents to parse/sync.
        skip_sync (bool): If True, skip syncing datasets and evaluators to Langfuse.
        no_cache (bool): If True, force reparsing of documents.
        targets (list[str]): The benchmark suites being targeted.
        
    Returns:
        Dict[str, Any]: A mapping of document_id -> row dictionary.
    """
    logger.info(
        "Bootstrapping environment...",
        targets=targets,
        limit=limit,
        skip_sync=skip_sync,
        no_cache=no_cache,
    )
    
    file_path = "apps/matrixcurator-benchmark/src/matrixcurator_benchmark/data/documents.parquet"
    parsed_docs = await dataset_services.preparse_documents(
        parquet_repository=parquet_repository,
        file_path=file_path,
        limit=limit,
        no_cache=no_cache
    )
    
    docs_dict = {
        row.get("id", row.get("document_id")): row 
        for row in parsed_docs
    }
    
    if not skip_sync:
        logger.info("Syncing datasets to Langfuse...")
        lanfuse_client = langfuse.Langfuse()
        
        await dataset_services.sync_datasets(
            parquet_repository=parquet_repository,
            langfuse_repository=dataset_langfuse_repository,
            client=lanfuse_client,
            docs=parsed_docs
        )
        
        if targets and ("agents" in targets or "evaluation" in targets):
            logger.info("Setting up evaluators...")
            evaluation_services.setup_evaluators(
                langfuse_repository=evaluation_langfuse_repository,
                client=lanfuse_client
            )
        else:
            logger.info("Skipping evaluators setup based on targets.")
    
    if targets and ("retrieval" in targets or "agents" in targets):
        logger.info("Auto ingesting vectors...")
        df_docs = pd.DataFrame(parsed_docs)
        retrieval_services.auto_ingest_vectors(df_docs)
    else:
        logger.info("Skipping vector ingestion based on targets.")
    
    logger.info("Environment bootstrapped successfully.")
    return docs_dict
