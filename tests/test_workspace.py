"""
Tests for the workspace module.
"""
import os
import tempfile
import yaml
from pathlib import Path
from datetime import datetime

import pytest

from airic.core.workspace import Workspace, WorkspaceConfig, WorkspaceContext, workspace_context, WorkspaceValidationError


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
    
    # Check that config file exists
    assert workspace.config_path.exists()
    
    # Check that validation passes
    assert workspace.is_valid_workspace()
    assert len(workspace.validate()) == 0


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


def test_workspace_config(temp_dir):
    """Test workspace configuration functionality."""
    # Create a workspace with custom config
    workspace = Workspace(temp_dir)
    custom_config = {
        "version": "0.1.0", 
        "name": "test-workspace",
        "description": "Test workspace",
        "custom_setting": "value"
    }
    workspace.initialize(custom_config)
    
    # Load config and check values
    config = workspace.config
    assert config.get("name") == "test-workspace"
    assert config.get("description") == "Test workspace"
    assert config.get("custom_setting") == "value"
    assert config.get("version") == "0.1.0"
    assert config.get("created_at") is not None
    
    # Test modifying config
    config.set("new_setting", 123)
    assert config.get("new_setting") == 123
    
    # Save and reload config
    config.save(workspace.config_path)
    new_config = WorkspaceConfig.load(workspace.config_path)
    assert new_config.get("new_setting") == 123
    
    # Test updating multiple values
    config.update({"key1": "value1", "key2": "value2"})
    assert config.get("key1") == "value1"
    assert config.get("key2") == "value2"


def test_workspace_validation(temp_dir):
    """Test workspace validation functionality."""
    # Create a workspace
    workspace = Workspace(temp_dir)
    workspace.initialize()
    
    # Should be valid
    assert workspace.is_valid_workspace()
    assert len(workspace.validate()) == 0
    
    # Delete a required directory
    (workspace.agents_dir).rmdir()
    
    # Should be invalid with specific error
    assert not workspace.is_valid_workspace()
    errors = workspace.validate()
    assert len(errors) == 1
    assert any(".airic/meta/agents" in error for error in errors)
    
    # Delete config file
    os.remove(workspace.config_path)
    
    # Should report both errors
    errors = workspace.validate()
    assert len(errors) == 2
    assert any("agents" in error for error in errors)
    assert any("config" in error for error in errors)


def test_workspace_context_manager(temp_dir):
    """Test workspace context manager."""
    # Create a workspace
    workspace = Workspace(temp_dir)
    workspace.initialize()
    
    # Test context manager with explicit path
    with WorkspaceContext(temp_dir) as ws:
        assert ws.root_path == temp_dir
        assert ws.is_initialized()
    
    # Test with invalid workspace
    invalid_dir = temp_dir / "invalid"
    invalid_dir.mkdir()
    
    with pytest.raises(WorkspaceValidationError):
        with WorkspaceContext(invalid_dir) as ws:
            pass
            
    # Test contextmanager function
    with workspace_context(temp_dir) as ws:
        assert ws.root_path == temp_dir
        assert ws.is_initialized()


def test_workspace_config_defaults():
    """Test workspace config default values."""
    config = WorkspaceConfig()
    assert config.get("version") == "0.1.0"
    assert config.get("name") == "airic-workspace"
    assert config.get("created_at") is None
    assert "document-driven AI collaboration" in config.get("description") 