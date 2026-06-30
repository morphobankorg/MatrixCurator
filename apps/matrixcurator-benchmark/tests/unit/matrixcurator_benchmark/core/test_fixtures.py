import pytest
from unittest.mock import patch

from matrixcurator_benchmark.core.fixtures import resolve_fixtures

@pytest.fixture
def mock_get_fixtures():
    with patch("matrixcurator_benchmark.core.fixtures.get_fixtures", spec=True) as mock:
        yield mock

@pytest.mark.asyncio
async def test_resolve_fixtures_basic(mock_get_fixtures):
    def fix1():
        return "val1"
        
    async def fix2(fix1):
        return f"{fix1}_val2"
        
    mock_get_fixtures.return_value = {
        "fix1": {"func": fix1, "scope": "function"},
        "fix2": {"func": fix2, "scope": "function"},
    }
    async def target(fix2, extra_arg):
        pass

    session_cache = {}
    extra_kwargs = {"extra_arg": "extra"}

    resolved = await resolve_fixtures(target, session_cache, extra_kwargs)
    
    assert resolved == {
        "extra_arg": "extra",
        "fix2": "val1_val2"
    }

@pytest.mark.asyncio
async def test_resolve_fixtures_session_cache(mock_get_fixtures):
    call_count = 0
    def session_fix():
        nonlocal call_count
        call_count += 1
        return "session_val"

    mock_get_fixtures.return_value = {
        "session_fix": {"func": session_fix, "scope": "session"},
    }

    def target1(session_fix):
        pass
        
    def target2(session_fix):
        pass

    session_cache = {}
    
    res1 = await resolve_fixtures(target1, session_cache)
    res2 = await resolve_fixtures(target2, session_cache)
    
    assert res1["session_fix"] == "session_val"
    assert res2["session_fix"] == "session_val"
    assert call_count == 1
    assert session_cache["session_fix"] == "session_val"

@pytest.mark.asyncio
async def test_resolve_fixtures_non_fixture_session_vars(mock_get_fixtures):
    """
    Test that configuration variables injected into session_cache
    (which are not actual registered fixtures) are properly resolved.
    """
    mock_get_fixtures.return_value = {}

    def target(limit: int, skip_sync: bool):
        pass

    session_cache = {"limit": 10, "skip_sync": True}
    
    resolved = await resolve_fixtures(target, session_cache)
    
    assert resolved == {"limit": 10, "skip_sync": True}

@pytest.mark.asyncio
async def test_resolve_fixtures_concurrency(mock_get_fixtures):
    import asyncio
    
    call_count = 0
    
    async def slow_session_fix():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)
        return "slow_val"

    mock_get_fixtures.return_value = {
        "slow_session_fix": {"func": slow_session_fix, "scope": "session"},
    }

    async def target(slow_session_fix):
        return slow_session_fix

    session_cache = {}
    
    from matrixcurator_benchmark.core.fixtures import _SESSION_LOCKS
    _SESSION_LOCKS.clear()

    # Launch 10 tasks concurrently
    tasks = [resolve_fixtures(target, session_cache) for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # All should return the same resolved args dict
    for res in results:
        assert res["slow_session_fix"] == "slow_val"
        
    # The fixture should have been executed exactly once
    assert call_count == 1
    assert session_cache["slow_session_fix"] == "slow_val"
