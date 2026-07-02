import asyncio
import time
from unittest.mock import patch

import pytest
from matrixcurator.utils.concurrency import AsyncConcurrencyManager, AsyncRateLimiter, RateLimitConfig


def test_async_rate_limiter_max_concurrency() -> None:
    # Default fallback
    limiter = AsyncRateLimiter()
    assert limiter.max_concurrency == 100

    # per_second
    config = RateLimitConfig(per_second=5)
    limiter = AsyncRateLimiter(settings=config)
    assert limiter.max_concurrency == 5

    # per_minute (120/60 = 2)
    config = RateLimitConfig(per_minute=120)
    limiter = AsyncRateLimiter(settings=config)
    assert limiter.max_concurrency == 2

    # per_hour (3600/3600 = 1)
    config = RateLimitConfig(per_hour=3600)
    limiter = AsyncRateLimiter(settings=config)
    assert limiter.max_concurrency == 1

    # Mixed tier - takes minimum
    config = RateLimitConfig(per_second=50, per_minute=120)
    limiter = AsyncRateLimiter(settings=config)
    assert limiter.max_concurrency == 2  # 120/min = 2/sec, 50/sec = 50. min is 2.
    
    # Cap to at least 1
    config = RateLimitConfig(per_hour=1)
    limiter = AsyncRateLimiter(settings=config)
    assert limiter.max_concurrency == 1  # 1/3600 = 0.0002, capped to 1

    # Direct params
    limiter = AsyncRateLimiter(max_calls=1, time_period=0.5)
    assert limiter.max_concurrency == 2  # 1 / 0.5 = 2


@pytest.mark.asyncio
async def test_async_rate_limiter_respects_limit() -> None:
    # Allow 2 calls per 0.1 seconds
    limiter = AsyncRateLimiter(max_calls=2, time_period=0.1)

    start_time = time.monotonic()

    # First two should be immediate
    await limiter.acquire()
    await limiter.acquire()

    elapsed = time.monotonic() - start_time
    assert elapsed < 0.05  # Should not have slept

    # Third call should sleep for about 0.1s
    await limiter.acquire()
    
    elapsed = time.monotonic() - start_time
    assert elapsed >= 0.1  # Should have waited for the time period


@pytest.mark.asyncio
async def test_async_rate_limiter_multi_tier() -> None:
    config = RateLimitConfig(per_second=2, per_minute=3)
    limiter = AsyncRateLimiter(settings=config)
    
    # We mock time.monotonic and asyncio.sleep to test the multi-tier logic without actually sleeping for a minute
    now = 100.0
    sleeps = []
    
    async def mock_sleep(s):
        sleeps.append(s)
        nonlocal now
        now += s

    def mock_monotonic():
        return now

    with patch("matrixcurator.utils.concurrency.time.monotonic", side_effect=mock_monotonic):
        with patch("matrixcurator.utils.concurrency.asyncio.sleep", side_effect=mock_sleep):
            # First 2 calls should be immediate (per_second limit reached)
            await limiter.acquire()
            await limiter.acquire()
            assert sum(sleeps) == 0.0
            
            # 3rd call should sleep to satisfy per_second
            await limiter.acquire()
            assert sum(sleeps) == 1.0  # Slept 1s to satisfy per_second=2
            
            # Now we have 3 calls in the last minute.
            # 4th call should sleep to satisfy per_minute
            await limiter.acquire()
            # The oldest of the 3 calls is at time 100.0. Current time is 101.0. 
            # To satisfy per_minute=3, it needs to wait until 100.0 + 60.0 = 160.0.
            # Current time is 101.0, so it sleeps for 59.0s.
            assert sum(sleeps) == 60.0


@pytest.mark.asyncio
async def test_async_concurrency_manager_auto_infer_concurrency() -> None:
    config = RateLimitConfig(per_minute=120)
    limiter = AsyncRateLimiter(settings=config)
    
    # Should automatically infer max_concurrency=2
    manager = AsyncConcurrencyManager(rate_limiter=limiter)
    assert manager.semaphore._value == 2
    
    manager_no_limiter = AsyncConcurrencyManager()
    assert manager_no_limiter.semaphore._value == 100


@pytest.mark.asyncio
async def test_async_concurrency_manager_semaphore() -> None:
    manager = AsyncConcurrencyManager(max_concurrent=1)

    async def worker() -> None:
        async with manager:
            await asyncio.sleep(0.05)

    start_time = time.monotonic()
    
    # Run two tasks, should take at least 0.1s combined due to concurrency limit of 1
    await asyncio.gather(worker(), worker())
    
    elapsed = time.monotonic() - start_time
    assert elapsed >= 0.1


@pytest.mark.asyncio
async def test_async_concurrency_manager_with_rate_limiter() -> None:
    limiter = AsyncRateLimiter(max_calls=1, time_period=0.1)
    manager = AsyncConcurrencyManager(max_concurrent=2, rate_limiter=limiter)

    start_time = time.monotonic()
    
    async def worker() -> None:
        async with manager:
            pass

    # Two tasks, semaphore allows 2 but rate limiter allows 1 per 0.1s
    await asyncio.gather(worker(), worker())
    
    elapsed = time.monotonic() - start_time
    assert elapsed >= 0.1
