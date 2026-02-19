"""
Secure Vault Interface: Safe Access to Legacy Data
===================================================
Classification: Internal Restricted
Status: 🟢 Production Ready

This module provides controlled, read-only access to the .secure_vault directory
without exposing sensitive file paths to the Git-tracked codebase.

Security Model:
1. Read-only access (agents cannot modify vault contents)
2. Path validation (prevents directory traversal attacks)
3. Audit logging (every vault access is logged)
4. Git isolation (vault is outside Git repository)

Supported Operations:
- Read legacy Excel inventory files
- Extract metadata from rental form PDFs
- Access network configuration files (read-only)

Prohibited Operations:
- Writing to vault
- Deleting vault contents
- Exposing raw file paths to agents

Usage:
    from src.agents.vault_interface import SecureVaultInterface
    
    vault = SecureVaultInterface(agent_id="auditor_v1")
    
    # Read legacy inventory for reconciliation
    df = vault.read_legacy_inventory()
    
    # Index rental forms for revenue analysis
    forms = vault.index_rental_forms()
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import pandas as pd
from datetime import datetime

from .audit_logger import create_logger

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================================
# EXCEPTION CLASSES
# ============================================================================

class VaultNotFoundError(Exception):
    """Raised when the .secure_vault directory doesn't exist."""
    pass

class SecurityViolationError(Exception):
    """Raised when a security policy is violated."""
    pass

class VaultAccessDeniedError(Exception):
    """
    Raised when agent lacks permission for requested vault operation.
    """
    pass

# ============================================================================
# SECURE VAULT INTERFACE CLASS
# ============================================================================

