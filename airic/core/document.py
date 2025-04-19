"""
Document handling functionality for Airic.

This module defines the Document class for managing Markdown documents
with YAML frontmatter in an Airic workspace.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentError(Exception):
    """Exception raised for document-related errors."""
    pass


class Document:
    """
    Represents a Markdown document in the Airic workspace.
    
    Documents in Airic are Markdown files that can contain:
    - YAML frontmatter for metadata
    - Markdown content for the actual document
    
    The Document class handles loading, parsing, and saving these files,
    as well as extracting and validating their metadata.
    """
    
    def __init__(self, path: Path, content: Optional[str] = None):
        """
        Initialize a document from a file path or content.
        
        Args:
            path: Path to the document file
            content: Optional document content (if not loaded from file)
        """
        self.path = path
        self.name = path.name
        self._content = content
        self._metadata = {}
        self._body = ""
        
        # Load content if not provided
        if content is None and path.exists():
            self._load()
        elif content is not None:
            self._parse(content)
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the document's metadata from frontmatter."""
        return self._metadata
    
    @property
    def body(self) -> str:
        """Get the document's main content (without frontmatter)."""
        return self._body
    
    @property
    def content(self) -> str:
        """Get the full document content (including frontmatter)."""
        if self._content is None:
            self._content = self._serialize()
        return self._content
    
    @property
    def doctype(self) -> Optional[str]:
        """Get the document type from metadata."""
        return self._metadata.get('doctype')
    
    @property
    def agent(self) -> Optional[str]:
        """Get the specified agent for this document from metadata."""
        return self._metadata.get('agent')
    
    def _load(self) -> None:
        """
        Load the document content from its file path.
        
        Raises:
            DocumentError: If the file cannot be read
        """
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._parse(content)
        except Exception as e:
            raise DocumentError(f"Failed to load document {self.path}: {str(e)}")
    
    def _parse(self, content: str) -> None:
        """
        Parse document content to extract frontmatter and body.
        
        Args:
            content: Document content to parse
        """
        self._content = content
        
        # Check for frontmatter delimiter
        frontmatter_separator = '---'
        if content.startswith(frontmatter_separator):
            # Find the end of the frontmatter
            second_separator = content.find(frontmatter_separator, len(frontmatter_separator))
            if second_separator != -1:
                # Extract frontmatter and body
                frontmatter = content[len(frontmatter_separator):second_separator].strip()
                self._body = content[second_separator + len(frontmatter_separator):].strip()
                
                # Parse frontmatter as YAML
                try:
                    # Safe load already captures all keys, including 'agent' if present
                    self._metadata = yaml.safe_load(frontmatter) or {}
                except Exception as e:
                    logger.warning(f"Failed to parse frontmatter in {self.path}: {str(e)}")
                    self._metadata = {}
            else:
                # No end separator found, treat entire content as body
                self._body = content
                self._metadata = {}
        else:
            # No frontmatter, treat entire content as body
            self._body = content
            self._metadata = {}
    
    def _serialize(self) -> str:
        """
        Serialize the document metadata and body back to a string.
        
        Returns:
            Full document content with frontmatter
        """
        if not self._metadata:
            return self._body
        
        # Convert metadata to YAML
        try:
            yaml_str = yaml.dump(self._metadata, default_flow_style=False)
            return f"---\n{yaml_str}---\n\n{self._body}"
        except Exception as e:
            logger.error(f"Failed to serialize document metadata: {str(e)}")
            return self._body
    
    def save(self) -> None:
        """
        Save the document to its file path.
        
        Raises:
            DocumentError: If the file cannot be written
        """
        try:
            # Ensure parent directory exists
            self.path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write document content
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(self.content)
        except Exception as e:
            raise DocumentError(f"Failed to save document {self.path}: {str(e)}")
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update document metadata.
        
        Args:
            metadata: New metadata to merge with existing metadata
        """
        self._metadata.update(metadata)
        self._content = None  # Force re-serialization on next access
    
    def update_body(self, body: str) -> None:
        """
        Update document body content.
        
        Args:
            body: New body content
        """
        self._body = body
        self._content = None  # Force re-serialization on next access
    
    def validate_metadata(self, required_fields: List[str] = None) -> List[str]:
        """
        Validate document metadata against required fields.
        
        Args:
            required_fields: List of required metadata fields
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if required_fields:
            for field in required_fields:
                if field not in self._metadata:
                    errors.append(f"Missing required metadata field: {field}")
        
        return errors
    
    @staticmethod
    def create_empty(path: Path, metadata: Optional[Dict[str, Any]] = None, title: Optional[str] = None) -> 'Document':
        """
        Create a new empty document.
        
        Args:
            path: Path where the document will be saved
            metadata: Optional initial metadata
            title: Optional document title (extracted from path if not provided)
            
        Returns:
            New Document instance
        """
        # Generate title from path if not provided
        if title is None:
            title = path.stem.replace('_', ' ').title()
        
        # Generate default metadata
        default_metadata = {
            'created_at': datetime.now().isoformat(),
            'title': title
        }
        
        # Merge with provided metadata
        if metadata:
            default_metadata.update(metadata)
        
        # Create initial content
        body = f"# {title}\n\nYour content here...\n"
        
        # Generate YAML frontmatter
        yaml_str = yaml.dump(default_metadata, default_flow_style=False)
        content = f"---\n{yaml_str}---\n\n{body}"
        
        # Create document instance
        doc = Document(path, content)
        return doc


def find_documents(directory: Path, pattern: str = "*.md") -> List[Document]:
    """
    Find all documents in a directory matching a pattern.
    
    Args:
        directory: Directory to search in
        pattern: Glob pattern to match files (default: "*.md")
        
    Returns:
        List of Document instances
    """
    if not directory.exists() or not directory.is_dir():
        return []
    
    documents = []
    for path in directory.glob(pattern):
        if path.is_file():
            try:
                doc = Document(path)
                documents.append(doc)
            except DocumentError as e:
                logger.warning(f"Failed to load document {path}: {str(e)}")
    
    return documents 