"""
Common Agent Utilities Library
Provides shared functionality for all agents including:
- Structured JSON logging
- MCP client connection management
- Retry logic with exponential backoff
- Health check mechanisms
- Error handling patterns
"""

import json
import logging
import time
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from contextlib import contextmanager


# Configuration constants
MCP_CONNECTION_TIMEOUT = 10  # seconds
MCP_TOOL_DISCOVERY_TIMEOUT = 5  # seconds
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # seconds - exponential backoff


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging across all agents.
    Provides consistent log format with timestamps, agent IDs, and contextual information.
    """
    
    def __init__(self, agent_id: str):
        super().__init__()
        self.agent_id = agent_id
    
    def format(self, record):
        """Format log record as JSON with standard fields."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "agent": self.agent_id,
            "message": record.getMessage(),
        }
        
        # Add optional contextual fields if present
        optional_fields = [
            'sub_agent', 'tool', 'query', 'error', 'retry_count', 
            'tool_count', 'operation', 'duration_ms', 'status'
        ]
        for field in optional_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(agent_id: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up structured JSON logging for an agent.
    
    Args:
        agent_id: Identifier for the agent (e.g., "agent001")
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(agent_id)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter(agent_id))
    logger.addHandler(handler)
    
    return logger


def validate_environment_variables(required_vars: List[str], logger: Optional[logging.Logger] = None) -> Dict[str, str]:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: List of environment variable names
        logger: Optional logger for error messages
    
    Returns:
        Dictionary mapping variable names to their values
    
    Raises:
        ValueError: If any required variable is missing
    """
    import os
    
    missing_vars = []
    env_values = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            env_values[var] = value
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        if logger:
            logger.error(error_msg, extra={"operation": "env_validation"})
        raise ValueError(error_msg)
    
    if logger:
        logger.info(
            f"Validated {len(required_vars)} environment variables",
            extra={"operation": "env_validation", "status": "success"}
        )
    
    return env_values


def retry_with_backoff(
    func: Callable,
    max_retries: int = MAX_RETRIES,
    delays: List[int] = None,
    logger: Optional[logging.Logger] = None,
    operation_name: str = "operation"
) -> Any:
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        delays: List of delay durations in seconds (default: [1, 2, 4])
        logger: Optional logger for retry messages
        operation_name: Name of operation for logging
    
    Returns:
        Result from successful function execution
    
    Raises:
        Exception: Last exception if all retries fail
    """
    if delays is None:
        delays = RETRY_DELAYS
    
    last_exception = None
    
    for attempt in range(max_retries + 1):  # Initial attempt + retries
        try:
            if attempt > 0:
                # This is a retry - wait before attempting
                delay = delays[min(attempt - 1, len(delays) - 1)]
                if logger:
                    logger.warning(
                        f"Retrying {operation_name} (attempt {attempt + 1}/{max_retries + 1}) after {delay}s delay",
                        extra={"operation": operation_name, "retry_count": attempt, "delay_seconds": delay}
                    )
                time.sleep(delay)
            
            # Execute the function
            result = func()
            
            # Success - log if this was a retry
            if attempt > 0 and logger:
                logger.info(
                    f"{operation_name} succeeded on retry attempt {attempt + 1}",
                    extra={"operation": operation_name, "retry_count": attempt, "status": "success"}
                )
            
            return result
            
        except Exception as e:
            last_exception = e
            error_msg = str(e)
            
            if logger:
                if attempt < max_retries:
                    # Will retry
                    logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{max_retries + 1}): {error_msg}",
                        extra={"operation": operation_name, "error": error_msg, "retry_count": attempt}
                    )
                else:
                    # Final attempt failed
                    logger.error(
                        f"{operation_name} failed after {max_retries + 1} attempts: {error_msg}",
                        extra={"operation": operation_name, "error": error_msg, "retry_count": attempt},
                        exc_info=True
                    )
    
    # All attempts failed - raise the last exception
    raise last_exception


@contextmanager
def timer_context(logger: logging.Logger, operation: str):
    """
    Context manager for timing operations and logging results.
    
    Args:
        logger: Logger instance
        operation: Name of operation being timed
    
    Yields:
        None
    
    Example:
        with timer_context(logger, "tool_discovery"):
            tools = discover_tools()
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"{operation} completed",
            extra={"operation": operation, "duration_ms": duration_ms}
        )


def create_error_response(
    agent_id: str,
    operation: str,
    error: Exception,
    include_details: bool = False
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        agent_id: Identifier of the agent
        operation: Operation that failed
        error: Exception that occurred
        include_details: Whether to include full error details (for debugging)
    
    Returns:
        Dictionary with standardized error format
    """
    response = {
        "agent": agent_id,
        "operation": operation,
        "status": "error",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error_type": type(error).__name__,
        "error_message": str(error)
    }
    
    if include_details:
        import traceback
        response["error_details"] = traceback.format_exc()
    
    return response


class AgentHealthChecker:
    """
    Health check mechanism for monitoring agent availability.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger
        self.health_status: Dict[str, Dict] = {}
    
    def check_agent_health(
        self,
        agent_id: str,
        health_check_func: Callable,
        timeout: int = 5
    ) -> Dict[str, Any]:
        """
        Check health of a single agent.
        
        Args:
            agent_id: Identifier of the agent
            health_check_func: Function that returns True if agent is healthy
            timeout: Timeout in seconds
        
        Returns:
            Dictionary with health status information
        """
        start_time = time.time()
        
        try:
            is_healthy = health_check_func()
            response_time_ms = int((time.time() - start_time) * 1000)
            
            status = {
                "agent_id": agent_id,
                "status": "healthy" if is_healthy else "unhealthy",
                "response_time_ms": response_time_ms,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            if self.logger:
                self.logger.info(
                    f"Health check for {agent_id}: {status['status']}",
                    extra={
                        "operation": "health_check",
                        "sub_agent": agent_id,
                        "status": status['status'],
                        "duration_ms": response_time_ms
                    }
                )
            
            self.health_status[agent_id] = status
            return status
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            status = {
                "agent_id": agent_id,
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": response_time_ms,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            if self.logger:
                self.logger.error(
                    f"Health check for {agent_id} failed: {str(e)}",
                    extra={
                        "operation": "health_check",
                        "sub_agent": agent_id,
                        "error": str(e),
                        "duration_ms": response_time_ms
                    }
                )
            
            self.health_status[agent_id] = status
            return status
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get summary of all agent health statuses.
        
        Returns:
            Dictionary with health summary
        """
        healthy_count = sum(1 for s in self.health_status.values() if s['status'] == 'healthy')
        total_count = len(self.health_status)
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_agents": total_count,
            "healthy_agents": healthy_count,
            "unhealthy_agents": total_count - healthy_count,
            "agents": self.health_status
        }


# Export all public functions and classes
__all__ = [
    'JSONFormatter',
    'setup_logging',
    'validate_environment_variables',
    'retry_with_backoff',
    'timer_context',
    'create_error_response',
    'AgentHealthChecker',
    'MCP_CONNECTION_TIMEOUT',
    'MCP_TOOL_DISCOVERY_TIMEOUT',
    'MAX_RETRIES',
    'RETRY_DELAYS'
]
