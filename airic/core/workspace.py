"""
Workspace management functionality for Airic.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from contextlib import contextmanager


logger = logging.getLogger(__name__)


class WorkspaceValidationError(Exception):
    """Exception raised when workspace validation fails."""
    pass


class WorkspaceConfig:
    """
    Manages workspace configuration and metadata.
    """
    
    DEFAULT_CONFIG = {
        "version": "0.1.0",
        "name": "airic-workspace",
        "description": "Airic workspace for document-driven AI collaboration",
        "created_at": None,  # Will be set at creation time
    }
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """
        Initialize workspace configuration.
        
        Args:
            config_data: Initial configuration data (uses DEFAULT_CONFIG if None)
        """
        self.data = config_data if config_data is not None else self.DEFAULT_CONFIG.copy()
    
    @classmethod
    def load(cls, config_path: Path) -> 'WorkspaceConfig':
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            WorkspaceConfig instance with loaded data
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file format is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                
            return cls(config_data)
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")
    
    def save(self, config_path: Path) -> None:
        """
        Save configuration to a YAML file.
        
        Args:
            config_path: Path to save the configuration file
            
        Raises:
            IOError: If unable to write to file
        """
        try:
            with open(config_path, 'w') as f:
                yaml.dump(self.data, f, default_flow_style=False)
        except Exception as e:
            raise IOError(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by key."""
        self.data[key] = value
    
    def update(self, config_data: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self.data.update(config_data)


class Workspace:
    """
    Manages an Airic workspace, including directory structure and configuration.
    """
    
    CONFIG_FILENAME = "config.yaml"
    REQUIRED_DIRS = [
        ".airic",
        ".airic/meta",
        ".airic/meta/agents",
        ".airic/meta/doctypes",
        ".airic/meta/workflows",
        ".airic/history"
    ]
    
    def __init__(self, root_path: Path):
        """
        Initialize a workspace with the given root path.
        
        Args:
            root_path: The root directory of the workspace
        """
        self.root_path = root_path
        self.airic_dir = root_path / ".airic"
        self.meta_dir = self.airic_dir / "meta"
        self.agents_dir = self.meta_dir / "agents"
        self.doctypes_dir = self.meta_dir / "doctypes"
        self.workflows_dir = self.meta_dir / "workflows"
        self.history_dir = self.airic_dir / "history"
        self.config_path = self.airic_dir / self.CONFIG_FILENAME
        self._config = None  # Lazy loaded
        
    @property
    def config(self) -> WorkspaceConfig:
        """
        Get the workspace configuration.
        
        Returns:
            WorkspaceConfig instance for this workspace
            
        Raises:
            WorkspaceValidationError: If workspace isn't initialized
        """
        if not self.is_initialized():
            raise WorkspaceValidationError("Workspace is not initialized")
            
        if self._config is None:
            if self.config_path.exists():
                self._config = WorkspaceConfig.load(self.config_path)
            else:
                self._config = WorkspaceConfig()
                
        return self._config
        
    @classmethod
    def find_workspace_root(cls, start_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Find the root of the Airic workspace by searching for .airic directory 
        in the current or parent directories.
        
        Args:
            start_dir: Directory to start searching from (defaults to current directory)
            
        Returns:
            Path to the workspace root, or None if not found
        """
        if start_dir is None:
            start_dir = Path.cwd()
            
        current_dir = start_dir.absolute()
        
        # Check if .airic exists in the current directory
        if (current_dir / ".airic").is_dir():
            return current_dir
            
        # Traverse up the directory tree
        parent = current_dir.parent
        
        # Stop if we've reached the root of the filesystem
        if parent == current_dir:
            return None
            
        # Recursively check parent directories
        return cls.find_workspace_root(parent)
        
    def is_initialized(self) -> bool:
        """
        Check if the workspace is properly initialized.
        
        Returns:
            True if the workspace has the required structure, False otherwise
        """
        return (
            self.airic_dir.is_dir() and
            self.meta_dir.is_dir() and
            self.agents_dir.is_dir() and
            self.doctypes_dir.is_dir() and
            self.workflows_dir.is_dir() and
            self.history_dir.is_dir()
        )
    
    def validate(self) -> List[str]:
        """
        Validate the workspace structure and return a list of validation errors.
        
        Returns:
            List of validation error messages (empty if no errors)
        """
        errors = []
        
        # Check required directories
        for dir_path in self.REQUIRED_DIRS:
            full_path = self.root_path / dir_path
            if not full_path.is_dir():
                errors.append(f"Required directory '{dir_path}' is missing")
        
        # Check config file - only if the main .airic directory exists
        # This ensures we validate the config file independently of the is_initialized() state
        if self.airic_dir.is_dir() and not self.config_path.exists():
            errors.append(f"Configuration file '{self.CONFIG_FILENAME}' is missing")
            
        return errors
    
    def is_valid_workspace(self) -> bool:
        """
        Check if the workspace is valid by running validation checks.
        
        Returns:
            True if the workspace is valid, False otherwise
        """
        return len(self.validate()) == 0
        
    def initialize(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize the workspace by creating the necessary directory structure
        and configuration.
        
        Args:
            config_data: Optional configuration data to initialize with
            
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Create directory structure
            self.airic_dir.mkdir(exist_ok=True)
            self.meta_dir.mkdir(exist_ok=True)
            self.agents_dir.mkdir(exist_ok=True)
            self.doctypes_dir.mkdir(exist_ok=True)
            self.workflows_dir.mkdir(exist_ok=True)
            self.history_dir.mkdir(exist_ok=True)
            
            # Create or update config file
            config = WorkspaceConfig(config_data)
            if not self.config_path.exists():
                # Add creation timestamp if this is a new config
                from datetime import datetime
                config.set("created_at", datetime.now().isoformat())
                
            config.save(self.config_path)
            self._config = config
            
            return True
        except Exception as e:
            logger.error(f"Error initializing workspace: {e}")
            return False


class WorkspaceContext:
    """
    Context manager for CLI commands that require a valid workspace.
    """
    
    def __init__(self, workspace_path: Optional[Path] = None):
        """
        Initialize workspace context.
        
        Args:
            workspace_path: Explicit workspace path (auto-detected if None)
        """
        self.workspace_path = workspace_path
        self.workspace = None
        
    def __enter__(self) -> Workspace:
        """
        Enter context manager, finding and validating workspace.
        
        Returns:
            Workspace instance
            
        Raises:
            WorkspaceValidationError: If workspace can't be found or validated
        """
        # Find workspace root if not explicitly provided
        if self.workspace_path is None:
            workspace_root = Workspace.find_workspace_root()
            if workspace_root is None:
                raise WorkspaceValidationError(
                    "Not in an Airic workspace. Run 'airic init' to create one, "
                    "or change to a valid workspace directory."
                )
            self.workspace_path = workspace_root
            
        # Create and validate workspace
        self.workspace = Workspace(self.workspace_path)
        validation_errors = self.workspace.validate()
        
        if validation_errors:
            error_msg = "Invalid Airic workspace:\n" + "\n".join([f"- {e}" for e in validation_errors])
            raise WorkspaceValidationError(error_msg)
            
        return self.workspace
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass


@contextmanager
def workspace_context(workspace_path: Optional[Path] = None) -> Workspace:
    """
    Simplified context manager function for workspace operations.
    
    Args:
        workspace_path: Explicit workspace path (auto-detected if None)
        
    Yields:
        Validated Workspace instance
        
    Raises:
        WorkspaceValidationError: If workspace can't be found or validated
    """
    context = WorkspaceContext(workspace_path)
    workspace = context.__enter__()
    try:
        yield workspace
    finally:
        context.__exit__(None, None, None) 