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
    # Template for defining agents
    "doctypes/agent_def.md": """---
name: agent_def
description: Template and guidelines for creating agent definitions
version: 0.1.0
doctype: doctype
---

# Agent Definition Document Type

This document type is designed for defining agents in the Airic workspace. 
Agents are specialized AI assistants that follow specific behavior patterns when interacting with documents.

## Structure

Agent definition documents should include:

1. **Metadata (YAML Frontmatter):**
   ```yaml
   ---
   name: agent_name              # Required: Unique identifier for the agent
   description: Short summary    # Required: Brief description of agent's purpose
   version: 0.1.0                # Required: Semantic version
   tools: [tool1, tool2]         # Optional: Tools this agent can use (future feature)
   ---
   ```

2. **Agent Description:**
   - Detailed explanation of the agent's purpose and capabilities
   - Target use cases and document types it works best with

3. **System Prompt:**
   - Specific instructions that define the agent's behavior
   - Personality traits, response style, and expertise areas
   - Constraints and guidelines for interactions

4. **Examples (Optional):**
   - Sample interactions showing how the agent should respond
   - "Do" and "Don't" examples to clarify behavior boundaries

## Guidelines

- Keep system prompts specific and focused on a single responsibility
- Use clear, direct language in system prompts
- Avoid contradictory instructions
- Consider the agent's limitations when defining capabilities
- Test agents with various document types and user queries
""",

    # Template for defining document types
    "doctypes/doctype_def.md": """---
name: doctype_def
description: Template and guidelines for creating document type definitions
version: 0.1.0
doctype: doctype
---

# DocType Definition Document Type

This document type is designed for defining document types in the Airic workspace.
Document types define the structure, purpose, and processing rules for different kinds of documents.

## Structure

DocType definition documents should include:

1. **Metadata (YAML Frontmatter):**
   ```yaml
   ---
   name: doctype_name           # Required: Unique identifier for the doctype
   description: Short summary   # Required: Brief description of doctype's purpose
   version: 0.1.0               # Required: Semantic version
   ---
   ```

2. **Purpose Description:**
   - Detailed explanation of what this document type is used for
   - When and why to use this document type

3. **Structure Guidelines:**
   - Required and optional sections
   - Formatting and content requirements
   - Any special syntax or conventions

4. **Examples (Optional):**
   - Sample document snippets showing proper structure
   - Templates that can be copied and adapted

## Guidelines

- Focus on structure more than content requirements
- Provide clear, actionable guidelines for document creation
- Balance flexibility and standardization
- Consider both human readability and machine processability
- Test document types with relevant agents to ensure compatibility
""",

    # Template for defining workflows
    "doctypes/workflow_def.md": """---
name: workflow_def
description: Template and guidelines for creating workflow definitions
version: 0.1.0
doctype: doctype
---

# Workflow Definition Document Type

This document type is designed for defining workflows in the Airic workspace.
Workflows define multi-step processes that guide users through completing complex tasks.

## Structure

Workflow definition documents should include:

1. **Metadata (YAML Frontmatter):**
   ```yaml
   ---
   name: workflow_name          # Required: Unique identifier for the workflow
   description: Short summary   # Required: Brief description of workflow's purpose
   version: 0.1.0               # Required: Semantic version
   doctype: workflow            # Required: Always set to "workflow"
   ---
   ```

2. **Purpose Description:**
   - Detailed explanation of what this workflow accomplishes
   - When and why to use this workflow

3. **Stages:**
   - Clearly defined steps in the workflow
   - Dependencies between steps
   - Expected inputs and outputs for each step

4. **Usage Instructions:**
   - How to initiate and progress through the workflow
   - How to track status and completion

## Guidelines

- Break complex processes into clear, manageable steps
- Define success criteria for each step and the overall workflow
- Provide guidance for handling common issues or exceptions
- Consider different skill levels when designing workflow instructions
- Test workflows end-to-end to ensure they lead to successful outcomes
""",

    # Default assistant agent
    "agents/assistant.md": """---
name: assistant
description: A general-purpose assistant for document interaction and task support
version: 0.1.0
---

# Assistant Agent

You are a helpful AI assistant that works with the user in the context of their current document.
When interacting with the user, you should consider the content of their current document, its metadata,
and any relevant context from linked documents.

## Guidelines

- Be concise and direct in your responses
- When the user asks about content in their document, reference it specifically
- Help with drafting, editing, and organizing document content
- Suggest improvements to document structure and clarity
- When appropriate, help the user break down complex tasks into smaller steps
- If the document has a specific doctype, follow the associated guidelines
- Offer relevant commands when they would help the user

## Document Context

For each interaction, you'll receive:
- The content of the user's current document
- Document metadata (like doctype, if specified)
- Any relevant history from previous interactions with this document
- Information about linked documents (when available)

Use this context to provide the most helpful, relevant responses possible.
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