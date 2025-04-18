"""
Utilities for Markdown parsing and processing.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import frontmatter


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
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        post = frontmatter.load(file_path)
        metadata = dict(post.metadata)
        content = post.content
        return metadata, content
    except Exception as e:
        raise ValueError(f"Error parsing Markdown file: {e}")


def extract_wikilinks(content: str) -> List[str]:
    """
    Extract WikiLinks ([[link]]) from content.
    
    Args:
        content: Markdown content to extract links from
        
    Returns:
        List of link targets (without the brackets)
    """
    # Match pattern [[link]] and extract 'link'
    pattern = r'\[\[(.*?)\]\]'
    matches = re.findall(pattern, content)
    return matches 