"""
Tests for the Document class.
"""
import pytest
import tempfile
from pathlib import Path
from airic.core.document import Document, DocumentError


class TestDocument:
    """Test suite for the Document class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_init_with_content(self):
        """Test initializing a document with explicit content."""
        path = Path("test.md")
        content = "# Test Document\n\nThis is a test."
        doc = Document(path, content)
        
        assert doc.path == path
        assert doc.name == "test.md"
        assert doc.body == content
        assert doc.metadata == {}
    
    def test_init_with_frontmatter(self):
        """Test initializing a document with frontmatter."""
        path = Path("test.md")
        content = """---
title: Test Document
doctype: test
version: 1.0.0
---

# Test Document

This is a test."""
        
        doc = Document(path, content)
        
        assert doc.path == path
        assert doc.doctype == "test"
        assert doc.metadata["title"] == "Test Document"
        assert doc.metadata["version"] == "1.0.0"
        assert "# Test Document" in doc.body
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading a document."""
        path = temp_dir / "test.md"
        doc = Document.create_empty(path, {"doctype": "test"}, "Test Document")
        
        # Save the document
        doc.save()
        assert path.exists()
        
        # Load the document
        loaded_doc = Document(path)
        assert loaded_doc.doctype == "test"
        assert loaded_doc.metadata["title"] == "Test Document"
        assert "# Test Document" in loaded_doc.body
    
    def test_update_metadata(self):
        """Test updating document metadata."""
        path = Path("test.md")
        doc = Document.create_empty(path, {"doctype": "test"}, "Test Document")
        
        # Update metadata
        doc.update_metadata({"version": "1.0.0", "author": "Test Author"})
        
        assert doc.metadata["doctype"] == "test"
        assert doc.metadata["version"] == "1.0.0"
        assert doc.metadata["author"] == "Test Author"
        
        # Check that content is reserializaed
        assert "version: 1.0.0" in doc.content
        assert "author: Test Author" in doc.content
    
    def test_update_body(self):
        """Test updating document body."""
        path = Path("test.md")
        doc = Document.create_empty(path, {"doctype": "test"}, "Test Document")
        
        # Update body
        new_body = "# Updated Title\n\nThis is updated content."
        doc.update_body(new_body)
        
        assert doc.body == new_body
        assert doc.metadata["doctype"] == "test"
        assert new_body in doc.content
    
    def test_validate_metadata(self):
        """Test validating document metadata."""
        path = Path("test.md")
        doc = Document.create_empty(path, {"doctype": "test"}, "Test Document")
        
        # Validate with no required fields
        errors = doc.validate_metadata()
        assert not errors
        
        # Validate with existing fields
        errors = doc.validate_metadata(["doctype", "title"])
        assert not errors
        
        # Validate with missing fields
        errors = doc.validate_metadata(["author", "version"])
        assert len(errors) == 2
        assert "author" in errors[0]
        assert "version" in errors[1]
    
    def test_create_empty(self):
        """Test creating an empty document."""
        path = Path("test.md")
        doc = Document.create_empty(path, {"doctype": "test"}, "Custom Title")
        
        assert doc.path == path
        assert doc.doctype == "test"
        assert doc.metadata["title"] == "Custom Title"
        assert "# Custom Title" in doc.body
        
        # Test with default title derived from path
        path = Path("test_document.md")
        doc = Document.create_empty(path, {"doctype": "test"})
        
        assert doc.metadata["title"] == "Test Document"
        assert "# Test Document" in doc.body 