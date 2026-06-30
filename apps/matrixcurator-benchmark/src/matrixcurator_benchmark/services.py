import asyncio
import langfuse
import structlog
from typing import Callable, Any

from matrixcurator_benchmark.exceptions import SkipBenchmark, FailBenchmark

logger = structlog.get_logger(__name__)


async def run_dataset_benchmark(
    dataset_name: str,
    run_name: str,
    process_fn: Callable[[Any, Any], Any],
    limit: int,
    workers: int,
) -> None:
    """Executes a benchmark over a Langfuse dataset.

    Args:
        dataset_name (str): The name of the Langfuse dataset to run against.
        run_name (str): The name for this benchmark run/trace.
        process_fn (Callable): The async function to execute for each item. Must take (item, trace).
        limit (int): Maximum number of unique documents to process.
        workers (int): Number of concurrent tasks.
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

    # Filter dataset.items based on limit (applying limit uniquely by document_id).
    filtered_items = []
    seen_docs = set()
    for item in items:
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

    semaphore = asyncio.Semaphore(workers)

    async def _run(item: Any, index: int) -> None:
        async with semaphore:
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

            item_id = getattr(item, "id", "unknown")
            logger.info("Processing benchmark item", item_index=index + 1, total_items=len(filtered_items), document_id=doc_id, item_id=item_id)
            
            context_manager = lanfuse_client.start_as_current_observation(
                name=run_name, as_type="span", input=item.input
            )
            
            if not context_manager:
                return

            with context_manager as trace:
                try:
                    await process_fn(item, trace)
                    
                    await asyncio.to_thread(
                        lanfuse_client.api.dataset_run_items.create,
                        run_name=run_name,
                        dataset_item_id=item.id,
                        trace_id=trace.trace_id,
                        observation_id=trace.id,
                    )
                except SkipBenchmark:
                    pass
                except FailBenchmark as e:
                    logger.error(
                        "Benchmark failed for item",
                        item_id=item_id,
                        document_id=doc_id,
                        error=str(e),
                    )
                    error_msg = f"Error: {str(e)}"
                    trace.update(level="ERROR", status_message=str(e), output=error_msg)
                    await asyncio.to_thread(
                        lanfuse_client.api.dataset_run_items.create,
                        run_name=run_name,
                        dataset_item_id=item.id,
                        trace_id=trace.trace_id,
                        observation_id=trace.id,
                    )
                except Exception as e:
                    logger.exception(
                        "Unexpected error for item",
                        item_id=item_id,
                        document_id=doc_id,
                    )
                    error_msg = f"Error: {str(e)}"
                    trace.update(level="ERROR", status_message=str(e), output=error_msg)
                    await asyncio.to_thread(
                        lanfuse_client.api.dataset_run_items.create,
                        run_name=run_name,
                        dataset_item_id=item.id,
                        trace_id=trace.trace_id,
                        observation_id=trace.id,
                    )

    await asyncio.gather(*[_run(item, index) for index, item in enumerate(filtered_items)])
    logger.info("Finished benchmark run", run_name=run_name)