class SecureVaultInterface:
    """
    Provides controlled access to the .secure_vault directory.
    
    The vault contains sensitive legacy data that should NOT be tracked in Git:
    - inventory_v1.xlsx: Legacy Excel inventory
    - wifi_config.xml: Network configuration
    - rental_forms/*.pdf: Legal documents
    
    All access is:
    - Read-only
    - Audited
    - Path-validated
    
    Attributes:
        agent_id: Identifier of agent accessing the vault
        vault_path: Absolute path to .secure_vault
    """
    
    # Vault location (MUST be outside Git repository)
    VAULT_PATH = os.environ.get("COLAB_VAULT_PATH", "/home/colabtechsolutions/.secure_vault")
    
    # Allowed file extensions (security whitelist)
    ALLOWED_EXTENSIONS = [".pdf", ".xlsx", ".xls", ".xml", ".csv"]
    
    # Maximum file size to read (10 MB - prevents DoS)
    MAX_FILE_SIZE_MB = 10
    
    def __init__(self, agent_id: str):
        """
        Initialize vault interface for a specific agent.
        
        Args:
            agent_id: Identifier of the agent requesting access
        
        Raises:
            VaultNotFoundError: If vault directory doesn't exist
            SecurityViolationError: If vault is inside Git repository
        """
        self.agent_id = agent_id
        self.vault_path = Path(self.VAULT_PATH)
        self._audit_logger = create_logger(f"{agent_id}_vault", "1.0.0")
        
        # Security checks
        self._validate_vault_exists()
        self._validate_git_isolation()
        
        logger.info(f"SecureVaultInterface initialized for {agent_id}")
        
        # Log initialization
        self._log_vault_access("init", "vault_interface")
    
    def _validate_vault_exists(self):
        """
        Verify the vault directory exists.
        
        Raises:
            VaultNotFoundError: If vault doesn't exist
        """
        if not self.vault_path.exists():
            error_msg = f"Secure vault not found at {self.vault_path}"
            logger.error(error_msg)
            raise VaultNotFoundError(error_msg)
        
        if not self.vault_path.is_dir():
            error_msg = f"Vault path exists but is not a directory: {self.vault_path}"
            logger.error(error_msg)
            raise VaultNotFoundError(error_msg)
    
    def _validate_git_isolation(self):
        """
        Ensure vault is NOT inside the Git repository.
        
        This prevents accidental commits of sensitive data.
        
        Raises:
            SecurityViolationError: If vault is tracked by Git
        """
        try:
            # Get Git repository root (use repo-relative path where possible)
            repo_candidate = Path(__file__).resolve().parents[2]
            try:
                git_root = subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=str(repo_candidate),
                    stderr=subprocess.DEVNULL,
                ).decode().strip()

                # Check if vault is inside Git repo
                if str(self.vault_path).startswith(git_root):
                    error_msg = (
                        f"SECURITY VIOLATION: Vault is inside Git repository! "
                        f"Vault: {self.vault_path}, Git: {git_root}"
                    )
                    logger.critical(error_msg)
                    self._log_vault_access("security_violation", "git_isolation_check")
                    raise SecurityViolationError(error_msg)

                logger.info("✓ Vault is isolated from Git repository")

            except subprocess.CalledProcessError:
                # Not in a Git repository - this is fine
                logger.warning("Could not verify Git isolation (not in a Git repo?)")
    
    def _validate_file_path(self, file_path: Path):
        """
        Validate that a file path is safe to access.
        
        Prevents:
        - Directory traversal attacks (../)
        - Access to files outside vault
        - Access to files with disallowed extensions
        
        Args:
            file_path: Path to validate
        
        Raises:
            SecurityViolationError: If path is unsafe
        """
        # Resolve absolute path and check it's inside vault
        resolved_path = file_path.resolve()
        
        if not str(resolved_path).startswith(str(self.vault_path.resolve())):
            error_msg = f"Path traversal attempt detected: {file_path}"
            logger.critical(error_msg)
            self._log_vault_access("security_violation", str(file_path))
            raise SecurityViolationError(error_msg)
        
        # Check file extension (case-insensitive)
        if file_path.suffix.lower() not in [ext.lower() for ext in self.ALLOWED_EXTENSIONS]:
            error_msg = f"Disallowed file extension: {file_path.suffix}"
            logger.warning(error_msg)
            raise SecurityViolationError(error_msg)
        
        # Check file size
        if resolved_path.exists():
            size_mb = resolved_path.stat().st_size / (1024 * 1024)
            if size_mb > self.MAX_FILE_SIZE_MB:
                error_msg = f"File too large: {size_mb:.2f} MB (max: {self.MAX_FILE_SIZE_MB} MB)"
                logger.warning(error_msg)
                raise SecurityViolationError(error_msg)
    
    def _log_vault_access(self, operation: str, resource: str, metadata: Optional[Dict] = None):
        """
        Log all vault access to audit_log.
        
        Args:
            operation: Type of access (read, list, etc.)
            resource: File or directory accessed
            metadata: Additional context
        """
        self._audit_logger.log_action(
            operation="vault_access",
            resource=f"vault:{resource}",
            metadata={
                "vault_operation": operation,
                **(metadata or {})
            }
        )
    
    # ========================================================================
    # PUBLIC API: SAFE VAULT OPERATIONS
    # ========================================================================
    
    def read_legacy_inventory(self) -> pd.DataFrame:
        """
        Read the legacy Excel inventory file (inventory_v1.xlsx).
        
        This is used by the Auditor Agent to reconcile old inventory
        records with the new database.
        
        Returns:
            pd.DataFrame: Legacy inventory data
        
        Raises:
            VaultAccessDeniedError: If file doesn't exist or can't be read
        
        Example:
            vault = SecureVaultInterface("auditor_v1")
            legacy_df = vault.read_legacy_inventory()
            
            # Compare with current database
            current_df = run_query("SELECT * FROM inventory_movements")
        """
        file_path = self.vault_path / "inventory_v1.xlsx"
        
        try:
            # Validate path
            self._validate_file_path(file_path)
            
            # Check file exists
            if not file_path.exists():
                raise VaultAccessDeniedError(f"File not found: {file_path.name}")
            
            # Read Excel
            df = pd.read_excel(file_path)
            
            # Log access
            self._log_vault_access(
                "read",
                file_path.name,
                metadata={"rows": len(df), "columns": list(df.columns)}
            )
            
            logger.info(f"Successfully read {file_path.name}: {len(df)} rows")
            return df
        
        except Exception as e:
            error_msg = f"Failed to read legacy inventory: {e}"
            logger.error(error_msg)
            self._audit_logger.log_error(
                operation="vault_access",
                error_message=error_msg,
                resource=f"vault:{file_path.name}"
            )
            raise VaultAccessDeniedError(error_msg) from e
    
    def index_rental_forms(self) -> List[Dict[str, Any]]:
        """
        Extract metadata from rental form PDFs.
        
        This is used by the Revenue Agent to correlate historical
        revenue data without reading full PDF contents.
        
        Returns:
            List[Dict]: List of metadata dicts with structure:
                {
                    "filename": str,
                    "size_kb": float,
                    "modified": datetime,
                    "path_relative": str
                }
        
        Example:
            vault = SecureVaultInterface("revenue_v1")
            forms = vault.index_rental_forms()
            
            for form in forms:
                print(f"{form['filename']}: {form['size_kb']:.2f} KB")
        """
        forms_dir = self.vault_path / "rental_forms"
        
        try:
            # Check directory exists
            if not forms_dir.exists():
                logger.warning(f"Rental forms directory not found: {forms_dir}")
                return []
            
            metadata = []
            
            # Scan for PDFs
            for pdf_file in forms_dir.glob("*.pdf"):
                try:
                    # Validate each file
                    self._validate_file_path(pdf_file)
                    
                    # Extract metadata
                    stat = pdf_file.stat()
                    meta = {
                        "filename": pdf_file.name,
                        "size_kb": stat.st_size / 1024,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "path_relative": str(pdf_file.relative_to(self.vault_path))
                    }
                    
                    metadata.append(meta)
                
                except SecurityViolationError as e:
                    # Skip invalid files
                    logger.warning(f"Skipping invalid file: {pdf_file.name}: {e}")
            
            # Log access
            self._log_vault_access(
                "list",
                "rental_forms/",
                metadata={"file_count": len(metadata)}
            )
            
            logger.info(f"Indexed {len(metadata)} rental forms")
            return metadata
        
        except Exception as e:
            error_msg = f"Failed to index rental forms: {e}"
            logger.error(error_msg)
            self._audit_logger.log_error(
                operation="vault_access",
                error_message=error_msg,
                resource="vault:rental_forms/"
            )
            return []
    
    def read_network_config(self) -> Optional[str]:
        """
        Read network configuration file (wifi_config.xml).
        
        This is a sensitive file and should only be accessed by
        authorized system configuration agents.
        
        Returns:
            str: XML content as string, or None if access denied
        
        Security Note:
            This method requires elevated privileges. Normal agents
            should not call this method.
        """
        file_path = self.vault_path / "wifi_config.xml"
        
        # Additional security check: only system agents can access this
        if not self.agent_id.startswith("system_"):
            error_msg = f"Access denied: {self.agent_id} lacks permission for network config"
            logger.warning(error_msg)
            self._log_vault_access("access_denied", file_path.name)
            raise VaultAccessDeniedError(error_msg)
        
        try:
            # Validate path
            self._validate_file_path(file_path)
            
            # Check file exists
            if not file_path.exists():
                raise VaultAccessDeniedError(f"File not found: {file_path.name}")
            
            # Read XML
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Log access (CRITICAL - this is a sensitive file)
            self._log_vault_access(
                "read",
                file_path.name,
                metadata={"content_length": len(content), "security_level": "HIGH"}
            )
            
            logger.warning(f"SENSITIVE FILE ACCESSED: {file_path.name} by {self.agent_id}")
            return content
        
        except Exception as e:
            error_msg = f"Failed to read network config: {e}"
            logger.error(error_msg)
            self._audit_logger.log_error(
                operation="vault_access",
                error_message=error_msg,
                resource=f"vault:{file_path.name}"
            )
            return None
    
    def list_vault_contents(self) -> List[Dict[str, Any]]:
        """
        List all files in the vault (for admin/debugging).
        
        Returns:
            List[Dict]: Metadata for all vault files
        
        Example:
            vault = SecureVaultInterface("admin_agent")
            contents = vault.list_vault_contents()
            
            for item in contents:
                print(f"{item['path']}: {item['size_kb']:.2f} KB")
        """
        try:
            contents = []
            
            for item in self.vault_path.rglob("*"):
                if item.is_file():
                    try:
                        # Validate each file
                        self._validate_file_path(item)
                        
                        stat = item.stat()
                        contents.append({
                            "path": str(item.relative_to(self.vault_path)),
                            "size_kb": stat.st_size / 1024,
                            "modified": datetime.fromtimestamp(stat.st_mtime),
                            "extension": item.suffix
                        })
                    
                    except SecurityViolationError:
                        # Skip invalid files
                        pass
            
            # Log access
            self._log_vault_access(
                "list",
                "vault_root/",
                metadata={"item_count": len(contents)}
            )
            
            return contents
        
        except Exception as e:
            error_msg = f"Failed to list vault contents: {e}"
            logger.error(error_msg)
            self._audit_logger.log_error(
                operation="vault_access",
                error_message=error_msg,
                resource="vault:/"
            )
            return []
    
    def get_vault_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vault.
        
        Returns:
            Dict: Vault statistics including:
                - total_files: Number of files
                - total_size_mb: Total size in MB
                - file_types: Count by extension
        """
        try:
            contents = self.list_vault_contents()
            
            stats = {
                "total_files": len(contents),
                "total_size_mb": sum(item["size_kb"] for item in contents) / 1024,
                "file_types": {}
            }
            
            # Count by extension
            for item in contents:
                ext = item["extension"]
                stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
            
            return stats
        
        except Exception as e:
            logger.error(f"Failed to get vault stats: {e}")
            return {
                "total_files": 0,
                "total_size_mb": 0.0,
                "file_types": {}
            }
