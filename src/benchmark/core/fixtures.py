# src/benchmark/core/fixtures.py
"""Dependency injection engine for benchmarks."""

import asyncio
import inspect
from typing import Any, Callable, Dict

from src.benchmark.core.registry import get_fixtures

_SESSION_CACHE: Dict[str, Any] = {}
_SESSION_LOCKS: Dict[str, asyncio.Lock] = {}


async def resolve_fixtures(
    func: Callable[..., Any],
    session_cache: Dict[str, Any],
    extra_kwargs: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Resolves dependencies recursively for a given function.
    Manages caching for scope="session".
    """
    if extra_kwargs is None:
        extra_kwargs = {}

    sig = inspect.signature(func)
    fixtures = get_fixtures()
    resolved_kwargs: Dict[str, Any] = {}

    for param_name in sig.parameters:
        if param_name in extra_kwargs:
            resolved_kwargs[param_name] = extra_kwargs[param_name]
            continue

        if param_name in session_cache and param_name not in fixtures:
            resolved_kwargs[param_name] = session_cache[param_name]
            continue

        if param_name in fixtures:
            fixture_info = fixtures[param_name]
            fixture_func = fixture_info["func"]
            scope = fixture_info["scope"]

            if scope == "session" and param_name in session_cache:
                resolved_kwargs[param_name] = session_cache[param_name]
                continue

            if scope == "session":
                if param_name not in _SESSION_LOCKS:
                    _SESSION_LOCKS[param_name] = asyncio.Lock()
                    
                async with _SESSION_LOCKS[param_name]:
                    if param_name in session_cache:
                        resolved_kwargs[param_name] = session_cache[param_name]
                        continue
                        
                    # Recursively resolve dependencies for this fixture
                    fixture_kwargs = await resolve_fixtures(
                        fixture_func, session_cache, extra_kwargs
                    )

                    if inspect.iscoroutinefunction(fixture_func):
                        result = await fixture_func(**fixture_kwargs)
                    else:
                        result = fixture_func(**fixture_kwargs)

                    session_cache[param_name] = result
                    resolved_kwargs[param_name] = result
            else:
                # Recursively resolve dependencies for this fixture
                fixture_kwargs = await resolve_fixtures(
                    fixture_func, session_cache, extra_kwargs
                )

                if inspect.iscoroutinefunction(fixture_func):
                    result = await fixture_func(**fixture_kwargs)
                else:
                    result = fixture_func(**fixture_kwargs)

                resolved_kwargs[param_name] = result

    return resolved_kwargs
