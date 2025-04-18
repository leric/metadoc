"""
Tests for the workspace module.
"""
import os
import tempfile
from pathlib import Path

import pytest

from airic.core.workspace import Workspace


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


def test_workspace_initialization(temp_dir):
    """Test workspace initialization and structure."""
    # Create a workspace
    workspace = Workspace(temp_dir)
    
    # Workspace shouldn't be initialized yet
    assert not workspace.is_initialized()
    
    # Initialize the workspace
    success = workspace.initialize()
    assert success
    
    # Check if all required directories exist
    assert workspace.is_initialized()
    assert workspace.airic_dir.is_dir()
    assert workspace.meta_dir.is_dir()
    assert workspace.agents_dir.is_dir()
    assert workspace.doctypes_dir.is_dir()
    assert workspace.workflows_dir.is_dir()
    assert workspace.history_dir.is_dir()


def test_workspace_find(temp_dir):
    """Test finding the workspace root."""
    # Create a workspace
    workspace = Workspace(temp_dir)
    workspace.initialize()
    
    # Create nested directories
    nested_dir = temp_dir / "a" / "b" / "c"
    nested_dir.mkdir(parents=True)
    
    # Should find workspace from nested directory
    found_path = Workspace.find_workspace_root(nested_dir)
    assert found_path == temp_dir
    
    # Should find workspace from workspace root
    found_path = Workspace.find_workspace_root(temp_dir)
    assert found_path == temp_dir
    
    # Should return None for unrelated directory
    with tempfile.TemporaryDirectory() as other_dir:
        found_path = Workspace.find_workspace_root(Path(other_dir))
        assert found_path is None 