"""
Main Typer application for Airic CLI.

IMPORTANT: This implementation is deprecated and will be removed in a future version. 
The preferred implementation is in airic.cli.main which is the actual entry point
defined in pyproject.toml. The __main__.py file has been updated to use main.py directly.
"""
import typer
from rich.console import Console
from typing import Optional
from pathlib import Path

from airic import __version__

# Console for rich output formatting
console = Console()

# Create the main Typer app instance
app = typer.Typer(
    name="airic",
    help="Personal AI Work Partner using Meta Documents",
    add_completion=True,
)

# Create command groups for different functionality areas
workspace_app = typer.Typer(help="Workspace management commands")
document_app = typer.Typer(help="Document operations and navigation")
ai_app = typer.Typer(help="AI interaction commands")

# Register command groups with the main app
app.add_typer(workspace_app, name="workspace", help="Manage Airic workspace")
app.add_typer(document_app, name="doc", help="Work with documents")
app.add_typer(ai_app, name="ai", help="Control AI behavior and interactions")


@app.callback()
def callback():
    """
    Airic - Personal AI Work Partner using Meta Documents.
    
    A CLI tool for AI-assisted document workflows.
    """
    pass


@app.command()
def version():
    """Show the version of Airic."""
    console.print(f"Airic version: [bold]{__version__}[/bold]")


# Create a simplified alias for the init command at the root level
@app.command(name="init")
def init_root_alias(
    directory: Optional[Path] = typer.Argument(None, help="Directory to initialize as an Airic workspace"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Name for the workspace"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description for the workspace"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinitialization if workspace already exists"),
):
    """Initialize a new Airic workspace in the specified directory."""
    # Import here to avoid circular imports
    from airic.cli.commands.workspace import init_workspace
    return init_workspace(directory, name, description, force)


def get_app() -> typer.Typer:
    """
    Get the configured Typer app instance.
    
    This is used as the main entry point for the CLI and for testing.
    """
    # Import the command modules to register commands
    # This must be done after creating the app to avoid circular imports
    import airic.cli.commands.workspace
    import airic.cli.commands.document
    import airic.cli.commands.ai
    
    return app 