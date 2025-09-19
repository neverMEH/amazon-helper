"""
Retry handler for AMC API calls with exponential backoff
"""

import time
import random
import logging
from typing import Any, Callable, Optional, Tuple, Dict
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class RetryHandler:
    """
    Handles retry logic for AMC API calls with exponential backoff
    """

    # Error codes/statuses that should trigger retry
    RETRYABLE_STATUS_CODES = [
        429,  # Too Many Requests (rate limit)
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    ]

    # Error codes that should NOT be retried
    NON_RETRYABLE_STATUS_CODES = [
        400,  # Bad Request (client error)
        401,  # Unauthorized (handled separately by token refresh)
        403,  # Forbidden
        404,  # Not Found
    ]

    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_DELAY = 1.0  # seconds
    DEFAULT_MAX_DELAY = 60.0  # seconds
    DEFAULT_EXPONENTIAL_BASE = 2.0
    DEFAULT_JITTER = True

    @classmethod
    def should_retry(cls, status_code: Optional[int], error: Optional[str] = None) -> bool:
        """
        Determine if a request should be retried based on status code and error

        Args:
            status_code: HTTP status code
            error: Error message

        Returns:
            True if request should be retried
        """
        # Check status code
        if status_code and status_code in cls.RETRYABLE_STATUS_CODES:
            return True

        if status_code and status_code in cls.NON_RETRYABLE_STATUS_CODES:
            return False

        # Check for specific error patterns
        if error:
            error_lower = error.lower()
            retryable_errors = [
                "timeout",
                "connection error",
                "connection reset",
                "connection refused",
                "temporarily unavailable",
                "service unavailable",
                "gateway timeout",
                "too many requests"
            ]

            for pattern in retryable_errors:
                if pattern in error_lower:
                    return True

        return False

    @classmethod
    def get_retry_delay(cls,
                       attempt: int,
                       initial_delay: float = DEFAULT_INITIAL_DELAY,
                       max_delay: float = DEFAULT_MAX_DELAY,
                       exponential_base: float = DEFAULT_EXPONENTIAL_BASE,
                       jitter: bool = DEFAULT_JITTER,
                       retry_after: Optional[int] = None) -> float:
        """
        Calculate retry delay with exponential backoff

        Args:
            attempt: Current retry attempt (0-based)
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter
            retry_after: Server-provided retry-after value (seconds)

        Returns:
            Delay in seconds
        """
        # Use server-provided retry-after if available
        if retry_after:
            delay = float(retry_after)
        else:
            # Calculate exponential backoff
            delay = initial_delay * (exponential_base ** attempt)

        # Cap at maximum delay
        delay = min(delay, max_delay)

        # Add jitter to prevent thundering herd
        if jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay = delay + random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)  # Ensure non-negative

    @classmethod
    def extract_retry_after(cls, response_headers: Dict[str, str]) -> Optional[int]:
        """
        Extract Retry-After header value from response

        Args:
            response_headers: Response headers

        Returns:
            Retry-after value in seconds, or None
        """
        retry_after = response_headers.get('Retry-After') or response_headers.get('retry-after')

        if retry_after:
            try:
                # Try parsing as integer (seconds)
                return int(retry_after)
            except ValueError:
                # Could be a date string - not handling for now
                logger.warning(f"Could not parse Retry-After header: {retry_after}")

        # Check X-RateLimit headers
        rate_limit_reset = response_headers.get('X-RateLimit-Reset') or response_headers.get('x-ratelimit-reset')
        if rate_limit_reset:
            try:
                # Unix timestamp
                reset_time = int(rate_limit_reset)
                current_time = int(time.time())
                return max(0, reset_time - current_time)
            except ValueError:
                logger.warning(f"Could not parse X-RateLimit-Reset header: {rate_limit_reset}")

        return None


def with_retry(max_retries: int = RetryHandler.DEFAULT_MAX_RETRIES,
              initial_delay: float = RetryHandler.DEFAULT_INITIAL_DELAY,
              max_delay: float = RetryHandler.DEFAULT_MAX_DELAY,
              exponential_base: float = RetryHandler.DEFAULT_EXPONENTIAL_BASE,
              jitter: bool = RetryHandler.DEFAULT_JITTER):
    """
    Decorator for adding retry logic to functions

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    # Check if result indicates a retryable error
                    if isinstance(result, dict) and 'status_code' in result:
                        status_code = result['status_code']
                        error = result.get('error')

                        if RetryHandler.should_retry(status_code, error):
                            if attempt < max_retries:
                                # Extract retry-after if available
                                headers = result.get('headers', {})
                                retry_after = RetryHandler.extract_retry_after(headers)

                                # Calculate delay
                                delay = RetryHandler.get_retry_delay(
                                    attempt,
                                    initial_delay,
                                    max_delay,
                                    exponential_base,
                                    jitter,
                                    retry_after
                                )

                                logger.warning(
                                    f"Retryable error (attempt {attempt + 1}/{max_retries + 1}): "
                                    f"Status {status_code}, Error: {error}. "
                                    f"Retrying in {delay:.2f} seconds..."
                                )

                                time.sleep(delay)
                                continue

                    return result

                except Exception as e:
                    last_exception = e

                    # Check if exception is retryable
                    error_msg = str(e)
                    if RetryHandler.should_retry(None, error_msg):
                        if attempt < max_retries:
                            delay = RetryHandler.get_retry_delay(
                                attempt,
                                initial_delay,
                                max_delay,
                                exponential_base,
                                jitter
                            )

                            logger.warning(
                                f"Retryable exception (attempt {attempt + 1}/{max_retries + 1}): "
                                f"{error_msg}. Retrying in {delay:.2f} seconds..."
                            )

                            time.sleep(delay)
                            continue

                    # Non-retryable error or last attempt
                    raise

            # If we get here, all retries exhausted
            if last_exception:
                raise last_exception

            return result

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)

                    # Check if result indicates a retryable error
                    if isinstance(result, dict) and 'status_code' in result:
                        status_code = result['status_code']
                        error = result.get('error')

                        if RetryHandler.should_retry(status_code, error):
                            if attempt < max_retries:
                                # Extract retry-after if available
                                headers = result.get('headers', {})
                                retry_after = RetryHandler.extract_retry_after(headers)

                                # Calculate delay
                                delay = RetryHandler.get_retry_delay(
                                    attempt,
                                    initial_delay,
                                    max_delay,
                                    exponential_base,
                                    jitter,
                                    retry_after
                                )

                                logger.warning(
                                    f"Retryable error (attempt {attempt + 1}/{max_retries + 1}): "
                                    f"Status {status_code}, Error: {error}. "
                                    f"Retrying in {delay:.2f} seconds..."
                                )

                                await asyncio.sleep(delay)
                                continue

                    return result

                except Exception as e:
                    last_exception = e

                    # Check if exception is retryable
                    error_msg = str(e)
                    if RetryHandler.should_retry(None, error_msg):
                        if attempt < max_retries:
                            delay = RetryHandler.get_retry_delay(
                                attempt,
                                initial_delay,
                                max_delay,
                                exponential_base,
                                jitter
                            )

                            logger.warning(
                                f"Retryable exception (attempt {attempt + 1}/{max_retries + 1}): "
                                f"{error_msg}. Retrying in {delay:.2f} seconds..."
                            )

                            await asyncio.sleep(delay)
                            continue

                    # Non-retryable error or last attempt
                    raise

            # If we get here, all retries exhausted
            if last_exception:
                raise last_exception

            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator