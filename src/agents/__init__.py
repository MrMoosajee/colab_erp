"""
Colab ERP v2.2: AI Agent Infrastructure
========================================
Classification: Internal Restricted
Status: 🟡 Pre-Production

This package provides the foundation for AI-powered autonomous agents that
extend the Colab ERP system while maintaining v2.1.3 stability guarantees.

Core Design Principles:
1. All agents MUST use AgentPoolManager for database connections
2. All agents MUST use normalize_dates() for timezone handling
3. All agent actions MUST be logged to audit_log table
4. All financial decisions REQUIRE superuser HITL approval

Available Agents (v2.2.0):
- AuditorAgent: Reconciles inventory vs. bookings (Ghost Inventory detection)
- ConflictResolverAgent: Pre-validates bookings (Sliding Doors logic)
- RevenueAgent: Calculates booking costs (Q1 2026 roadmap)
"""

__version__ = "2.2.0"
__author__ = "Colab Tech Solutions - AI Engineering Division"

# Expose key components at package level
from .pool_manager import AgentPoolManager, PoolSaturationError
from .base_agent import BaseAgent
from .audit_logger import AuditLogger

__all__ = [
    "AgentPoolManager",
    "PoolSaturationError",
    "BaseAgent",
    "AuditLogger",
]
