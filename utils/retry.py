"""
Retry decorator with exponential backoff and jitter.

Provides a configurable @retry decorator for wrapping functions that may
fail transiently (network calls, API requests, file I/O under contention).

Usage:
    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(ConnectionError,))
    def fetch_data(url: str) -> dict:
        ...
"""

import functools
import logging
import random
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator that retries a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of times to call the function (>= 1).
        delay: Initial delay in seconds before the first retry.
        backoff: Multiplier applied to the delay after each retry.
        exceptions: Tuple of exception types that trigger a retry.

    Returns:
        Decorated function that transparently retries on failure.

    Raises:
        The original exception if all attempts are exhausted.
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    if delay < 0:
        raise ValueError("delay must be >= 0")
    if backoff < 1:
        raise ValueError("backoff must be >= 1")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: BaseException | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc

                    if attempt == max_attempts:
                        logger.error(
                            "Function '%s' failed after %d/%d attempts: %s",
                            func.__name__,
                            attempt,
                            max_attempts,
                            exc,
                        )
                        raise

                    # Random jitter between 0 and 1 second
                    jitter = random.uniform(0, 1.0)  # noqa: S311
                    sleep_time = current_delay + jitter

                    logger.warning(
                        "Function '%s' failed on attempt %d/%d: %s — "
                        "retrying in %.2fs",
                        func.__name__,
                        attempt,
                        max_attempts,
                        exc,
                        sleep_time,
                    )

                    time.sleep(sleep_time)
                    current_delay *= backoff

            # Should never reach here, but satisfy the type checker
            raise last_exception  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator


# ──────────────────────────────────────────────────────────────────────
# Demo / self-test
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )

    call_count = 0

    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(RuntimeError,))
    def flaky_function() -> str:
        """Simulates a function that fails twice then succeeds."""
        global call_count  # noqa: PLW0603
        call_count += 1
        if call_count < 3:
            raise RuntimeError(f"Simulated failure #{call_count}")
        return "Success on attempt 3!"

    result = flaky_function()
    logger.info("Result: %s", result)

    # Demonstrate total failure
    logger.info("--- Now demonstrating total failure ---")

    @retry(max_attempts=2, delay=0.5, backoff=1.0, exceptions=(ValueError,))
    def always_fails() -> None:
        """Always raises ValueError."""
        raise ValueError("Permanent error")

    try:
        always_fails()
    except ValueError as exc:
        logger.info("Caught expected final exception: %s", exc)
