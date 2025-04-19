"""
Tests for markdown utilities.
"""
import tempfile
from pathlib import Path

import pytest
import frontmatter

from airic.utils.markdown import (
    parse_markdown_file, extract_wikilinks, extract_frontmatter,
    get_metadata_field, find_wikilinks, parse_wikilink,
    MarkdownDocument
)


def test_extract_frontmatter():
    """Test extracting frontmatter from a file."""
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
                
            # Extract frontmatter
            metadata, content = extract_frontmatter(temp_path)
            
            # Check metadata
            assert metadata["title"] == "Test Document"
            assert metadata["agent"] == "test_agent"
            assert metadata["doctype"] == "test_doctype"
            assert metadata["status"] == "draft"
            
            # Check content
            assert "# Test Content" in content
            assert "This is a test document with [[link1]] and [[link2]]." in content
            
        finally:
            # Clean up
            temp_path.unlink()


def test_extract_frontmatter_str_path():
    """Test extracting frontmatter using string path."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp:
        temp_path = temp.name
        try:
            # Create a test markdown file with frontmatter
            md_content = """---
title: Test Document
---

# Content
"""
            with open(temp_path, "w") as f:
                f.write(md_content)
                
            # Extract frontmatter using string path
            metadata, content = extract_frontmatter(temp_path)
            
            # Check metadata
            assert metadata["title"] == "Test Document"
            assert "# Content" in content
            
        finally:
            # Clean up
            Path(temp_path).unlink()


def test_extract_frontmatter_file_not_found():
    """Test extracting frontmatter from non-existent file."""
    with pytest.raises(FileNotFoundError):
        extract_frontmatter("non_existent_file.md")


def test_get_metadata_field():
    """Test getting metadata fields with default values."""
    metadata = {
        "title": "Test Document",
        "tags": ["test", "markdown"]
    }
    
    # Existing field
    assert get_metadata_field(metadata, "title") == "Test Document"
    assert get_metadata_field(metadata, "tags") == ["test", "markdown"]
    
    # Non-existent field with default
    assert get_metadata_field(metadata, "doctype", "note") == "note"
    
    # Non-existent field without default
    assert get_metadata_field(metadata, "status") is None


def test_find_wikilinks():
    """Test finding WikiLinks in content."""
    content = """
    # Test Document
    
    This is a test document with [[link1]] and [[link2]].
    
    Multiple links on the same line: [[link3]] and [[link4]].
    
    Complex links: [[link with spaces]] and [[target|display text]].
    """
    
    links = find_wikilinks(content)
    assert len(links) == 6
    assert "[[link1]]" in links
    assert "[[link2]]" in links
    assert "[[link3]]" in links
    assert "[[link4]]" in links
    assert "[[link with spaces]]" in links
    assert "[[target|display text]]" in links


def test_parse_wikilink():
    """Test parsing WikiLinks into components."""
    # Regular WikiLink
    link = parse_wikilink("[[test page]]")
    assert link["target"] == "test page"
    assert link["display_text"] == "test page"
    
    # WikiLink with display text
    link = parse_wikilink("[[target|display text]]")
    assert link["target"] == "target"
    assert link["display_text"] == "display text"
    
    # WikiLink with extra spaces
    link = parse_wikilink("[[  spaced target  |  display text  ]]")
    assert link["target"] == "spaced target"
    assert link["display_text"] == "display text"
    
    # Invalid WikiLink
    with pytest.raises(ValueError):
        parse_wikilink("not a wikilink")


def test_extract_wikilinks():
    """Test extracting wikilinks from content."""
    content = """
    # Test Document
    
    This is a test document with [[link1]] and [[link2]].
    
    Multiple links on the same line: [[link3]] and [[link4]].
    
    Nested links don't work: [[link5 with [[nested]]]]
    
    But [[links/with/paths]] and [[links with spaces]] work fine.
    
    Links with display text: [[actual target|display text]]
    """
    
    links = extract_wikilinks(content)
    assert len(links) == 8
    assert "link1" in links
    assert "link2" in links
    assert "link3" in links
    assert "link4" in links
    assert "nested" in links  # Only the inner nested part is extracted
    assert "links/with/paths" in links
    assert "links with spaces" in links
    assert "actual target" in links  # Only the target part, not display text


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


def test_markdown_document_init():
    """Test initializing a MarkdownDocument from a file."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp:
        temp_path = Path(temp.name)
        try:
            # Create a test markdown file with frontmatter
            md_content = """---
title: Test Document
doctype: note
tags: tag1, tag2, tag3
---

# Test Content

This is a test document with [[link1]] and [[link2|Display Text]].
"""
            with open(temp_path, "w") as f:
                f.write(md_content)
                
            # Create MarkdownDocument
            doc = MarkdownDocument(temp_path)
            
            # Check basic properties
            assert doc.title == "Test Document"
            assert doc.doctype == "note"
            assert doc.tags == ["tag1", "tag2", "tag3"]
            assert "# Test Content" in doc.content
            
            # Check WikiLinks
            links = doc.get_wikilinks()
            assert len(links) == 2
            assert links[0]["target"] == "link1"
            assert links[0]["display_text"] == "link1"
            assert links[1]["target"] == "link2"
            assert links[1]["display_text"] == "Display Text"
            
            # Check raw WikiLinks
            raw_links = doc.get_raw_wikilinks()
            assert len(raw_links) == 2
            assert "link1" in raw_links
            assert "link2" in raw_links
            
        finally:
            # Clean up
            temp_path.unlink()


