"""Timeout utilities for resource-limited operations."""

import signal
import threading
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def with_timeout(
    func: Callable[..., T], timeout_seconds: int, *args: Any, **kwargs: Any
) -> T:
    """Execute function with timeout protection (cross-platform).

    Args:
        func: Function to execute with timeout.
        timeout_seconds: Maximum execution time in seconds.
            If 0 or negative, no timeout is applied.
        *args: Positional arguments to pass to func.
        **kwargs: Keyword arguments to pass to func.

    Returns:
        Return value from func.

    Raises:
        TimeoutError: If function execution exceeds timeout_seconds.

    Note:
        - On Unix/macOS: Uses signal.SIGALRM for reliable timeout
        - On Windows: Uses threading (may not interrupt native C code)
    """
    if timeout_seconds <= 0:
        return func(*args, **kwargs)

    # Try signal-based timeout (Unix/macOS)
    if hasattr(signal, "SIGALRM"):

        def timeout_handler(signum: int, frame: Any) -> None:
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")

        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        try:
            return func(*args, **kwargs)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Fallback for Windows: use threading
        result: list[T | None] = [None]
        exception: list[Exception | None] = [None]

        def target() -> None:
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        if exception[0]:
            raise exception[0]
        return result[0]  # type: ignore[return-value]
