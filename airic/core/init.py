"""
Workspace initialization functionality.
"""
import os
import yaml
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from airic.core.workspace import Workspace

logger = logging.getLogger(__name__)


# Default templates for workspace files
DEFAULT_TEMPLATES = {
    # Default template for a basic agent
    "agents/default.md": """---
name: default
description: A basic agent that responds to documents without specific formatting
version: 0.1.0
---

# Default Agent

You are a helpful AI assistant that can discuss and assist with any document.
When working with a document that doesn't have a specific agent or doctype associated with it,
you will act as a general-purpose assistant.

## Guidelines

- Be concise and direct in responses
- Ask clarifying questions when the user's intent is unclear
- Suggest relevant commands or document types when appropriate
- Help with exploring and understanding documents in the workspace
""",

    # Default template for a writer agent
    "agents/writer.md": """---
name: writer
description: An agent specialized in helping with writing and editing text documents
version: 0.1.0
---

# Writer Agent

You are a specialized AI assistant focused on helping users with writing and editing documents.
You excel at improving text clarity, structure, grammar, and style.

## Guidelines

- Focus on improving the document's readability and impact
- Suggest structural improvements when appropriate
- Help with word choice and phrasing
- Check for consistency in tone and style
- Point out grammatical issues and suggest corrections
- Ask for clarification about the target audience and purpose if needed
""",

    # Default template for a meeting notes doctype
    "doctypes/meeting_notes.md": """---
name: meeting_notes
description: Template and guidelines for meeting notes and summaries
version: 0.1.0
---

# Meeting Notes Document Type

This document type is designed for capturing and organizing meeting notes in a clear, structured format.

## Structure

Meeting notes should include the following sections:

1. **Meeting Information**
   - Date and time
   - Participants
   - Meeting purpose/agenda

2. **Discussion Points**
   - Key topics discussed
   - Decisions made
   - Action items with assignees and deadlines

3. **Next Steps**
   - Follow-up meetings
   - Deadlines and milestones

## Example

```
# Project Kickoff Meeting

**Date:** 2025-04-15
**Time:** 10:00-11:30
**Participants:** Alice, Bob, Charlie

## Agenda
1. Project overview
2. Timeline discussion
3. Task assignments

## Discussion
- Alice presented the project goals and constraints
- Team agreed on the two-week sprint schedule
- Concerns raised about the API integration timeline

## Action Items
- [ ] Bob: Create project repository (Due: Apr 16)
- [ ] Charlie: Draft API specifications (Due: Apr 18)
- [ ] Alice: Schedule technical architecture review (Due: Apr 20)

## Next Meeting
- Technical review on April 20, 14:00
```
""",

    # Default template for a brainstorming doctype
    "doctypes/brainstorming.md": """---
name: brainstorming
description: Structure and guidelines for brainstorming sessions
version: 0.1.0
---

# Brainstorming Document Type

This document type is designed for creative ideation sessions and capturing unstructured thoughts that can later be refined into more formal documents or tasks.

## Structure

Brainstorming documents should include:

1. **Context/Problem Statement**
   - Clear description of the challenge or opportunity
   - Any constraints or requirements

2. **Ideas Section**
   - Unfiltered list of ideas and concepts
   - Questions to explore further
   - Connections between different concepts

3. **Next Steps**
   - Ideas worthy of deeper exploration
   - Action items to validate or develop concepts

## Guidelines for Effective Brainstorming

- Focus on quantity of ideas first, evaluation later
- Build on others' ideas with "yes, and..." thinking
- Avoid critiquing ideas during the generation phase
- Use lists, mind maps, or other visual structures
- Capture peripheral thoughts even if they seem tangential
""",

    # Default template for a workflow
    "workflows/document_review.md": """---
name: document_review
description: A workflow for systematically reviewing and improving documents
version: 0.1.0
doctype: workflow
---

# Document Review Workflow

This workflow defines a systematic process for reviewing and improving documents in a collaborative environment.

## Stages

1. **Initial Assessment**
   - Identify document type and purpose
   - Determine appropriate review criteria
   - Set review priorities (structure, content, grammar, etc.)

2. **Content Review**
   - Evaluate whether the document achieves its purpose
   - Check for completeness of information
   - Assess logical flow and organization

3. **Language Review**
   - Check grammar and spelling
   - Improve clarity and conciseness
   - Ensure consistent tone and terminology

4. **Finalization**
   - Implement accepted changes
   - Update metadata (version, last reviewed date)
   - Document decisions made during review

## Usage

To use this workflow:

1. Create a new document with metadata referencing this workflow: `workflow: document_review`
2. Work through each stage systematically
3. Use checkboxes to track progress: `- [x] Completed initial assessment`
"""
}


