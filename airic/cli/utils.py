"""
Utility functions for Airic CLI commands.
"""
import os
import functools
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.padding import Padding
from rich.style import Style
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast, Dict

from airic.core.workspace import WorkspaceContext, WorkspaceValidationError, Workspace

# Set up console with nice styling
console = Console()

# Function return type for decorator typing
F = TypeVar('F', bound=Callable[..., Any])

# Error styles
ERROR_STYLE = Style(color="red", bold=True)
WARNING_STYLE = Style(color="yellow", bold=True)
SUCCESS_STYLE = Style(color="green", bold=True)
INFO_STYLE = Style(color="blue", bold=True)

def print_error(message: str) -> None:
    """Print an error message with consistent styling."""
    console.print(f"❌ [bold red]Error:[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message with consistent styling."""
    console.print(f"⚠️  [bold yellow]Warning:[/bold yellow] {message}")


def print_success(message: str) -> None:
    """Print a success message with consistent styling."""
    console.print(f"✅ [bold green]{message}[/bold green]")


def print_info(message: str) -> None:
    """Print an informational message with consistent styling."""
    console.print(f"ℹ️  {message}")


def format_path(path: Path) -> str:
    """Format a path for display, using ~ for home directory if applicable."""
    try:
        relative_to_home = path.relative_to(Path.home())
        return f"~/{relative_to_home}"
    except ValueError:
        # Not under home directory
        return str(path)


def print_markdown(content: str) -> None:
    """Render markdown content with rich formatting."""
    md = Markdown(content)
    console.print(md)


def requires_workspace(f: F) -> F:
    """
    Decorator to ensure a command is run within a valid workspace.
    
    Automatically provides the workspace as the first argument to the decorated function.
    For example:
    
    @app.command()
    @requires_workspace
    def my_command(workspace, arg1: str):
        # Command implementation
    """
    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            with WorkspaceContext() as workspace:
                return f(workspace, *args, **kwargs)
        except WorkspaceValidationError as e:
            print_error(str(e))
            print_info("Run 'airic init' to create a new workspace or change to a valid workspace directory.")
            raise typer.Exit(code=1)
    return cast(F, wrapper)


def print_workspace_info(workspace) -> None:
    """Print formatted information about a workspace."""
    table = Table(show_header=False, box=None)
    table.add_column("Property", style="bold")
    table.add_column("Value")
    
    table.add_row("Workspace path", format_path(workspace.root_path))
    table.add_row("Name", workspace.config.get("name", "unnamed"))
    table.add_row("Description", workspace.config.get("description", "No description"))
    table.add_row("Version", workspace.config.get("version", "unknown"))
    if created_at := workspace.config.get("created_at"):
        table.add_row("Created at", created_at)
    
    console.print(Panel(table, title="Workspace Information", border_style="blue"))


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Prompt user to confirm an action with consistent styling.
    
    Args:
        message: The confirmation message to display
        default: Default action if user just presses Enter
        
    Returns:
        True if user confirmed, False otherwise
    """
    return typer.confirm(message, default=default) 