def test_markdown_document_from_string():
    """Test creating a MarkdownDocument from a string."""
    md_content = """---
title: String Document
doctype: agent
tags:
  - test
  - markdown
---

# String Content

This is created from a string with [[link]].
"""
    
    doc = MarkdownDocument.from_string(md_content, "virtual.md")
    
    # Check basic properties
    assert doc.title == "String Document"
    assert doc.doctype == "agent"
    assert doc.tags == ["test", "markdown"]
    assert doc.file_path.name == "virtual.md"
    assert "# String Content" in doc.content
    
    # Check WikiLinks
    links = doc.get_wikilinks()
    assert len(links) == 1
    assert links[0]["target"] == "link"
    
    # Create without path
    doc2 = MarkdownDocument.from_string(md_content)
    assert doc2.file_path is None


def test_markdown_document_metadata_access():
    """Test accessing metadata fields in a MarkdownDocument."""
    md_content = """---
title: Test
doctype: note
custom: value
nested:
  key: nested_value
---

Content
"""
    
    doc = MarkdownDocument.from_string(md_content)
    
    # Standard properties
    assert doc.title == "Test"
    assert doc.doctype == "note"
    
    # Custom field access
    assert doc.get_metadata_field("custom") == "value"
    assert doc.get_metadata_field("nested") == {"key": "nested_value"}
    assert doc.get_metadata_field("non_existent") is None
    assert doc.get_metadata_field("non_existent", "default") == "default"


def test_markdown_document_validate_frontmatter():
    """Test frontmatter validation in MarkdownDocument."""
    # Valid document with all fields
    doc1 = MarkdownDocument.from_string("""---
title: Test
doctype: note
---
Content
""")
    assert doc1.validate_frontmatter() is True
    
    # Missing title
    doc2 = MarkdownDocument.from_string("""---
doctype: note
---
Content
""")
    assert doc2.validate_frontmatter() is False
    
    # Custom required fields
    doc3 = MarkdownDocument.from_string("""---
title: Test
doctype: note
---
Content
""")
    assert doc3.validate_frontmatter(["title", "author"]) is False
    
    # Agent document type
    doc4 = MarkdownDocument.from_string("""---
title: Agent
doctype: agent
agent: test_agent
---
Content
""")
    assert doc4.validate_frontmatter() is True


def test_markdown_document_validate_wikilinks():
    """Test WikiLink validation in MarkdownDocument."""
    # All valid links
    doc1 = MarkdownDocument.from_string("""---
title: Test
---
Text with [[valid link]] and [[another/valid/link]].
""")
    assert doc1.validate_wikilinks() == []
    
    # Invalid links
    doc2 = MarkdownDocument.from_string("""---
title: Test
---
Text with [[]] and [[invalid:link]] and [[valid link]].
""")
    problematic = doc2.validate_wikilinks()
    assert len(problematic) == 2
    assert "[[]]" in problematic
    assert "[[invalid:link]]" in problematic 