def create_template_file(dest_path: Path, template_content: str) -> None:
    """
    Create a file from a template.
    
    Args:
        dest_path: Destination path for the template file
        template_content: Content for the template file
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, 'w') as f:
        f.write(template_content)


def initialize_workspace(directory: Path, config: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    Initialize a workspace with all necessary directories and default templates.
    This is an enhanced version of Workspace.initialize() with better error handling
    and default templates.
    
    Args:
        directory: Directory to initialize as workspace
        config: Optional workspace configuration
        
    Returns:
        Tuple of (success, error_messages)
    """
    created_dirs = []
    created_files = []
    error_messages = []
    
    try:
        # Create a workspace instance
        workspace = Workspace(directory)
        
        # Check if already initialized
        if workspace.is_initialized():
            return (True, ["Workspace already initialized"])
            
        # Create core directories
        try:
            os.makedirs(workspace.airic_dir, exist_ok=True)
            created_dirs.append(workspace.airic_dir)
            
            os.makedirs(workspace.meta_dir, exist_ok=True)
            created_dirs.append(workspace.meta_dir)
            
            os.makedirs(workspace.agents_dir, exist_ok=True)
            created_dirs.append(workspace.agents_dir)
            
            os.makedirs(workspace.doctypes_dir, exist_ok=True)
            created_dirs.append(workspace.doctypes_dir)
            
            os.makedirs(workspace.workflows_dir, exist_ok=True)
            created_dirs.append(workspace.workflows_dir)
            
            os.makedirs(workspace.history_dir, exist_ok=True)
            created_dirs.append(workspace.history_dir)
        except PermissionError:
            error_messages.append(f"Permission denied when creating directories in {directory}")
            _rollback_initialization(created_dirs, created_files)
            return (False, error_messages)
        except OSError as e:
            error_messages.append(f"Error creating workspace directories: {str(e)}")
            _rollback_initialization(created_dirs, created_files)
            return (False, error_messages)
            
        # Create workspace configuration
        try:
            # Prepare configuration
            workspace_config = config.copy() if config else {}
            
            # Ensure required fields are present
            if "created_at" not in workspace_config:
                workspace_config["created_at"] = datetime.now().isoformat()
                
            if "version" not in workspace_config:
                workspace_config["version"] = "0.1.0"
                
            # Save configuration
            with open(workspace.config_path, 'w') as f:
                yaml.dump(workspace_config, f, default_flow_style=False)
                created_files.append(workspace.config_path)
        except Exception as e:
            error_messages.append(f"Error creating workspace configuration: {str(e)}")
            _rollback_initialization(created_dirs, created_files)
            return (False, error_messages)
            
        # Create template files
        try:
            # Add default templates
            for template_path, content in DEFAULT_TEMPLATES.items():
                dest_path = workspace.meta_dir / template_path
                create_template_file(dest_path, content)
                created_files.append(dest_path)
        except Exception as e:
            error_messages.append(f"Error creating template files: {str(e)}")
            _rollback_initialization(created_dirs, created_files)
            return (False, error_messages)
            
        # Create README.md if it doesn't exist
        try:
            readme_path = directory / "README.md"
            if not readme_path.exists():
                workspace_name = workspace_config.get("name", "Airic Workspace")
                workspace_desc = workspace_config.get("description", 
                                               "An Airic workspace for document-driven AI collaboration")
                
                with open(readme_path, "w") as f:
                    f.write(f"# {workspace_name}\n\n")
                    f.write(f"{workspace_desc}\n")
                created_files.append(readme_path)
        except Exception as e:
            logger.warning(f"Error creating README.md: {str(e)}")
            # Non-critical error, don't roll back
            
        return (True, [])
        
    except Exception as e:
        error_messages.append(f"Unexpected error during workspace initialization: {str(e)}")
        _rollback_initialization(created_dirs, created_files)
        return (False, error_messages)


def _rollback_initialization(created_dirs: List[Path], created_files: List[Path]) -> None:
    """
    Roll back initialization by removing created files and directories.
    
    Args:
        created_dirs: List of directories that were created
        created_files: List of files that were created
    """
    # Remove files first
    for file_path in reversed(created_files):
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Rollback: Removed file {file_path}")
        except Exception as e:
            logger.error(f"Error during rollback when removing file {file_path}: {str(e)}")
            
    # Then remove directories (in reverse order to handle nested dirs)
    for dir_path in reversed(created_dirs):
        try:
            if dir_path.exists() and dir_path.is_dir():
                # Only remove if empty
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    logger.debug(f"Rollback: Removed directory {dir_path}")
        except Exception as e:
            logger.error(f"Error during rollback when removing directory {dir_path}: {str(e)}") 