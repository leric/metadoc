"""
Main CLI command entry points for Airic.
"""
import os
import typer
import asyncio
from pathlib import Path
from rich.console import Console
from rich import print as rprint
from typing import Optional

from airic import __version__
from airic.core.workspace import Workspace, WorkspaceContext, workspace_context, WorkspaceValidationError
from airic.core.init import initialize_workspace

app = typer.Typer(
    name="airic",
    help="Personal AI Work Partner using Meta Documents",
    add_completion=True,
)
console = Console()

def get_version():
    """Return the version of the package."""
    return __version__


@app.callback()
def callback():
    """
    Airic - Personal AI Work Partner using Meta Documents.
    """
    pass


@app.command()
def version():
    """Show the version of Airic."""
    console.print(f"Airic version: [bold]{get_version()}[/bold]")


@app.command()
def init(
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
        console.print(f"⚠️  [yellow]Workspace in [bold]{directory}[/bold] is already initialized.[/yellow]")
        if typer.confirm("Do you want to reinitialize it?", default=False):
            console.print("Reinitializing workspace...")
        else:
            console.print("Aborting.")
            return
    
    # Initialize the workspace using the enhanced initialization logic
    console.print(f"Initializing Airic workspace in [bold]{directory}[/bold]...")
    success, error_messages = initialize_workspace(directory, config)
    
    if not success:
        console.print(f"❌ [bold red]Failed to initialize workspace[/bold red]")
        for error in error_messages:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)
    
    # Load the workspace to get config for display
    workspace = Workspace(directory)
    
    # Display results
    console.print(f"✅ Initialized Airic workspace in [bold]{directory}[/bold]")
    
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
    console.print("  agents/default.md")
    console.print("  agents/writer.md")
    console.print("  doctypes/meeting_notes.md")
    console.print("  doctypes/brainstorming.md")
    console.print("  workflows/document_review.md")

    console.print("\n🎉 Initialization complete! Start by creating documents with your favorite Markdown editor.")
    console.print("   Then use 'airic open <document>' to begin working with your AI partner.")


@app.command()
def check():
    """
    Check if the current directory is within a valid Airic workspace.
    """
    try:
        with workspace_context() as workspace:
            console.print(f"✅ Found valid Airic workspace at: [bold]{workspace.root_path}[/bold]")
            console.print(f"\nWorkspace name: [bold]{workspace.config.get('name')}[/bold]")
            console.print(f"Description: {workspace.config.get('description')}")
            console.print(f"Version: {workspace.config.get('version')}")
            if created_at := workspace.config.get('created_at'):
                console.print(f"Created at: {created_at}")
    except WorkspaceValidationError as e:
        console.print(f"❌ [bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def repl(
    workspace_path: Optional[Path] = typer.Argument(
        None, help="Path to an Airic workspace (uses current directory if not specified)"
    ),
):
    """
    Start an interactive REPL (Read-Eval-Print Loop) session.
    
    The REPL provides a command-line interface for interacting with Airic,
    including document management and AI assistance.
    """
    from airic.cli.repl import start_repl
    
    # Use current directory if no path is provided
    if workspace_path is None:
        workspace_path = Path.cwd()
    
    # Start the REPL
    try:
        asyncio.run(start_repl(workspace_path))
    except KeyboardInterrupt:
        console.print("\n[yellow]REPL session terminated.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


def main():
    """Main entry point for the CLI."""
    app() 