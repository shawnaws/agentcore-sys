"""
HTTP Request Tool with Timeout and Retry Logic
Provides a wrapper around strands_tools.http_request with:
- 30-second timeout
- Exponential backoff retry (1s, 2s)
- Maximum 2 retry attempts
- Structured error logging
"""

import time
import logging
from typing import Any, Dict
from strands_tools import http_request

logger = logging.getLogger(__name__)

# Configuration constants
HTTP_TIMEOUT = 30  # seconds
MAX_RETRIES = 2
RETRY_DELAYS = [1, 2]  # seconds - exponential backoff


def http_request_with_retry(*args, **kwargs) -> Any:
    """
    Execute HTTP request with timeout and retry logic.
    
    This wrapper adds resilience to HTTP requests by:
    1. Setting a 30-second timeout
    2. Retrying failed requests up to 2 times
    3. Using exponential backoff (1s, 2s) between retries
    4. Logging all retry attempts
    
    Args:
        *args: Positional arguments passed to http_request
        **kwargs: Keyword arguments passed to http_request
    
    Returns:
        Response from http_request
        
    Raises:
        Exception: If all retry attempts fail
    """
    # Add timeout to kwargs if not already specified
    if 'timeout' not in kwargs:
        kwargs['timeout'] = HTTP_TIMEOUT
    
    last_exception = None
    
    for attempt in range(MAX_RETRIES + 1):  # Initial attempt + retries
        try:
            if attempt > 0:
                # This is a retry - wait before attempting
                delay = RETRY_DELAYS[attempt - 1]
                logger.warning(
                    f"Retrying HTTP request (attempt {attempt + 1}/{MAX_RETRIES + 1}) after {delay}s delay",
                    extra={"retry_count": attempt}
                )
                time.sleep(delay)
            
            # Execute the HTTP request
            result = http_request(*args, **kwargs)
            
            # Success - log if this was a retry
            if attempt > 0:
                logger.info(
                    f"HTTP request succeeded on retry attempt {attempt + 1}",
                    extra={"retry_count": attempt}
                )
            
            return result
            
        except Exception as e:
            last_exception = e
            error_msg = str(e)
            
            if attempt < MAX_RETRIES:
                # Will retry
                logger.warning(
                    f"HTTP request failed (attempt {attempt + 1}/{MAX_RETRIES + 1}): {error_msg}",
                    extra={"error": error_msg, "retry_count": attempt}
                )
            else:
                # Final attempt failed
                logger.error(
                    f"HTTP request failed after {MAX_RETRIES + 1} attempts: {error_msg}",
                    extra={"error": error_msg, "retry_count": attempt}
                )
    
    # All attempts failed - raise the last exception
    raise last_exception


# Export the function
__all__ = ['http_request_with_retry']
