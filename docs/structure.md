## Airic CLI Structure and Functionality

Airic is a "Personal AI Work Partner using Meta Documents" with a CLI interface built on Typer. The codebase follows a modular architecture that separates core functionality from the CLI interface.

### Main Application Structure

- **Entry points:**
  - `airic/__main__.py`: Entry point when running with `python -m airic`
  - `airic/cli/main.py`: Primary CLI implementation (preferred over app.py)
  - `airic/cli/app.py`: Legacy Typer application (being deprecated)

- **CLI organization:**
  - Command pattern with logical groups: workspace, document, ai
  - Rich console output for user-friendly interaction
  - Context managers for workspace validation

### Core Components

#### Workspace Management

- **Core implementation: `airic/core/workspace.py`**
  - `Workspace` class: Manages workspace directory structure and configuration
  - `WorkspaceConfig` class: Handles workspace configuration data
  - `WorkspaceContext`: Context manager for commands requiring a valid workspace
  - `workspace_context()`: Convenient context manager function

- **Workspace structure:**
  - `.airic/`: Root directory for all metadata and history
  - `.airic/meta/`: Contains agents, doctypes, and workflows definitions
  - `.airic/meta/agents/`: Agent definitions (e.g., assistant.md)
  - `.airic/meta/doctypes/`: Document type definitions
  - `.airic/meta/workflows/`: Workflow process definitions
  - `.airic/history/`: Records of document interactions and agent responses

- **Workspace initialization: `airic/core/init.py`**
  - `initialize_workspace()`: Sets up directory structure and base configuration
  - Default templates for agents, doctypes, and workflows
  - Rollback mechanism for failed initialization

#### Document Operations

- **Document commands: `airic/cli/commands/document.py`**
  - `list_documents`: Lists Markdown documents in the workspace
  - `open_document`: Opens a document for editing (or creates it)
  - `document_info`: Displays information about a document

#### Utilities and Helpers

- **CLI utilities: `airic/cli/utils.py`**
  - Rich console output formatting functions
  - `requires_workspace` decorator for commands needing workspace context
  - Path formatting and user interaction helpers

- **Markdown utilities: `airic/utils/markdown.py`**
  - Functions for parsing and processing Markdown documents
  - Frontmatter extraction and validation

### Command Structure

#### Workspace Commands

- `airic init [directory]`: Initialize a new workspace
- `airic check`: Verify current directory is a valid workspace
- Additional workspace management commands in `airic/cli/commands/workspace.py`

#### Document Commands

- `airic doc list`: List Markdown documents in workspace
- `airic doc open <document_path>`: Open/create a document
- `airic doc info <document_path>`: Show document information

#### AI Interaction Commands

- AI-related commands defined in `airic/cli/commands/ai.py`

### Design Patterns

- **Context Manager Pattern**: `WorkspaceContext` for workspace validation
- **Decorator Pattern**: `@requires_workspace` for command requirements
- **Command Pattern**: CLI operations organized as discrete commands
- **Factory Pattern**: App instance creation via `get_app()`

### Implementation Notes

- Separate CLI interface from core logic for better testability and reuse
- Rich console output for improved user experience
- YAML-based configuration for workspace settings
- Markdown documents with YAML frontmatter for metadata
- File-based organization of agent and document type definitions

This architecture provides a clean separation of concerns, making the codebase maintainable and extensible. The workspace concept is central, providing a consistent environment for AI-assisted document operations with proper configuration and directory structure.