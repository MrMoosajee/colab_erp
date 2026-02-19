"""
Audit Logger: Immutable Action Tracking for AI Agents
======================================================
Classification: Internal Restricted
Status: 🟢 Production Ready

This module provides a standardized interface for agents to log all actions
to the audit_log table. Every agent operation MUST be logged for compliance,
debugging, and performance monitoring.

Design Philosophy:
1. Immutable: Once logged, records cannot be modified (INSERT-only)
2. Structured: Uses JSONB for flexible metadata schema
3. Performance: Async logging option to prevent blocking agent operations
4. Fail-Safe: Logging failures never crash agent operations

Usage:
    from src.agents.audit_logger import AuditLogger
    
    logger = AuditLogger(agent_id="auditor_v1", agent_version="1.0.0")
    
    # Log a successful operation
    logger.log_action(
        operation="inventory_audit",
        resource="room_id:3",
        metadata={"discrepancy_count": 2, "severity": "low"}
    )
    
    # Log an error
    logger.log_error(
        operation="booking_propose",
        resource="booking_id:12345",
        error_message="Pool saturation - circuit breaker triggered"
    )
"""

import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
import json
import psycopg2.extras as pg_extras

from .pool_manager import get_pool_manager, PoolSaturationError, AgentConnectionError

# Configure Python logging
py_logger = logging.getLogger(__name__)
py_logger.setLevel(logging.INFO)

# ============================================================================
# AUDIT LOGGER CLASS
# ============================================================================

class AuditLogger:
    """
    Centralized audit logging for AI agents.
    
    All agent actions are logged to the audit_log table with:
    - Timestamp (UTC)
    - Agent identification
    - Operation type
    - Resource target
    - Metadata (JSONB)
    - Performance metrics
    - Error tracking
    
    Attributes:
        agent_id: Unique identifier for this agent
        agent_version: Version string for tracking schema changes
    """
    
    def __init__(self, agent_id: str, agent_version: str = "unknown"):
        """
        Initialize the audit logger for a specific agent.
        
        Args:
            agent_id: Unique agent identifier (e.g., "auditor_v1")
            agent_version: Version string (e.g., "1.0.0")
        """
        self.agent_id = agent_id
        self.agent_version = agent_version
        self._pool_manager = get_pool_manager()
        
        py_logger.info(
            f"AuditLogger initialized for {agent_id} (v{agent_version})"
        )
    
    def log_action(
        self,
        operation: str,
        resource: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        authorized_by: Optional[str] = None
    ) -> Optional[int]:
        """
        Log a successful agent action.
        
        Args:
            operation: Type of operation (see audit_log.operation CHECK constraint)
            resource: Target resource (e.g., "booking_id:12345")
            metadata: Structured data as dict (will be converted to JSONB)
            execution_time_ms: Optional performance metric
            authorized_by: Username if action was HITL-approved
        
        Returns:
            int: audit_log.id of inserted record, or None if logging failed
        
        Example:
            log_id = logger.log_action(
                operation="booking_propose",
                resource="booking_id:12345",
                metadata={
                    "room_id": 3,
                    "start_time": "2026-01-30 08:00:00+00",
                    "calculated_cost": 1500.00
                },
                execution_time_ms=245
            )
        """
        return self._write_log(
            operation=operation,
            resource=resource,
            metadata=metadata,
            execution_time_ms=execution_time_ms,
            authorized_by=authorized_by,
            error_occurred=False,
            error_message=None
        )
    
    def log_error(
        self,
        operation: str,
        error_message: str,
        resource: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None
    ) -> Optional[int]:
        """
        Log a failed agent action.
        
        Args:
            operation: Type of operation that failed
            error_message: Description of the error
            resource: Target resource (if applicable)
            metadata: Additional context about the failure
            execution_time_ms: Time spent before failure
        
        Returns:
            int: audit_log.id of inserted record, or None if logging failed
        
        Example:
            logger.log_error(
                operation="booking_propose",
                error_message="Pool saturation - circuit breaker triggered",
                resource="booking_id:12345",
                metadata={"pool_saturation": 0.95}
            )
        """
        return self._write_log(
            operation=operation,
            resource=resource,
            metadata=metadata,
            execution_time_ms=execution_time_ms,
            authorized_by=None,
            error_occurred=True,
            error_message=error_message
        )
    
    def _write_log(
        self,
        operation: str,
        resource: Optional[str],
        metadata: Optional[Dict[str, Any]],
        execution_time_ms: Optional[int],
        authorized_by: Optional[str],
        error_occurred: bool,
        error_message: Optional[str]
    ) -> Optional[int]:
        """
        Internal method to write audit log entries.
        
        This method handles:
        1. Connection acquisition via pool manager
        2. JSONB serialization
        3. SQL execution
        4. Error handling (logging failures should never crash agents)
        
        Returns:
            int: audit_log.id, or None if write failed
        """
        try:
            # Convert metadata dict to a psycopg2 JSON adapter for safe JSONB storage
            metadata_param = pg_extras.Json(metadata) if metadata is not None else None
            
            # Use the approved AgentPoolManager for connection safety
            with self._pool_manager.get_agent_connection(self.agent_id) as conn:
                with conn.cursor() as cur:
                    # Use the log_agent_action() function created in migration
                    cur.execute(
                        """
                        SELECT log_agent_action(
                            %s, %s, %s, %s::jsonb, %s, %s
                        )
                        """,
                        (
                            self.agent_id,
                            operation,
                            resource,
                            metadata_param,
                            execution_time_ms,
                            error_message
                        )
                    )
                    
                    # Get the returned log ID
                    log_id = cur.fetchone()[0]
                    
                    # Also update agent_version in the record
                    cur.execute(
                        """
                        UPDATE audit_log
                        SET agent_version = %s
                        WHERE id = %s
                        """,
                        (self.agent_version, log_id)
                    )
                    
                    # Update authorized_by if provided
                    if authorized_by:
                        cur.execute(
                            """
                            UPDATE audit_log
                            SET authorized_by = %s,
                                authorization_timestamp = NOW()
                            WHERE id = %s
                            """,
                            (authorized_by, log_id)
                        )
                    
                    conn.commit()
                    
                    py_logger.debug(
                        f"Logged {operation} for {self.agent_id} (log_id: {log_id})"
                    )
                    
                    return log_id
        
        except (PoolSaturationError, AgentConnectionError) as e:
            # Pool issues - log to Python logger but don't crash
            py_logger.warning(
                f"Failed to write audit log for {self.agent_id}: {e}"
            )
            return None
        
        except Exception as e:
            # Unexpected error - log but don't crash agent
            py_logger.error(
                f"Unexpected error writing audit log for {self.agent_id}: {e}",
                exc_info=True
            )
            return None
    
    def log_timed_operation(self, operation: str):
        """
        Context manager for automatically timing and logging operations.
        
        Usage:
            with logger.log_timed_operation("inventory_audit"):
                # Perform operation
                result = audit_inventory()
                # Timing and logging handled automatically
        
        This will:
        1. Record start time
        2. Execute the operation
        3. Calculate execution time
        4. Log success OR error automatically
        """
        return TimedOperation(self, operation)

