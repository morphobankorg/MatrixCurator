import asyncio
import langfuse
import structlog
from typing import Callable, Any

from matrixcurator_benchmark.exceptions import SkipBenchmark, FailBenchmark

logger = structlog.get_logger(__name__)


async def run_dataset_benchmark(
    dataset_name: str,
    run_name: str,
    task_fn: Callable[..., Any],
    limit: int,
    workers: int,
    evaluators: list[Any] | None = None,
    filter_fn: Callable[[Any], bool] | None = None,
) -> None:
    """Executes a benchmark over a Langfuse dataset using Langfuse Experiments API.

    Args:
        dataset_name (str): The name of the Langfuse dataset to run against.
        run_name (str): The name for this benchmark run/experiment.
        task_fn (Callable): The function conforming to TaskFunction protocol to execute for each item.
        limit (int): Maximum number of unique documents to process.
        workers (int): Number of concurrent tasks.
        evaluators (list, optional): Optional list of client-side evaluators.
        filter_fn (Callable, optional): Optional function to pre-filter items.
    """
    logger.info("Starting benchmark run", run_name=run_name, dataset_name=dataset_name)
    lanfuse_client = langfuse.Langfuse()

    try:
        logger.debug("Fetching dataset from Langfuse")
        dataset = lanfuse_client.get_dataset(dataset_name)
    except Exception as e:
        logger.error("Failed to fetch dataset", dataset_name=dataset_name, exc_info=True)
        return

    items = list(dataset.items) if not isinstance(dataset.items, list) else dataset.items
    
    if not items:
        logger.warning("Dataset has 0 items!", dataset_name=dataset_name)
        return

    # Filter dataset.items based on filter_fn and limit (applying limit uniquely by document_id).
    filtered_items = []
    seen_docs = set()
    for item in items:
        if filter_fn and not filter_fn(item):
            continue

        doc_id = None
        if isinstance(item.input, dict):
            doc_id = item.input.get("document_id")
        elif hasattr(item.input, "document_id"):
            doc_id = getattr(item.input, "document_id")
        elif isinstance(item.input, str):
            import json
            try:
                parsed = json.loads(item.input)
                if isinstance(parsed, dict):
                    doc_id = parsed.get("document_id")
            except Exception:
                pass

        if doc_id:
            seen_docs.add(doc_id)

        if limit > 0 and len(seen_docs) > limit:
            break

        filtered_items.append(item)

    logger.info(
        "Filtered benchmark items",
        filtered_count=len(filtered_items),
        unique_documents=len(seen_docs),
        total_items=len(items),
    )

    if not filtered_items:
        logger.warning("No items left after filtering!", dataset_name=dataset_name)
        return

    try:
        await asyncio.to_thread(
            lanfuse_client.run_experiment,
            name=run_name,
            data=filtered_items,
            task=task_fn,
            evaluators=evaluators or [],
            max_concurrency=workers,
        )
    except Exception as e:
        logger.exception("Failed to run experiment", run_name=run_name, exc_info=e)
        
    logger.info("Finished benchmark run", run_name=run_name)
