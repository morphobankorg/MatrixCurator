"""Global state container for discovery of benchmarks and fixtures."""

from typing import Any, Callable, Dict, List

BENCHMARKS: List[Dict[str, Any]] = []
FIXTURES: Dict[str, Dict[str, Any]] = {}


def add_benchmark(func: Callable[..., Any], metadata: Dict[str, Any]) -> None:
    """Register a new benchmark function."""
    BENCHMARKS.append({"func": func, "metadata": metadata})


def add_fixture(name: str, func: Callable[..., Any], scope: str) -> None:
    """Register a new fixture function."""
    FIXTURES[name] = {"func": func, "scope": scope}


def get_benchmarks() -> List[Dict[str, Any]]:
    """Retrieve all registered benchmarks."""
    return BENCHMARKS


def get_fixtures() -> Dict[str, Dict[str, Any]]:
    """Retrieve all registered fixtures."""
    return FIXTURES
