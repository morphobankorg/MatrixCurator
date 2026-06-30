# src/benchmark/core/runner.py
"""Master orchestrator module for benchmark discovery and execution."""

import asyncio
import importlib
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict

from lume.integrations.langfuse import langfuse  # type: ignore
from langfuse import observe

from src.benchmark.core.exceptions import FailBenchmark, SkipBenchmark
from src.benchmark.core.execution import execute_single_run, expand_permutations
from src.benchmark.core.fixtures import _SESSION_CACHE, resolve_fixtures
from src.benchmark.core.registry import get_benchmarks

logger = logging.getLogger(__name__)


def discover_benchmarks(path: str, filters: list[str] = None) -> None:
    """
    Iterate `path` looking for files `benchmark_*.py`.
    Uses `importlib` to import them, triggering the decorators.
    """
    base_path = Path(path).resolve()
    if not base_path.exists():
        logger.error("Path %s does not exist.", base_path)
        return

    sys.path.insert(0, str(base_path.parent))

    conf_path = base_path / "confbenchmark.py"
    if conf_path.exists():
        module_name = conf_path.relative_to(base_path.parent).with_suffix("").parts
        module_path = ".".join(module_name)
        try:
            importlib.import_module(module_path)
            logger.info("Imported config module %s", module_path)
        except Exception as e:
            logger.exception("Failed to import %s: %s", module_path, e)

    for item in base_path.rglob("benchmark_*.py"):
        if item.is_file():
            if filters and not any(f in item.name for f in filters):
                continue
            # Get module path relative to the directory above base_path to match sys.path insertion
            module_name = item.relative_to(base_path.parent).with_suffix("").parts
            module_path = ".".join(module_name)
            try:
                importlib.import_module(module_path)
                logger.info("Discovered benchmarks in %s", module_path)
            except Exception as e:
                logger.exception("Failed to import %s: %s", module_path, e)

    sys.path.pop(0)


async def run_all(workers: int, limit: int, skip_sync: bool) -> None:
    """
    Execute all discovered benchmarks with the specified concurrency limit.
    """
    # Initialize Langfuse client
    lf_client = langfuse.Langfuse() if hasattr(langfuse, "Langfuse") else langfuse

    # Expose global configurations for granular fixtures to use
    _SESSION_CACHE["skip_sync"] = skip_sync
    _SESSION_CACHE["limit"] = limit
    _SESSION_CACHE["lf_client"] = lf_client

    benchmarks = get_benchmarks()
    semaphore = asyncio.Semaphore(workers)

    async def run_item(
        func: Callable[..., Any],
        kwargs: Dict[str, Any],
        item_data: Any,
        dataset_name: str,
        dataset_item: Any,
    ) -> None:
        async with semaphore:
            trace_name = f"{func.__name__}_{dataset_name}"

            captured_output = {"value": None}

            def langfuse_trace(output: Any = None) -> Any:
                import langfuse as lf
                client = lf.get_client()
                if output is not None:
                    captured_output["value"] = output
                    try:
                        client.set_current_trace_io(output=output)
                    except Exception as e:
                        logger.warning(f"Failed to update trace IO: {e}")
                class DummyTrace:
                    @property
                    def id(self):
                        try:
                            return client.get_current_trace_id()
                        except Exception:
                            return None
                return DummyTrace()

            # Inject item data and trace
            extra_kwargs = {
                "dataset_item": dataset_item,
                "item": item_data,
                "langfuse_trace": langfuse_trace,
                **kwargs,
            }

            try:
                resolved_kwargs = await resolve_fixtures(
                    func, _SESSION_CACHE, extra_kwargs
                )
            except Exception as e:
                logger.error("Error resolving fixtures for %s: %s", func.__name__, e)
                return

            if hasattr(func, "__benchmark_metadata__"):
                skip_if = func.__benchmark_metadata__.get("skip_if")
                if skip_if and skip_if(resolved_kwargs):
                    logger.debug("Skipped benchmark: %s - pre-execution condition met", func.__name__)
                    return

            @observe(name=trace_name)
            async def _execute_traced_item():
                try:
                    await execute_single_run(func, resolved_kwargs)

                    # Create a trace run item link
                    import langfuse as lf
                    client = lf.get_client()
                    
                    try:
                        trace_id = client.get_current_trace_id()
                    except Exception:
                        trace_id = None
                        
                    if trace_id:
                        lf_client.api.dataset_run_items.create(
                            run_name=trace_name,
                            dataset_item_id=dataset_item.id,
                            trace_id=trace_id
                        )
                    return captured_output["value"]

                except SkipBenchmark:
                    pass
                except FailBenchmark:
                    pass
                except Exception as e:
                    logger.error("Unexpected error in %s: %s", func.__name__, e)

            await _execute_traced_item()

    tasks = []

    for bench in benchmarks:
        func = bench["func"]
        metadata = bench["metadata"]
        dataset_name = metadata.get("dataset_name", "default")

        # Fetch the dataset from Langfuse
        try:
            dataset = lf_client.get_dataset(dataset_name)
            items = getattr(dataset, "items", [])
        except Exception as e:
            logger.error("Could not fetch dataset %s: %s", dataset_name, e)
            continue

        if limit > 0:
            items = items[:limit]

        for item in items:
            item_input = getattr(item, "input", {})

            for kwargs in expand_permutations(func):
                tasks.append(run_item(func, kwargs, item_input, dataset_name, item))

    if tasks:
        await asyncio.gather(*tasks)

    # Ensure all traces flush
    lf_client.flush()
