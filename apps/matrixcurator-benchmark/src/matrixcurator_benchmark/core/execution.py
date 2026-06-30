"""Handles permutation expansion and single-execution logic."""

import inspect
import itertools
import logging
from typing import Any, Callable, Dict, Generator

from matrixcurator_benchmark.core.exceptions import FailBenchmark, SkipBenchmark

logger = logging.getLogger(__name__)


def expand_permutations(
    func: Callable[..., Any],
) -> Generator[Dict[str, Any], None, None]:
    """
    Yield a dict of kwargs for every combination of @parametrize stacked on the function.
    """
    if not hasattr(func, "__benchmark_metadata__") or "parametrizations" not in getattr(
        func, "__benchmark_metadata__"
    ):
        yield {}
        return

    parametrizations = getattr(func, "__benchmark_metadata__")["parametrizations"]

    # Process from top to bottom decorator
    param_lists = []
    for param in parametrizations:
        argnames = [name.strip() for name in param["argnames"].split(",")]
        argvalues = param["argvalues"]

        current_param_list = []
        for value in argvalues:
            if len(argnames) == 1:
                current_param_list.append({argnames[0]: value})
            else:
                current_param_list.append(dict(zip(argnames, value)))
        param_lists.append(current_param_list)

    # Cartesian product of all parametrizations
    for combination in itertools.product(*param_lists):
        merged_kwargs: Dict[str, Any] = {}
        for d in combination:
            merged_kwargs.update(d)
        yield merged_kwargs


async def execute_single_run(func: Callable[..., Any], kwargs: Dict[str, Any]) -> Any:
    """
    Run the single async function. Intercepts SkipBenchmark and FailBenchmark for proper logging.
    """
    try:
        if inspect.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            return func(**kwargs)
    except SkipBenchmark as e:
        logger.debug("Skipped benchmark: %s - %s", func.__name__, str(e))
        raise
    except FailBenchmark as e:
        logger.error("Failed benchmark: %s - %s", func.__name__, str(e))
        raise
    except Exception:
        logger.exception("Error in benchmark: %s", func.__name__)
        raise
