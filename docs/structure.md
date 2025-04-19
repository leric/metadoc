## Airic CLI Structure and Functionality

Airic is a "Personal AI Work Partner using Meta Documents" with a CLI interface built on Typer. The codebase is organized in a modular fashion with these key components:

### Main Application Structure

- airic/cli/app.py: Defines the main Typer application with command groups

- airic/__main__.py: Entry point for running the CLI with python -m airic

- Command pattern: Commands are organized into logical groups (workspace, document, ai)

### Workspace Management

- airic/core/workspace.py: Core workspace functionality

- Workspace class: Manages workspace directory structure and configuration

- WorkspaceConfig class: Handles workspace configuration data

- WorkspaceContext: Context manager for commands requiring a valid workspace

- Workspace structure includes .airic directory with meta, agents, doctypes, workflows, and history subdirectories

- airic/cli/commands/workspace.py: CLI commands for workspace operations

- init_workspace: Creates a new workspace with configuration

- workspace_info: Displays information about current workspace

- check_workspace: Validates if current directory is a workspace

### Document Operations

- airic/cli/commands/document.py: Document-related CLI commands

- list_documents: Lists Markdown documents in the workspace

- open_document: Opens a document for editing (or creates it)

- document_info: Displays information about a document

### Utilities

- airic/cli/utils.py: Shared utility functions

- Rich console output formatting

- Workspace requirement decorator

- Helper functions for consistent UI feedback

- Path formatting and confirmation prompts

### Command Registration Pattern

- Commands are defined in separate modules

- Modules are imported in app.py's get_app() function

- Commands use the @requires_workspace decorator when workspace context is needed

### Design Patterns

- Context manager pattern for workspace validation

- Decorator pattern for command requirements

- Command pattern for CLI operations

- Factory pattern for app instance creation

The codebase follows a clean architecture with separation of concerns between core functionality and CLI interface. The workspace concept is central, providing a consistent environment for AI-assisted document operations with proper configuration and directory structure.