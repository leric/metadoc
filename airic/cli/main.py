"""
Main CLI command entry points for Airic.
"""
import os
import typer
from pathlib import Path
from rich.console import Console
from rich import print as rprint

from airic import __version__

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

    # Create .airic directory and subdirectories
    airic_dir = directory / ".airic"
    airic_dir.mkdir(exist_ok=True)
    
    meta_dir = airic_dir / "meta"
    meta_dir.mkdir(exist_ok=True)
    
    agents_dir = meta_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    
    doctypes_dir = meta_dir / "doctypes"
    doctypes_dir.mkdir(exist_ok=True)
    
    workflows_dir = meta_dir / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    
    history_dir = airic_dir / "history"
    history_dir.mkdir(exist_ok=True)
    
    console.print(f"✅ Initialized Airic workspace in [bold]{directory}[/bold]")
    console.print("\nDirectory structure created:")
    console.print("  .airic/")
    console.print("  ├── meta/")
    console.print("  │   ├── agents/")
    console.print("  │   ├── doctypes/")
    console.print("  │   └── workflows/")
    console.print("  └── history/")
    
    # Create a basic README.md if it doesn't exist
    readme_path = directory / "README.md"
    if not readme_path.exists():
        with open(readme_path, "w") as f:
            f.write("# Airic Workspace\n\n")
            f.write("This is an Airic workspace for document-driven AI collaboration.\n")
        console.print("\n📝 Created basic README.md")

    console.print("\n🎉 Initialization complete! Start by creating documents with your favorite Markdown editor.")
    console.print("   Then use 'airic open <document>' to begin working with your AI partner.")


def main():
    """Main entry point for the CLI."""
    app() 