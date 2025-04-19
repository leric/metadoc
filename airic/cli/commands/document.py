"""
Document operation commands for Airic CLI.
"""
import typer
from pathlib import Path
from typing import Optional, List
from rich.table import Table

from airic.cli.app import document_app
from airic.cli.utils import (
    console,
    print_error,
    print_warning,
    print_success,
    print_info,
    requires_workspace,
    format_path
)
from airic.core.workspace import Workspace


@document_app.command(name="list")
@requires_workspace
def list_documents(
    workspace,
    directory: Optional[Path] = typer.Option(
        None, "--dir", "-d", help="Directory to list documents from (relative to workspace root)"
    ),
    pattern: str = typer.Option(
        "*.md", "--pattern", "-p", help="File pattern to match (e.g., '*.md')"
    ),
):
    """
    List Markdown documents in the workspace.
    
    By default, lists all .md files in the workspace root.
    """
    # Determine the directory to search
    search_dir = workspace.root_path
    if directory:
        search_dir = workspace.root_path / directory
        if not search_dir.exists() or not search_dir.is_dir():
            print_error(f"Directory not found: {directory}")
            raise typer.Exit(code=1)
    
    # Find all matching documents
    documents = list(search_dir.glob(pattern))
    
    if not documents:
        print_info(f"No documents matching '{pattern}' found in {format_path(search_dir)}")
        return
    
    # Create a table to display the documents
    table = Table(title=f"Documents in {format_path(search_dir)}")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Size", justify="right")
    
    # Add each document to the table
    for doc in sorted(documents):
        if doc.is_file():
            # Get relative path from workspace root
            try:
                rel_path = doc.relative_to(workspace.root_path)
                table.add_row(
                    doc.name,
                    str(rel_path),
                    f"{doc.stat().st_size:,} bytes"
                )
            except ValueError:
                # This shouldn't happen, but just in case
                pass
    
    console.print(table)
    print_info(f"Found {len(documents)} document(s)")


@document_app.command(name="open")
@requires_workspace
def open_document(
    workspace,
    document_path: Path = typer.Argument(
        ..., help="Path to the document to open (relative to workspace root)"
    ),
    create: bool = typer.Option(
        False, "--create", "-c", 
        help="Create the document if it doesn't exist"
    ),
):
    """
    Open a document for editing and set it as the active document.
    
    The document path is relative to the workspace root.
    If document doesn't exist, it can be created with the --create flag.
    """
    # Resolve the full path to the document
    full_path = workspace.root_path / document_path
    
    # Check if the document exists
    if not full_path.exists():
        if create:
            try:
                # Create parent directories if needed
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create empty document
                with open(full_path, "w") as f:
                    f.write("---\n")
                    f.write("# Add your metadata here (e.g., doctype: meeting_notes)\n")
                    f.write("---\n\n")
                    f.write(f"# {document_path.stem.replace('_', ' ').title()}\n\n")
                    f.write("Your content here...\n")
                
                print_success(f"Created new document: {format_path(full_path)}")
            except Exception as e:
                print_error(f"Failed to create document: {str(e)}")
                raise typer.Exit(code=1)
        else:
            print_error(f"Document not found: {document_path}")
            print_info("Use --create to create a new document at this path")
            raise typer.Exit(code=1)
    
    # In a real implementation, this would set the active document in the REPL
    # For now, just show that the document is "opened"
    print_success(f"Opened document: {format_path(full_path)}")
    print_info("In the full implementation, this would become the active document in the REPL session.")


@document_app.command(name="info")
@requires_workspace
def document_info(
    workspace,
    document_path: Path = typer.Argument(
        ..., help="Path to the document (relative to workspace root)"
    ),
):
    """
    Display information about a document.
    
    Shows metadata, file information, and related documents if available.
    """
    # Resolve the full path to the document
    full_path = workspace.root_path / document_path
    
    # Check if the document exists
    if not full_path.exists():
        print_error(f"Document not found: {document_path}")
        raise typer.Exit(code=1)
    
    # Display basic file information
    console.print(f"Document: [bold]{document_path}[/bold]")
    console.print(f"Full path: {format_path(full_path)}")
    console.print(f"Size: {full_path.stat().st_size:,} bytes")
    
    # In a full implementation, we would parse the document to extract metadata
    # and show more detailed information
    console.print("\n[yellow]Note: Full metadata extraction will be implemented in a future task[/yellow]") 