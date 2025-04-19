"""
Workspace management commands for Airic CLI.
"""
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console

from airic.cli.app import workspace_app
from airic.cli.utils import (
    console,
    print_error, 
    print_warning, 
    print_success, 
    print_info,
    print_workspace_info,
    requires_workspace,
    confirm_action
)
from airic.core.workspace import Workspace, WorkspaceValidationError, WorkspaceContext
from airic.core.init import initialize_workspace


@workspace_app.command(name="init")
def init_workspace(
    directory: Path = typer.Argument(
        None, help="Directory to initialize as an Airic workspace"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Name for the workspace"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Description for the workspace"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force reinitialization if workspace already exists"
    ),
):
    """
    Initialize a new Airic workspace in the specified directory.
    
    Creates the necessary directory structure and configuration files.
    """
    # Use current directory if not specified
    if directory is None:
        directory = Path.cwd()
    else:
        # Create directory if it doesn't exist
        directory.mkdir(parents=True, exist_ok=True)

    # Prepare custom configuration
    config = {}
    if name:
        config["name"] = name
    if description:
        config["description"] = description
    
    # Check if already initialized
    workspace = Workspace(directory)
    if workspace.is_initialized() and not force:
        print_warning(f"Workspace in [bold]{directory}[/bold] is already initialized.")
        if confirm_action("Do you want to reinitialize it?", default=False):
            print_info("Reinitializing workspace...")
        else:
            print_info("Aborting.")
            return
    
    # Initialize the workspace using the enhanced initialization logic
    print_info(f"Initializing Airic workspace in [bold]{directory}[/bold]...")
    success, error_messages = initialize_workspace(directory, config)
    
    if not success:
        print_error(f"Failed to initialize workspace")
        for error in error_messages:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)
    
    # Load the workspace to get config for display
    workspace = Workspace(directory)
    
    # Display results
    print_success(f"Initialized Airic workspace in [bold]{directory}[/bold]")
    
    # Show configuration details
    console.print("\nWorkspace Configuration:")
    console.print(f"  Name: [bold]{workspace.config.get('name')}[/bold]")
    console.print(f"  Description: {workspace.config.get('description')}")
    console.print(f"  Version: {workspace.config.get('version')}")
    
    console.print("\nDirectory structure created:")
    console.print("  .airic/")
    console.print("  ├── meta/")
    console.print("  │   ├── agents/")
    console.print("  │   ├── doctypes/")
    console.print("  │   └── workflows/")
    console.print("  └── history/")
    
    # Show information about templates
    console.print("\nCreated template files:")
    console.print("  doctypes/agent_def.md")
    console.print("  doctypes/doctype_def.md")
    console.print("  doctypes/workflow_def.md")
    console.print("  agents/assistant.md")

    console.print("\n🎉 Initialization complete! Start by creating documents with your favorite Markdown editor.")
    console.print("   Then use 'airic open <document>' to begin working with your AI partner.")


@workspace_app.command(name="info")
@requires_workspace
def workspace_info(workspace):
    """
    Display information about the current workspace.
    
    Shows workspace path, configuration, and structure details.
    """
    print_workspace_info(workspace)
    
    # Show structure information
    console.print("\nDirectory structure:")
    console.print("  .airic/")
    console.print("  ├── meta/")
    console.print("  │   ├── agents/")
    console.print("  │   ├── doctypes/")
    console.print("  │   └── workflows/")
    console.print("  └── history/")


@workspace_app.command(name="check")
def check_workspace():
    """
    Check if the current directory is within a valid Airic workspace.
    
    Returns success if a valid workspace is found, error otherwise.
    """
    try:
        with WorkspaceContext() as workspace:
            print_success(f"Found valid Airic workspace at: [bold]{workspace.root_path}[/bold]")
            # Show minimal workspace info
            console.print(f"Workspace name: [bold]{workspace.config.get('name')}[/bold]")
            console.print(f"Version: {workspace.config.get('version')}")
    except WorkspaceValidationError as e:
        print_error(str(e))
        raise typer.Exit(code=1) 