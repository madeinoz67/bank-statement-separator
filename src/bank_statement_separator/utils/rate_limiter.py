"""Rate limiting utilities for API calls."""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict

from openai import RateLimitError

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 50
    requests_per_hour: int = 1000
    burst_limit: int = 10
    backoff_min: float = 1.0
    backoff_max: float = 60.0
    backoff_multiplier: float = 2.0


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._lock = threading.Lock()
        self._request_times: list[float] = []
        self._burst_tokens = config.burst_limit

    def acquire(self) -> bool:
        """
        Acquire permission to make a request.

        Returns:
            bool: True if request is allowed, False if rate limited
        """
        with self._lock:
            now = time.time()

            # Clean old requests (sliding window for per-minute limit)
            minute_ago = now - 60
            self._request_times = [t for t in self._request_times if t > minute_ago]

            # Check per-minute limit
            if len(self._request_times) >= self.config.requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded: {len(self._request_times)} requests in last minute "
                    f"(limit: {self.config.requests_per_minute})"
                )
                return False

            # Check burst limit - this is the primary check for immediate requests
            if self._burst_tokens <= 0:
                logger.warning("Burst limit exceeded")
                return False

            # Allow request
            self._request_times.append(now)
            self._burst_tokens -= 1

            return True

    def _replenish_burst_tokens(self, now: float) -> None:
        """Slowly replenish burst tokens over time."""
        # Simple replenishment: add tokens based on time passed
        # This is a simplified implementation
        if self._burst_tokens < self.config.burst_limit:
            self._burst_tokens = min(self.config.burst_limit, self._burst_tokens + 1)

    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics."""
        with self._lock:
            now = time.time()
            minute_ago = now - 60
            recent_requests = len([t for t in self._request_times if t > minute_ago])

            return {
                "requests_last_minute": recent_requests,
                "limit_per_minute": self.config.requests_per_minute,
                "burst_tokens_remaining": self._burst_tokens,
                "burst_limit": self.config.burst_limit,
                "total_requests_tracked": len(self._request_times),
            }


class BackoffStrategy:
    """Exponential backoff strategy for retries."""

    @staticmethod
    def calculate_backoff_delay(attempt: int, base_delay: float = 1.0) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds

        Returns:
            float: Delay in seconds
        """
        delay = base_delay * (2**attempt)
        # Add jitter to prevent thundering herd
        import random

        jitter = random.uniform(0.1, 1.0)
        return min(delay * jitter, 60.0)  # Cap at 60 seconds

    @staticmethod
    def execute_with_backoff(
        func, max_attempts: int = 5, base_delay: float = 1.0, *args, **kwargs
    ):
        """
        Execute function with exponential backoff on rate limit errors.

        Args:
            func: Function to execute
            max_attempts: Maximum number of attempts
            base_delay: Base delay between attempts
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func execution

        Raises:
            RateLimitError: If all attempts fail
            Exception: Other exceptions from func
        """
        last_exception = None

        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    delay = BackoffStrategy.calculate_backoff_delay(attempt, base_delay)
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{max_attempts}), "
                        f"backing off for {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Rate limit error persisted after {max_attempts} attempts"
                    )
                    raise
            except Exception as e:
                # Re-raise non-rate-limit exceptions immediately
                logger.error(f"Non-rate-limit error in {func.__name__}: {e}")
                raise

        # This should not be reached, but just in case
        if last_exception:
            raise last_exception


def load_rate_limit_config_from_env() -> RateLimitConfig:
    """Load rate limit configuration from environment variables."""
    import os

    return RateLimitConfig(
        requests_per_minute=int(os.getenv("OPENAI_REQUESTS_PER_MINUTE", "50")),
        requests_per_hour=int(os.getenv("OPENAI_REQUESTS_PER_HOUR", "1000")),
        burst_limit=int(os.getenv("OPENAI_BURST_LIMIT", "10")),
        backoff_min=float(os.getenv("OPENAI_BACKOFF_MIN", "1.0")),
        backoff_max=float(os.getenv("OPENAI_BACKOFF_MAX", "60.0")),
        backoff_multiplier=float(os.getenv("OPENAI_BACKOFF_MULTIPLIER", "2.0")),
    )
