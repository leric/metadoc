"""
Workspace management functionality for Airic.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any


class Workspace:
    """
    Manages an Airic workspace, including directory structure and configuration.
    """
    
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
        
    def initialize(self) -> bool:
        """
        Initialize the workspace by creating the necessary directory structure.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.airic_dir.mkdir(exist_ok=True)
            self.meta_dir.mkdir(exist_ok=True)
            self.agents_dir.mkdir(exist_ok=True)
            self.doctypes_dir.mkdir(exist_ok=True)
            self.workflows_dir.mkdir(exist_ok=True)
            self.history_dir.mkdir(exist_ok=True)
            return True
        except Exception:
            return False 