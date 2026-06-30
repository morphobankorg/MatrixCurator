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
    logger.info("Starting benchmark run: %s on dataset %s", run_name, dataset_name)
    lanfuse_client = langfuse.Langfuse()

    try:
        dataset = lanfuse_client.get_dataset(dataset_name)
    except Exception as e:
        logger.error("Failed to fetch dataset %s: %s", dataset_name, str(e))
        return

    items = dataset.items

    # Filter dataset.items based on limit (applying limit uniquely by document_id).
    filtered_items = []
    seen_docs = set()
    for item in items:
        # Extract document_id. Handle both dict access or attribute access if needed.
        # Langfuse DatasetItem input usually parses to a dict.
        doc_id = None
        if isinstance(item.input, dict):
            doc_id = item.input.get("document_id")

        if doc_id:
            seen_docs.add(doc_id)

        if limit > 0 and len(seen_docs) > limit:
            break

        filtered_items.append(item)

    logger.info(
        "Filtered to %d items (from %d unique documents) out of %d total items",
        len(filtered_items),
        len(seen_docs),
        len(items),
    )

    semaphore = asyncio.Semaphore(workers)

    async def _run(item: Any) -> None:
        async with semaphore:
            trace = lanfuse_client.trace(name=run_name, tags=[run_name])
            try:
                await process_fn(item, trace)
                item.link(trace, run_name)
            except SkipBenchmark:
                # Ignore and do NOT link
                pass
            except FailBenchmark as e:
                logger.error(
                    "Benchmark failed for item %s: %s",
                    getattr(item, "id", "unknown"),
                    str(e),
                )
                trace.update(level="ERROR", status_message=str(e))
                item.link(trace, run_name)
            except Exception as e:
                logger.exception(
                    "Unexpected error for item %s", getattr(item, "id", "unknown")
                )
                trace.update(level="ERROR", status_message=str(e))
                item.link(trace, run_name)

    await asyncio.gather(*[_run(item) for item in filtered_items])
    logger.info("Finished benchmark run: %s", run_name)
