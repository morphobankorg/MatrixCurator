# src/benchmark/core/decorators.py
"""Syntactic sugar for defining tests and fixtures."""

import functools
from typing import Any, Callable, List, Optional

from src.benchmark.core.registry import add_benchmark, add_fixture


def benchmark(
    dataset_name: str = "default",
    skip_if: Optional[Callable[[Any], bool]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Flag an async function as a benchmark."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not hasattr(func, "__benchmark_metadata__"):
            func.__benchmark_metadata__ = {}  # type: ignore

        func.__benchmark_metadata__["dataset_name"] = dataset_name  # type: ignore
        func.__benchmark_metadata__["skip_if"] = skip_if  # type: ignore

        add_benchmark(func, func.__benchmark_metadata__)  # type: ignore

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def parametrize(
    argnames: str, argvalues: List[Any]
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Parse string argnames and store them as metadata for execution expansion."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not hasattr(func, "__benchmark_metadata__"):
            func.__benchmark_metadata__ = {}  # type: ignore

        if "parametrizations" not in func.__benchmark_metadata__:  # type: ignore
            func.__benchmark_metadata__["parametrizations"] = []  # type: ignore

        func.__benchmark_metadata__["parametrizations"].append(
            {  # type: ignore
                "argnames": argnames,
                "argvalues": argvalues,
            }
        )

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def fixture(
    scope: str = "function", name: Optional[str] = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a function (sync or async) as a dependency."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        fixture_name = name if name else func.__name__
        add_fixture(fixture_name, func, scope)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator
