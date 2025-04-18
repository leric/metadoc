"""
Tests for workspace initialization functionality.
"""
import os
import tempfile
import shutil
import yaml
from pathlib import Path
import pytest

from airic.core.init import initialize_workspace, DEFAULT_TEMPLATES, _rollback_initialization, create_template_file
from airic.core.workspace import Workspace


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


def test_initialize_workspace_basic(temp_dir):
    """Test basic workspace initialization."""
    # Initialize workspace
    success, errors = initialize_workspace(temp_dir)
    
    # Check success
    assert success
    assert not errors
    
    # Check directory structure
    workspace = Workspace(temp_dir)
    assert workspace.is_initialized()
    assert workspace.config_path.exists()
    
    # Check for template files
    for template_path in DEFAULT_TEMPLATES.keys():
        template_file = workspace.meta_dir / template_path
        assert template_file.exists()
        
    # Check README.md was created
    readme_path = temp_dir / "README.md"
    assert readme_path.exists()


def test_initialize_workspace_custom_config(temp_dir):
    """Test workspace initialization with custom configuration."""
    # Custom config
    config = {
        "name": "Test Workspace",
        "description": "A test workspace",
        "custom_setting": "value"
    }
    
    # Initialize workspace
    success, errors = initialize_workspace(temp_dir, config)
    
    # Check success
    assert success
    assert not errors
    
    # Check configuration was saved
    workspace = Workspace(temp_dir)
    assert workspace.config.get("name") == "Test Workspace"
    assert workspace.config.get("description") == "A test workspace"
    assert workspace.config.get("custom_setting") == "value"
    
    # Check README.md content
    readme_path = temp_dir / "README.md"
    with open(readme_path, "r") as f:
        content = f.read()
        assert "Test Workspace" in content
        assert "A test workspace" in content


def test_initialize_workspace_already_initialized(temp_dir):
    """Test initializing already initialized workspace."""
    # Initialize once
    success1, errors1 = initialize_workspace(temp_dir)
    assert success1
    
    # Initialize again
    success2, errors2 = initialize_workspace(temp_dir)
    assert success2  # Should still return success
    assert len(errors2) == 1
    assert "already initialized" in errors2[0]


def test_initialize_workspace_with_permission_error(temp_dir, monkeypatch):
    """Test initialization with permission error."""
    
    # Mock makedirs to raise PermissionError
    original_makedirs = os.makedirs
    
    def mock_makedirs(path, *args, **kwargs):
        # Let it create .airic directory but fail on meta dir
        if isinstance(path, Path):
            path_str = str(path)
        else:
            path_str = path
            
        if ".airic/meta" in path_str and ".airic/meta/" not in path_str:
            raise PermissionError("Permission denied")
        return original_makedirs(path, *args, **kwargs)
    
    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    
    # Initialize workspace
    success, errors = initialize_workspace(temp_dir)
    
    # Check failure
    assert not success
    assert len(errors) == 1
    assert "Permission denied" in errors[0]
    
    # In our implementation, the rollback removes empty directories
    # So .airic might be removed if it's empty
    # What's important is that meta directories weren't created
    meta_dir = temp_dir / ".airic" / "meta"
    assert not meta_dir.exists()


def test_initialize_workspace_with_template_error(temp_dir, monkeypatch):
    """Test initialization with error creating templates."""
    
    # Mock open to raise IOError when creating template files
    # But only do this for the first template file to let the others succeed
    original_open = open
    
    def mock_open(file, *args, **kwargs):
        # Convert to string if it's a Path
        if hasattr(file, '__fspath__'):
            file_str = file.__fspath__()
        else:
            file_str = str(file)
            
        # Only fail on this specific file
        if "agents/default.md" in file_str:
            raise IOError("Failed to create file")
        return original_open(file, *args, **kwargs)
    
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Initialize workspace
    success, errors = initialize_workspace(temp_dir)
    
    # Check failure
    assert not success
    assert len(errors) == 1
    assert "template files" in errors[0]
    
    # Directories may have been created but config file should have been rolled back
    workspace = Workspace(temp_dir)
    # Even if .airic was created and not removed in rollback, the config file should be gone
    assert not workspace.config_path.exists()


