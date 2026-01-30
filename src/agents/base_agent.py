"""
Base Agent: Abstract Foundation for All AI Agents
==================================================
Classification: Internal Restricted
Status: 🟢 Production Ready

This module defines the BaseAgent abstract class that all Colab ERP agents
must inherit from. It enforces:

1. Standardized initialization
2. Mandatory audit logging
3. Timezone compliance via normalize_dates()
4. Connection pool safety via AgentPoolManager
5. Configuration management via agent_config table

All agents MUST:
- Inherit from BaseAgent
- Implement the execute() method
- Use self.log_action() for all operations
- Use self.get_connection() for database access
- Use self.normalize_dates() for timezone handling

Example Agent Implementation:
    
    from src.agents.base_agent import BaseAgent
    
    class MyAgent(BaseAgent):
        AGENT_ID = "my_agent_v1"
        AGENT_VERSION = "1.0.0"
        
        def execute(self, **kwargs):
            with self.log_timed_operation("my_operation"):
                with self.get_connection() as conn:
                    # Agent logic here
                    pass
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging

from .pool_manager import get_pool_manager
from .audit_logger import create_logger
from src.db import normalize_dates  # Import the v2.1.3 timezone logic

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================================
# BASE AGENT ABSTRACT CLASS
# ============================================================================

class BaseAgent(ABC):
    """
    Abstract base class for all Colab ERP AI agents.
    
    All agents must define:
        AGENT_ID: Unique identifier (e.g., "auditor_v1")
        AGENT_VERSION: Version string (e.g., "1.0.0")
    
    All agents must implement:
        execute(**kwargs): Main agent logic
    
    All agents inherit:
        - Connection pooling via AgentPoolManager
        - Audit logging via AuditLogger
        - Timezone normalization via normalize_dates()
        - Configuration loading from agent_config table
    
    Attributes:
        agent_id: Unique identifier for this agent
        agent_version: Version string
        config: Configuration dict loaded from agent_config table
        enabled: Whether this agent is enabled
    """
    
    # Subclasses MUST override these
    AGENT_ID: str = None
    AGENT_VERSION: str = "1.0.0"
    
    def __init__(self):
        """
        Initialize the agent.
        
        This:
        1. Validates AGENT_ID is defined
        2. Loads configuration from agent_config table
        3. Initializes pool manager and audit logger
        4. Checks if agent is enabled
        
        Raises:
            ValueError: If AGENT_ID is not defined
            RuntimeError: If agent is disabled in config
        """
        # Validation
        if self.AGENT_ID is None:
            raise ValueError(
                f"{self.__class__.__name__} must define AGENT_ID class attribute"
            )
        
        self.agent_id = self.AGENT_ID
        self.agent_version = self.AGENT_VERSION
        
        # Initialize infrastructure
        self._pool_manager = get_pool_manager()
        self._audit_logger = create_logger(self.agent_id, self.agent_version)
        
        # Load configuration from database
        self.config = self._load_config()
        self.enabled = self.config.get("enabled", True)
        
        # Check if agent is enabled
        if not self.enabled:
            error_msg = f"Agent {self.agent_id} is DISABLED in agent_config table"
            logger.warning(error_msg)
            self._audit_logger.log_error(
                operation="config_change",
                error_message=error_msg
            )
            raise RuntimeError(error_msg)
        
        logger.info(
            f"Agent {self.agent_id} (v{self.agent_version}) initialized successfully"
        )
        
        # Log initialization
        self._audit_logger.log_action(
            operation="read",  # Loading config counts as a read
            resource=f"agent_config:{self.agent_id}",
            metadata={"config": self.config}
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load agent configuration from the agent_config table.
        
        Returns:
            dict: Configuration object with structure:
                {
                    "enabled": bool,
                    "version": str,
                    "config": dict  # Custom agent settings
                }
        
        If no config exists, returns default empty config.
        """
        try:
            with self._pool_manager.get_agent_connection(self.agent_id) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT enabled, version, config
                        FROM agent_config
                        WHERE agent_id = %s
                        """,
                        (self.agent_id,)
                    )
                    
                    row = cur.fetchone()
                    
                    if row:
                        enabled, version, config_json = row
                        return {
                            "enabled": enabled,
                            "version": version,
                            "config": config_json or {}
                        }
                    else:
                        # No config found - return defaults
                        logger.warning(
                            f"No config found for {self.agent_id} in agent_config table. "
                            f"Using defaults."
                        )
                        return {
                            "enabled": True,
                            "version": self.agent_version,
                            "config": {}
                        }
        
        except Exception as e:
            logger.error(f"Failed to load config for {self.agent_id}: {e}")
            # Return safe defaults if config loading fails
            return {
                "enabled": True,
                "version": self.agent_version,
                "config": {}
            }
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the agent's primary function.
        
        This method MUST be implemented by all subclasses.
        
        Args:
            **kwargs: Agent-specific parameters
        
        Returns:
            Any: Agent-specific results
        
        Example:
            class AuditorAgent(BaseAgent):
                def execute(self, room_id=None):
                    # Audit logic here
                    return audit_results
        """
        pass
    
    # ========================================================================
    # INFRASTRUCTURE HELPERS (Available to all agents)
    # ========================================================================
    
    @contextmanager
    def get_connection(self):
        """
        Context manager to get a database connection via pool manager.
        
        This is the ONLY way agents should acquire connections.
        Never use src.db.get_db_connection() directly in agent code.
        
        Usage:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
        
        Yields:
            psycopg2.connection: Database connection
        """
        with self._pool_manager.get_agent_connection(self.agent_id) as conn:
            yield conn
    
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
        
        This wraps AuditLogger.log_action() for convenience.
        
        Args:
            operation: Type of operation
            resource: Target resource
            metadata: Structured metadata
            execution_time_ms: Performance metric
            authorized_by: Superuser who authorized (for HITL)
        
        Returns:
            int: audit_log.id
        """
        return self._audit_logger.log_action(
            operation=operation,
            resource=resource,
            metadata=metadata,
            execution_time_ms=execution_time_ms,
            authorized_by=authorized_by
        )
    
    def log_error(
        self,
        operation: str,
        error_message: str,
        resource: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Log a failed agent action.
        
        This wraps AuditLogger.log_error() for convenience.
        
        Args:
            operation: Type of operation that failed
            error_message: Error description
            resource: Target resource
            metadata: Additional context
        
        Returns:
            int: audit_log.id
        """
        return self._audit_logger.log_error(
            operation=operation,
            error_message=error_message,
            resource=resource,
            metadata=metadata
        )
    
    def log_timed_operation(self, operation: str):
        """
        Context manager for automatically timing and logging operations.
        
        Usage:
            with self.log_timed_operation("my_operation") as op:
                op.set_resource("resource:123")
                op.add_metadata("key", "value")
                # Operation logic here
        
        Returns:
            TimedOperation: Context manager that auto-logs on exit
        """
        return self._audit_logger.log_timed_operation(operation)
    
    def normalize_dates(self, date_input, time_start, time_end):
        """
        Normalize dates from user timezone (SAST) to UTC.
        
        This is a wrapper around src.db.normalize_dates() that ensures
        agents use the v2.1.3 Logic Bridge for timezone handling.
        
        Args:
            date_input: date object
            time_start: time object
            time_end: time object
        
        Returns:
            tuple: (start_utc, end_utc) as timezone-aware datetime objects
        
        Example:
            from datetime import date, time
            
            start_utc, end_utc = self.normalize_dates(
                date(2026, 1, 30),
                time(10, 0),
                time(12, 0)
            )
            # start_utc is now 2026-01-30 08:00:00+00:00 (UTC)
        """
        return normalize_dates(date_input, time_start, time_end)
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value from the agent's config.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
        
        Returns:
            Any: Configuration value
        
        Example:
            max_discrepancy = self.get_config_value(
                "thresholds.max_discrepancy_percent",
                default=5.0
            )
        """
        # Support nested keys with dot notation
        keys = key.split('.')
        value = self.config.get("config", {})
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def update_config(self, new_config: Dict[str, Any], updated_by: str):
        """
        Update agent configuration in the database.
        
        This should only be called by admin interfaces, not by agents themselves.
        
        Args:
            new_config: New configuration dict
            updated_by: Username of person making the change
        
        Returns:
            bool: True if update successful
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE agent_config
                        SET config = %s::jsonb,
                            updated_by = %s,
                            updated_at = NOW()
                        WHERE agent_id = %s
                        """,
                        (str(new_config), updated_by, self.agent_id)
                    )
                    conn.commit()
            
            # Log the config change
            self.log_action(
                operation="config_change",
                resource=f"agent_config:{self.agent_id}",
                metadata={"new_config": new_config},
                authorized_by=updated_by
            )
            
            # Reload config
            self.config = self._load_config()
            
            logger.info(f"Configuration updated for {self.agent_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update config for {self.agent_id}: {e}")
            self.log_error(
                operation="config_change",
                error_message=str(e),
                resource=f"agent_config:{self.agent_id}"
            )
            return False
    
    def __str__(self):
        """String representation of the agent."""
        return f"{self.__class__.__name__}({self.agent_id} v{self.agent_version})"
    
    def __repr__(self):
        """Developer representation of the agent."""
        return (
            f"<{self.__class__.__name__} "
            f"id={self.agent_id} "
            f"version={self.agent_version} "
            f"enabled={self.enabled}>"
        )
