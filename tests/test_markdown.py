"""
Tests for markdown utilities.
"""
import tempfile
from pathlib import Path

import pytest
import frontmatter

from airic.utils.markdown import parse_markdown_file, extract_wikilinks


def test_extract_wikilinks():
    """Test extracting wikilinks from content."""
    content = """
    # Test Document
    
    This is a test document with [[link1]] and [[link2]].
    
    Multiple links on the same line: [[link3]] and [[link4]].
    
    Nested links don't work: [[link5 with [[nested]]]]
    
    But [[links/with/paths]] and [[links with spaces]] work fine.
    """
    
    links = extract_wikilinks(content)
    assert len(links) == 7
    assert "link1" in links
    assert "link2" in links
    assert "link3" in links
    assert "link4" in links
    assert "link5 with [[nested" in links  # Not ideal but expected behavior with regex
    assert "links/with/paths" in links
    assert "links with spaces" in links


def test_parse_markdown_file():
    """Test parsing a markdown file with frontmatter."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp:
        temp_path = Path(temp.name)
        try:
            # Create a test markdown file with frontmatter
            md_content = """---
title: Test Document
agent: test_agent
doctype: test_doctype
status: draft
---

# Test Content

This is a test document with [[link1]] and [[link2]].
"""
            with open(temp_path, "w") as f:
                f.write(md_content)
                
            # Parse the file
            metadata, content = parse_markdown_file(temp_path)
            
            # Check metadata
            assert metadata["title"] == "Test Document"
            assert metadata["agent"] == "test_agent"
            assert metadata["doctype"] == "test_doctype"
            assert metadata["status"] == "draft"
            
            # Check content
            assert "# Test Content" in content
            assert "This is a test document with [[link1]] and [[link2]]." in content
            
            # Extract links from content
            links = extract_wikilinks(content)
            assert len(links) == 2
            assert "link1" in links
            assert "link2" in links
            
        finally:
            # Clean up
            temp_path.unlink()
            
            
def test_parse_markdown_file_no_frontmatter():
    """Test parsing a markdown file without frontmatter."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp:
        temp_path = Path(temp.name)
        try:
            # Create a test markdown file without frontmatter
            md_content = """# Test Content

This is a test document with no frontmatter.
"""
            with open(temp_path, "w") as f:
                f.write(md_content)
                
            # Parse the file
            metadata, content = parse_markdown_file(temp_path)
            
            # Check metadata (should be empty)
            assert metadata == {}
            
            # Check content
            assert "# Test Content" in content
            assert "This is a test document with no frontmatter." in content
            
        finally:
            # Clean up
            temp_path.unlink()


def test_parse_markdown_file_not_found():
    """Test parsing a non-existent file."""
    non_existent_file = Path("non_existent_file.md")
    with pytest.raises(FileNotFoundError):
        parse_markdown_file(non_existent_file) 