def test_initialize_workspace_with_os_error(temp_dir, monkeypatch):
    """Test initialization with OSError during directory creation."""
    
    # Mock makedirs to raise OSError
    original_makedirs = os.makedirs
    
    def mock_makedirs(path, *args, **kwargs):
        if ".airic/meta/doctypes" in str(path):
            raise OSError("Simulated OS error")
        return original_makedirs(path, *args, **kwargs)
    
    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    
    # Initialize workspace
    success, errors = initialize_workspace(temp_dir)
    
    # Check failure
    assert not success
    assert len(errors) == 1
    assert "Error creating workspace directories" in errors[0]
    assert "Simulated OS error" in errors[0]
    
    # Check that the rollback was performed
    doctypes_dir = temp_dir / ".airic" / "meta" / "doctypes"
    assert not doctypes_dir.exists()


def test_initialize_workspace_with_readme_error(temp_dir, monkeypatch):
    """Test initialization with error creating README.md."""
    
    # First create a file with the same name as the README.md but make it a directory
    # This will cause an error when trying to write to it
    readme_dir = temp_dir / "README.md"
    readme_dir.mkdir()
    
    # Initialize workspace (should still succeed despite README error)
    success, errors = initialize_workspace(temp_dir)
    
    # Check success (README errors are non-critical)
    assert success
    assert not errors
    
    # Check directory structure was created
    workspace = Workspace(temp_dir)
    assert workspace.is_initialized()
    assert workspace.config_path.exists()


def test_rollback_with_errors(temp_dir):
    """Test rollback functionality with errors during cleanup."""
    
    # Create some test files and directories to roll back
    test_dir = temp_dir / "test_dir"
    test_dir.mkdir()
    
    test_file = temp_dir / "test_file.txt"
    with open(test_file, "w") as f:
        f.write("test content")
    
    # Create a directory that can't be removed (contains files)
    nested_dir = temp_dir / "nested_dir"
    nested_dir.mkdir()
    nested_file = nested_dir / "nested_file.txt"
    with open(nested_file, "w") as f:
        f.write("nested content")
    
    # Perform rollback - this should handle errors gracefully
    _rollback_initialization([test_dir, nested_dir], [test_file])
    
    # test_file and test_dir should be gone, but nested_dir should remain
    assert not test_file.exists()
    assert not test_dir.exists()
    assert nested_dir.exists()
    assert nested_file.exists()


def test_initialize_workspace_with_config_error(temp_dir, monkeypatch):
    """Test initialization with error in config file creation."""
    
    # Allow directories to be created first
    # Then mock open to raise an error when trying to create config file
    original_open = open
    
    def mock_open(file, *args, **kwargs):
        # Convert to string if it's a Path
        if hasattr(file, '__fspath__'):
            file_str = file.__fspath__()
        else:
            file_str = str(file)
            
        # Fail only on config.yaml
        if "config.yaml" in file_str and "w" in args:
            raise IOError("Config file error")
        return original_open(file, *args, **kwargs)
    
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Initialize workspace
    success, errors = initialize_workspace(temp_dir)
    
    # Check failure
    assert not success
    assert len(errors) == 1
    assert "Error creating workspace configuration" in errors[0]
    
    # Check that rollback removed directories (or left them in an indeterminate state)
    # The key point is the config file should not exist
    workspace = Workspace(temp_dir)
    assert not workspace.config_path.exists()


def test_initialize_workspace_with_general_error(temp_dir, monkeypatch):
    """Test initialization with a general unexpected error."""
    
    # Mock Workspace constructor to raise an exception
    original_init = Workspace.__init__
    
    def mock_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        raise RuntimeError("Unexpected error")
    
    monkeypatch.setattr(Workspace, "__init__", mock_init)
    
    # Initialize workspace
    success, errors = initialize_workspace(temp_dir)
    
    # Check failure
    assert not success
    assert len(errors) == 1
    assert "Unexpected error during workspace initialization" in errors[0]


def test_create_template_file_with_nonexistent_parent(temp_dir):
    """Test creating a template file when parent directories don't exist."""
    
    test_path = temp_dir / "nonexistent_dir" / "template.md"
    
    # Create template file - should create parent directories
    create_template_file(test_path, "Test content")
    
    # Verify file was created
    assert test_path.exists()
    with open(test_path, "r") as f:
        assert f.read() == "Test content" 