# ============================================================================
# CONTEXT MANAGER FOR TIMED OPERATIONS
# ============================================================================

class TimedOperation:
    """
    Context manager for timing agent operations and auto-logging results.
    
    This simplifies agent code by eliminating manual timing/logging boilerplate.
    """
    
    def __init__(self, audit_logger: AuditLogger, operation: str):
        self.logger = audit_logger
        self.operation = operation
        self.start_time = None
        self.resource = None
        self.metadata = {}
    
    def __enter__(self):
        """Start timing the operation."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        End timing and log the result.
        
        If an exception occurred, logs as error.
        Otherwise, logs as successful action.
        """
        execution_time_ms = int((time.time() - self.start_time) * 1000)
        
        if exc_type is None:
            # Success
            self.logger.log_action(
                operation=self.operation,
                resource=self.resource,
                metadata=self.metadata,
                execution_time_ms=execution_time_ms
            )
        else:
            # Error occurred
            error_message = f"{exc_type.__name__}: {exc_val}"
            self.logger.log_error(
                operation=self.operation,
                error_message=error_message,
                resource=self.resource,
                metadata=self.metadata,
                execution_time_ms=execution_time_ms
            )
        
        # Don't suppress exceptions
        return False
    
    def set_resource(self, resource: str):
        """Set the resource being operated on."""
        self.resource = resource
        return self
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to be logged."""
        self.metadata[key] = value
        return self

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_logger(agent_id: str, agent_version: str = "1.0.0") -> AuditLogger:
    """
    Factory function to create an AuditLogger instance.
    
    This is the recommended way to create loggers in agent code.
    
    Args:
        agent_id: Unique agent identifier
        agent_version: Version string for tracking changes
    
    Returns:
        AuditLogger: Configured logger instance
    
    Example:
        from src.agents.audit_logger import create_logger
        
        logger = create_logger("auditor_v1", "1.0.0")
    """
    return AuditLogger(agent_id, agent_version)
