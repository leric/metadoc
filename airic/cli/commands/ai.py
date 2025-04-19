"""
AI interaction commands for Airic CLI.
"""
import typer
from rich.console import Console
from rich.panel import Panel
from airic.cli.app import ai_app
from airic.cli.utils import console, print_info, print_success, requires_workspace

@ai_app.command(name="info")
def ai_info():
    """
    Display information about the AI configuration.
    """
    console.print(Panel(
        "[bold]AI Configuration[/bold]\n\n"
        "The AI functionality is currently being implemented.\n"
        "Stay tuned for future updates!",
        title="AI Information",
        border_style="blue"
    ))
    print_info("AI commands will be available in a future release.") 