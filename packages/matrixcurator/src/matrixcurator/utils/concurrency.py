import asyncio
import time
from typing import Any, Optional
from pydantic import BaseModel


class RateLimitConfig(BaseModel):
    per_second: Optional[int] = None
    per_minute: Optional[int] = None
    per_hour: Optional[int] = None


class AsyncRateLimiter:
    """Rate limiter that restricts execution to a maximum number of calls per time period."""

    def __init__(
        self,
        max_calls: Optional[int] = None,
        time_period: float = 1.0,
        settings: Optional[RateLimitConfig] = None,
    ) -> None:
        self.limits: list[tuple[int, float]] = []
        if settings:
            if settings.per_second:
                self.limits.append((settings.per_second, 1.0))
            if settings.per_minute:
                self.limits.append((settings.per_minute, 60.0))
            if settings.per_hour:
                self.limits.append((settings.per_hour, 3600.0))
        elif max_calls is not None:
            self.limits.append((max_calls, time_period))

        self.calls: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token from the rate limiter, sleeping if necessary."""
        if not self.limits:
            return

        async with self._lock:
            while True:
                now = time.monotonic()
                max_sleep = 0.0

                for max_calls, time_period in self.limits:
                    window_start = now - time_period
                    recent_calls = [t for t in self.calls if t > window_start]

                    if len(recent_calls) >= max_calls:
                        oldest_in_window = recent_calls[0]
                        sleep_time = time_period - (now - oldest_in_window)
                        if sleep_time > max_sleep:
                            max_sleep = sleep_time

                if max_sleep > 0:
                    await asyncio.sleep(max_sleep)
                else:
                    break

            now = time.monotonic()
            self.calls.append(now)

            # Cleanup old calls beyond the maximum time period
            max_period = max(limit[1] for limit in self.limits)
            self.calls = [t for t in self.calls if now - t <= max_period]

    @property
    def max_concurrency(self) -> int:
        """Calculate the max concurrency dynamically based on rate limits (burst logic)."""
        if not self.limits:
            return 100  # Arbitrary default if no limits
        
        # Calculate strictest limits per second
        rates = []
        for max_calls, time_period in self.limits:
            rates.append(max_calls / time_period)
        
        strictest_rate = min(rates)
        # Cap to at least 1
        return max(1, int(strictest_rate))


class AsyncConcurrencyManager:
    """Context manager combining asyncio.Semaphore and an optional AsyncRateLimiter."""

    def __init__(
        self, max_concurrent: Optional[int] = None, rate_limiter: Optional[AsyncRateLimiter] = None
    ) -> None:
        if max_concurrent is None:
            if rate_limiter:
                max_concurrent = rate_limiter.max_concurrency
            else:
                max_concurrent = 100
                
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = rate_limiter

    async def __aenter__(self) -> "AsyncConcurrencyManager":
        """Acquire the semaphore and then the rate limiter (if configured)."""
        await self.semaphore.acquire()
        try:
            if self.rate_limiter:
                await self.rate_limiter.acquire()
        except Exception:
            self.semaphore.release()
            raise
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Release the semaphore."""
        self.semaphore.release()
