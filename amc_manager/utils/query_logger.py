"""
SQL Query Logging Utility
Provides structured logging for SQL queries at different processing stages
"""

import logging
import hashlib
from typing import Any, Dict, Optional
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class QueryLogger:
    """
    Structured logging for SQL queries through their lifecycle
    """

    # Processing stages
    STAGE_TEMPLATE = "template"
    STAGE_PARAMETER_EXTRACTION = "parameter_extraction"
    STAGE_PARAMETER_VALIDATION = "parameter_validation"
    STAGE_PARAMETER_SUBSTITUTION = "parameter_substitution"
    STAGE_LENGTH_VALIDATION = "length_validation"
    STAGE_AMC_SUBMISSION = "amc_submission"
    STAGE_AMC_EXECUTION = "amc_execution"
    STAGE_RESULT_RETRIEVAL = "result_retrieval"

    @classmethod
    def generate_query_id(cls, sql_query: str) -> str:
        """Generate a unique ID for tracking a query through its lifecycle"""
        # Use first 8 chars of hash for readability
        hash_obj = hashlib.md5(sql_query.encode())
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        return f"query_{timestamp}_{hash_obj.hexdigest()[:8]}"

    @classmethod
    def log_query_stage(cls,
                       query_id: str,
                       stage: str,
                       sql_query: str,
                       parameters: Optional[Dict[str, Any]] = None,
                       metadata: Optional[Dict[str, Any]] = None,
                       level: str = "INFO") -> None:
        """
        Log a query at a specific processing stage

        Args:
            query_id: Unique identifier for this query
            stage: Processing stage (use STAGE_* constants)
            sql_query: The SQL query content
            parameters: Query parameters if applicable
            metadata: Additional metadata (e.g., instance_id, user_id)
            level: Log level (INFO, DEBUG, WARNING, ERROR)
        """
        log_entry = {
            "query_id": query_id,
            "stage": stage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sql_preview": cls._truncate_sql(sql_query, 500),
            "sql_length": len(sql_query),
            "parameter_count": len(parameters) if parameters else 0
        }

        # Add metadata if provided
        if metadata:
            log_entry["metadata"] = metadata

        # Add parameter summary (not full values for security)
        if parameters:
            log_entry["parameters"] = cls._summarize_parameters(parameters)

        # Format log message
        message = f"[{query_id}] Stage: {stage} | Length: {log_entry['sql_length']} bytes"

        # Add parameter info if present
        if parameters:
            message += f" | Parameters: {log_entry['parameter_count']}"

        # Log at appropriate level
        if level == "DEBUG":
            logger.debug(message, extra={"structured": log_entry})
            # Also log full SQL at debug level
            logger.debug(f"[{query_id}] Full SQL:\n{sql_query}")
        elif level == "WARNING":
            logger.warning(message, extra={"structured": log_entry})
        elif level == "ERROR":
            logger.error(message, extra={"structured": log_entry})
        else:
            logger.info(message, extra={"structured": log_entry})

    @classmethod
    def log_parameter_processing(cls,
                                query_id: str,
                                param_name: str,
                                param_value: Any,
                                formatted_value: str,
                                is_large_list: bool = False) -> None:
        """
        Log individual parameter processing

        Args:
            query_id: Query identifier
            param_name: Parameter name
            param_value: Original parameter value
            formatted_value: Formatted value for SQL
            is_large_list: Whether this is a large list requiring special handling
        """
        # Determine value type and size
        value_type = type(param_value).__name__
        value_size = len(param_value) if isinstance(param_value, (list, str)) else 1

        log_entry = {
            "query_id": query_id,
            "parameter": param_name,
            "type": value_type,
            "size": value_size,
            "formatted_length": len(formatted_value),
            "is_large_list": is_large_list
        }

        message = f"[{query_id}] Parameter '{param_name}': {value_type} with {value_size} items"

        if is_large_list:
            logger.warning(f"{message} - Large list detected, consider VALUES clause",
                         extra={"structured": log_entry})
        else:
            logger.debug(message, extra={"structured": log_entry})

    @classmethod
    def log_validation_result(cls,
                            query_id: str,
                            validation_type: str,
                            is_valid: bool,
                            details: Optional[Dict[str, Any]] = None,
                            error_message: Optional[str] = None) -> None:
        """
        Log validation results

        Args:
            query_id: Query identifier
            validation_type: Type of validation (length, syntax, injection, etc.)
            is_valid: Whether validation passed
            details: Additional validation details
            error_message: Error message if validation failed
        """
        log_entry = {
            "query_id": query_id,
            "validation_type": validation_type,
            "is_valid": is_valid,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if details:
            log_entry["details"] = details

        if error_message:
            log_entry["error"] = error_message

        message = f"[{query_id}] Validation '{validation_type}': {'PASS' if is_valid else 'FAIL'}"

        if not is_valid:
            if error_message:
                message += f" - {error_message}"
            logger.warning(message, extra={"structured": log_entry})
        else:
            logger.debug(message, extra={"structured": log_entry})

    @classmethod
    def log_amc_submission(cls,
                         query_id: str,
                         instance_id: str,
                         entity_id: str,
                         sql_query: str,
                         response_status: Optional[int] = None,
                         execution_id: Optional[str] = None,
                         error: Optional[str] = None) -> None:
        """
        Log AMC API submission

        Args:
            query_id: Query identifier
            instance_id: AMC instance ID
            entity_id: Entity ID
            sql_query: Final SQL query submitted
            response_status: HTTP response status code
            execution_id: AMC execution ID if successful
            error: Error message if failed
        """
        log_entry = {
            "query_id": query_id,
            "stage": cls.STAGE_AMC_SUBMISSION,
            "instance_id": instance_id,
            "entity_id": entity_id,
            "sql_length": len(sql_query),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if response_status:
            log_entry["response_status"] = response_status

        if execution_id:
            log_entry["execution_id"] = execution_id
            message = f"[{query_id}] AMC submission successful: execution_id={execution_id}"
            logger.info(message, extra={"structured": log_entry})
        else:
            log_entry["error"] = error
            message = f"[{query_id}] AMC submission failed: {error}"
            logger.error(message, extra={"structured": log_entry})

    @classmethod
    def log_execution_status(cls,
                           query_id: str,
                           execution_id: str,
                           status: str,
                           duration_seconds: Optional[float] = None,
                           result_count: Optional[int] = None,
                           error: Optional[str] = None) -> None:
        """
        Log execution status updates

        Args:
            query_id: Query identifier
            execution_id: AMC execution ID
            status: Execution status (PENDING, RUNNING, SUCCEEDED, FAILED)
            duration_seconds: Execution duration if completed
            result_count: Number of results if successful
            error: Error message if failed
        """
        log_entry = {
            "query_id": query_id,
            "execution_id": execution_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if duration_seconds:
            log_entry["duration_seconds"] = duration_seconds

        if result_count is not None:
            log_entry["result_count"] = result_count

        message = f"[{query_id}] Execution {execution_id}: {status}"

        if status == "SUCCEEDED":
            if result_count is not None:
                message += f" - {result_count} results"
            if duration_seconds:
                message += f" in {duration_seconds:.2f}s"
            logger.info(message, extra={"structured": log_entry})
        elif status == "FAILED":
            log_entry["error"] = error
            message += f" - {error}"
            logger.error(message, extra={"structured": log_entry})
        else:
            logger.debug(message, extra={"structured": log_entry})

    @classmethod
    def _truncate_sql(cls, sql: str, max_length: int = 500) -> str:
        """Truncate SQL for preview in logs"""
        if len(sql) <= max_length:
            return sql
        return sql[:max_length] + "... [truncated]"

    @classmethod
    def _summarize_parameters(cls, parameters: Dict[str, Any]) -> Dict[str, str]:
        """Create a summary of parameters without exposing sensitive values"""
        summary = {}

        for key, value in parameters.items():
            if isinstance(value, list):
                summary[key] = f"list[{len(value)}]"
            elif isinstance(value, str):
                if len(value) > 50:
                    summary[key] = f"string[{len(value)} chars]"
                else:
                    # Only show short strings (likely not sensitive)
                    summary[key] = value
            elif value is None:
                summary[key] = "null"
            elif isinstance(value, bool):
                summary[key] = str(value).lower()
            else:
                summary[key] = type(value).__name__

        return summary

    @classmethod
    def create_query_summary(cls, query_id: str) -> Dict[str, Any]:
        """
        Create a summary of all stages for a query (for debugging)
        Note: This would require storing logs in memory or database
        """
        # This is a placeholder for future implementation
        # Would need to aggregate logs by query_id
        return {
            "query_id": query_id,
            "message": "Query summary not yet implemented"
        }


# Configure structured logging formatter
class StructuredFormatter(logging.Formatter):
    """Custom formatter that includes structured data"""

    def format(self, record):
        # Add structured data to the message if present
        if hasattr(record, 'structured'):
            # Could output as JSON for machine parsing
            # For now, just add key details to message
            pass
        return super().format(record)


def setup_query_logging(log_level=logging.INFO):
    """
    Set up query logging with appropriate handlers and formatters
    """
    # Get the logger
    query_logger = logging.getLogger('amc_manager.utils.query_logger')
    query_logger.setLevel(log_level)

    # Create console handler with structured formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    query_logger.addHandler(console_handler)

    return query_logger