"""
Utilities for Markdown parsing and processing.
"""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import frontmatter

logger = logging.getLogger(__name__)

def extract_frontmatter(file_path: Union[str, Path]) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter from a Markdown file.
    
    Args:
        file_path: Path to the Markdown file
        
    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If there's an error parsing the frontmatter
        PermissionError: If the file cannot be accessed due to permissions
        UnicodeDecodeError: If the file has invalid UTF-8 encoding
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
        
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        post = frontmatter.load(file_path)
        metadata = dict(post.metadata)
        content = post.content
        return metadata, content
    except PermissionError as e:
        logger.error(f"Permission denied when accessing {file_path}: {e}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Invalid UTF-8 encoding in {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error parsing frontmatter in {file_path}: {e}")
        raise ValueError(f"Error parsing Markdown frontmatter: {e}")

def get_metadata_field(frontmatter: Dict[str, Any], field_name: str, default: Any = None) -> Any:
    """
    Safely extract a specific field from frontmatter.
    
    Args:
        frontmatter: Dictionary containing frontmatter metadata
        field_name: Name of the field to extract
        default: Default value to return if field doesn't exist
        
    Returns:
        Value of the field or default if not found
    """
    return frontmatter.get(field_name, default)

def find_wikilinks(content: str) -> List[str]:
    """
    Find all WikiLinks ([[link]]) in Markdown content.
    
    Args:
        content: Markdown content to search
        
    Returns:
        List of all raw WikiLinks found (including brackets)
    """
    # Match pattern [[anything]] and return the whole match
    pattern = r'\[\[([^\[\]]*?(?:\[[^\[\]]*?\][^\[\]]*?)*?)\]\]'
    matches = re.findall(pattern, content)
    return [f"[[{match}]]" for match in matches]

def parse_wikilink(wikilink: str) -> Dict[str, str]:
    """
    Parse a WikiLink into its components.
    
    Args:
        wikilink: Raw WikiLink string (e.g., "[[Some Page]]" or "[[Some Page|Display Text]]")
        
    Returns:
        Dictionary with 'target' and 'display_text' keys
        
    Raises:
        ValueError: If the WikiLink format is invalid
    """
    # Remove outer brackets
    if not (wikilink.startswith("[[") and wikilink.endswith("]]")):
        raise ValueError(f"Invalid WikiLink format: {wikilink}")
    
    link_text = wikilink[2:-2].strip()
    
    # Handle [[target|display]] format
    if "|" in link_text:
        target, display_text = link_text.split("|", 1)
        return {
            "target": target.strip(),
            "display_text": display_text.strip()
        }
    
    # Regular [[target]] format
    return {
        "target": link_text,
        "display_text": link_text
    }

def extract_wikilinks(content: str) -> List[str]:
    """
    Extract WikiLinks targets (without brackets) from content.
    
    Args:
        content: Markdown content to extract links from
        
    Returns:
        List of link targets (without the brackets)
    """
    # Match pattern [[link]] and extract 'link'
    pattern = r'\[\[([^\[\]]*?(?:\[[^\[\]]*?\][^\[\]]*?)*?)\]\]'
    matches = re.findall(pattern, content)
    
    # Process pipes in WikiLinks: [[target|display]] -> target
    processed_links = []
    for match in matches:
        if "|" in match:
            target, _ = match.split("|", 1)
            processed_links.append(target.strip())
        else:
            processed_links.append(match.strip())
            
    return processed_links

def parse_markdown_file(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """
    Parse a Markdown file and extract frontmatter metadata and content.
    
    Args:
        file_path: Path to the Markdown file
        
    Returns:
        Tuple of (metadata dict, content string)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file cannot be parsed as Markdown
    """
    return extract_frontmatter(file_path)


class MarkdownDocument:
    """
    Class representing a Markdown document with frontmatter and content.
    """
    
    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize a Markdown document from a file.
        
        Args:
            file_path: Path to the Markdown file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If there's an error parsing the frontmatter
        """
        self.file_path = Path(file_path) if isinstance(file_path, str) else file_path
        self._metadata, self._content = extract_frontmatter(self.file_path)
        self._wikilinks = None  # Cached wikilinks
        
    @classmethod
    def from_string(cls, content: str, path: Optional[str] = None) -> 'MarkdownDocument':
        """
        Create a MarkdownDocument from a string.
        
        Args:
            content: String containing markdown content with optional frontmatter
            path: Optional path to associate with the document
            
        Returns:
            MarkdownDocument instance
        """
        instance = cls.__new__(cls)
        
        # Parse the string
        post = frontmatter.loads(content)
        instance._metadata = dict(post.metadata)
        instance._content = post.content
        instance._wikilinks = None
        
        # Set a placeholder path if none provided
        instance.file_path = Path(path) if path else None
        
        return instance
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the document's metadata."""
        return self._metadata
        
    @property
    def content(self) -> str:
        """Get the document's content without frontmatter."""
        return self._content
        
    @property
    def title(self) -> Optional[str]:
        """Get the document's title from metadata."""
        return get_metadata_field(self._metadata, 'title')
        
    @property
    def doctype(self) -> Optional[str]:
        """Get the document's doctype from metadata."""
        return get_metadata_field(self._metadata, 'doctype')
        
    @property
    def tags(self) -> List[str]:
        """Get the document's tags from metadata."""
        tags = get_metadata_field(self._metadata, 'tags', [])
        if isinstance(tags, str):
            # Split comma-separated tags
            return [tag.strip() for tag in tags.split(',')]
        return tags
        
    def get_metadata_field(self, field_name: str, default: Any = None) -> Any:
        """Get a specific metadata field."""
        return get_metadata_field(self._metadata, field_name, default)
        
    def get_wikilinks(self) -> List[Dict[str, str]]:
        """
        Get all WikiLinks in the document as structured objects.
        
        Returns:
            List of dictionaries with 'target' and 'display_text' keys
        """
        if self._wikilinks is None:
            raw_links = find_wikilinks(self._content)
            self._wikilinks = [parse_wikilink(link) for link in raw_links]
        return self._wikilinks
        
    def get_raw_wikilinks(self) -> List[str]:
        """
        Get just the WikiLink targets.
        
        Returns:
            List of WikiLink targets
        """
        return extract_wikilinks(self._content)
        
    def validate_frontmatter(self, required_fields: List[str] = None) -> bool:
        """
        Validate that the frontmatter contains required fields.
        
        Args:
            required_fields: List of field names that must be present
            
        Returns:
            True if valid, False otherwise
        """
        if required_fields is None:
            # Default required fields based on doctype
            doctype = self.doctype
            if doctype == 'note':
                required_fields = ['title']
            elif doctype == 'agent':
                required_fields = ['title', 'agent']
            else:
                required_fields = ['title']
                
        for field in required_fields:
            if field not in self._metadata:
                logger.warning(f"Missing required field '{field}' in {self.file_path}")
                return False
                
        return True
        
    def validate_wikilinks(self) -> List[str]:
        """
        Identify potentially broken or malformed WikiLinks.
        
        Returns:
            List of problematic WikiLinks
        """
        problematic = []
        for link in self.get_wikilinks():
            target = link['target']
            # Check for empty targets
            if not target.strip():
                problematic.append(f"[[{target}]]")
            # Check for targets with invalid characters
            elif re.search(r'[<>:"|?*]', target):
                problematic.append(f"[[{target}]]")
                
        return problematic 