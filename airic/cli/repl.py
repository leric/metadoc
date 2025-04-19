"""
Interactive REPL (Read-Eval-Print Loop) for Airic CLI.

This module implements a command-line interface with prompt-toolkit,
providing command history, input handling, and a foundation for rich output.
"""

import os
import textwrap
import asyncio # Add asyncio import
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Union
import re  # Add import for regex

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter, Completer, Completion, PathCompleter
from rich.console import Console, ConsoleOptions, RenderResult
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich import box
from prompt_toolkit.document import Document as PromptDocument # Avoid collision with our Document

from airic.core.workspace import Workspace, workspace_context, WorkspaceValidationError
from airic.core.document import Document, DocumentError, find_documents
from airic.core.agent import interact_with_agent # Import the correct agent interaction function


# Custom Completer for /open command
class OpenCompleter(Completer):
    def __init__(self, repl_instance: 'AiricREPL'):
        self.repl = repl_instance

    def get_completions(self, document: PromptDocument, complete_event):
        if not self.repl.workspace:
            return # No workspace, no completions

        text_before_cursor = document.text_before_cursor
        
        # Extract the part after '/open '
        parts = text_before_cursor.split(maxsplit=1)
        if len(parts) < 2:
             # Not enough text after /open yet, or just /open
             # Maybe complete top-level dirs/files here? Let's keep it simple for now.
             current_input = ""
        else:
             current_input = parts[1]

        workspace_root = self.repl.workspace.root_path
        
        # --- 1. WikiLink Completions ---
        wikilinks = set()
        if self.repl.active_document:
            try:
                # Find unique WikiLinks in the active document body
                found = re.findall(r'\[\[(.+?)\]\]', self.repl.active_document.body)
                wikilinks.update(f"[[{link.strip()}]]" for link in found)
            except Exception:
                # Ignore errors reading/parsing document body for links
                pass 
                
        # Yield matching WikiLinks first
        for link in sorted(list(wikilinks)):
            if link.lower().startswith(current_input.lower()):
                 # Display [[Link Name]], complete with [[Link Name]]
                yield Completion(
                    link, 
                    start_position=-len(current_input), 
                    display=link,
                    display_meta='WikiLink'
                )

        # --- 2. Filesystem Path Completions ---
        try:
            # Use PathCompleter logic carefully adapted for workspace relative paths
            # PathCompleter expects an absolute path fragment usually. We need to handle relative.
            
            # Determine the base path and partial name for glob
            if os.path.sep in current_input:
                base_dir_str, partial_name = os.path.split(current_input)
                base_path = (workspace_root / base_dir_str).resolve()
            else:
                base_path = workspace_root
                partial_name = current_input

            # Ensure base_path is within the workspace and exists
            if base_path.is_dir() and str(base_path).startswith(str(workspace_root)):
                # Glob for matching files and directories
                for item in base_path.glob(f"{partial_name}*"):
                    # Construct the completion text relative to workspace root
                    try:
                        rel_path_str = str(item.relative_to(workspace_root))
                    except ValueError:
                        continue # Should not happen if logic is correct

                    # Skip already suggested WikiLinks (if they resolve to the same file)
                    # This check is basic, might need refinement
                    is_wikilink_match = False
                    if item.is_file() and item.suffix == '.md':
                         wikilink_form = f"[[{item.stem}]]"
                         if wikilink_form in wikilinks:
                              is_wikilink_match = True
                              
                    if not is_wikilink_match:
                        display_meta = 'Directory' if item.is_dir() else 'File'
                        # Append / to directories for easier navigation
                        completion_text = rel_path_str + os.path.sep if item.is_dir() else rel_path_str
                        
                        yield Completion(
                            completion_text,
                            start_position=-len(current_input),
                            display=rel_path_str, # Show relative path without trailing /
                            display_meta=display_meta
                        )
        except Exception as e:
             # Log error maybe? For now, fail silently if path completion fails
             # self.repl.print_warning(f"Debug: Path completion error: {e}") # DEBUG
             pass


# Main Completer deciding which completer to use
class ConditionalCompleter(Completer):
    def __init__(self, repl_instance: 'AiricREPL'):
        self.repl = repl_instance
        self.command_completer = WordCompleter([cmd.lstrip('/') for cmd in repl_instance.commands.keys()], ignore_case=True)
        self.open_completer = OpenCompleter(repl_instance)

    def get_completions(self, document: PromptDocument, complete_event):
        text = document.text_before_cursor
        
        if text.startswith('/open '):
            # Use OpenCompleter if we are typing after '/open '
            # We need to adjust the document context for OpenCompleter potentially
            # Let OpenCompleter handle splitting '/open ' off
            yield from self.open_completer.get_completions(document, complete_event)
        elif text.startswith('/'):
             # Use command completer if starting with / but not '/open '
             # Need to adjust document for WordCompleter - it completes from start
             word_doc = PromptDocument(text.lstrip('/'), cursor_position=document.cursor_position - 1)
             yield from self.command_completer.get_completions(word_doc, complete_event)
        # else:
            # Could add other completers here, e.g., for AI context
            # For now, no completions if not starting with /

class AiricREPL:
    """
    Implements the REPL interface for Airic using prompt-toolkit.
    
    This class manages:
    - Command input with history
    - Differentiation between commands and text input
    - Rich output formatting including Markdown and syntax highlighting
    - Asynchronous interaction with the AI agent
    """
    
    def __init__(self, workspace_path: Optional[Path] = None):
        """
        Initialize the REPL interface.
        
        Args:
            workspace_path: Optional path to an Airic workspace
        """
        self.workspace_path = workspace_path
        self.workspace = None
        self.active_document = None
        self.active_doctype = None
        self.active_agent = None # Initialize active_agent early
        self.console = Console()
        self.running = True  # Flag to control the REPL loop
        
        # Initialize AI service - Keep this for now if other parts rely on it,
        # but the core text processing will use the agent.
        # self.ai_service = get_ai_service("mock") # Comment out or remove if fully replaced
        
        # Set up history file in user's home directory
        history_dir = Path.home() / ".airic" / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        history_file = history_dir / "command_history.txt"
        
        # Register command handlers *BEFORE* initializing completer
        self.commands = {
            'exit': self._handle_exit,
            'quit': self._handle_exit,
            'help': self._handle_help,
            'list': self._handle_list,
            'open': self._handle_open,
            'info': self._handle_info,
            'close': self._handle_close,
            'new': self._handle_new,
            'init': self._handle_init,
            'edit': self._handle_edit,
            'save': self._handle_save,
            'ai': self._handle_ai,
        }

        # Use the new ConditionalCompleter
        main_completer = ConditionalCompleter(self)

        # Set up prompt session with history
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=self._create_keybindings(),
            style=self._create_style(),
            completer=main_completer, # Use the new completer
            bottom_toolbar=self._get_status_bar,
        )
        
    def _create_keybindings(self) -> KeyBindings:
        """Create custom key bindings for the REPL."""
        bindings = KeyBindings()
        
        @bindings.add('c-d')
        def _(event):
            """Exit when Control-D is pressed."""
            event.app.exit()
        
        return bindings
    
    def _create_style(self) -> Style:
        """Create custom styles for the prompt."""
        return Style.from_dict({
            'prompt': 'ansicyan bold',
            'command': 'ansigreen',
            'error': 'ansired',
            'status.toolbar': 'bg:#222222 #aaaaaa',
            'status.info': 'bg:#222222 #ffffff',
            'status.document': 'bg:#222222 #88ff88',
            'status.doctype': 'bg:#222222 #ffaa00',
        })
    
    def _get_status_bar(self) -> HTML:
        """Generate the status bar content based on current context."""
        parts = []
        
        # Add workspace info
        if self.workspace:
            workspace_name = self.workspace.config.get('name', 'airic')
            parts.append(f"<status.info>Workspace:</status.info> <status.toolbar>{workspace_name}</status.toolbar>")
        else:
            parts.append("<status.info>No active workspace</status.info>")
        
        # Add separator
        parts.append("<status.toolbar> | </status.toolbar>")
        
        # Add document info
        if self.active_document:
            doc_name = self.active_document.name
            parts.append(f"<status.info>Document:</status.info> <status.document>{doc_name}</status.document>")
            
            # Add doctype if available
            if self.active_doctype:
                parts.append(f"<status.info> Type:</status.info> <status.doctype>{self.active_doctype}</status.doctype>")
            else:
                parts.append("<status.info> Type:</status.info> <status.toolbar>none</status.toolbar>")
            # Add agent info if available
            if self.active_agent:
                parts.append(f"<status.info> Agent:</status.info> <status.doctype>{self.active_agent}</status.doctype>") # Using doctype style for agent
        else:
            parts.append("<status.info>No active document</status.info>")
        
        return HTML(" ".join(parts))
    
    async def start(self): # Make start method async
        """
        Start the REPL loop.
        
        This is the main entry point for the interactive CLI.
        """
        self._print_welcome_message()
        
        try:
            self._initialize_workspace()
        except WorkspaceValidationError as e:
            self.print_error(f"Error: {str(e)}")
            self.print_warning("You are not in a valid Airic workspace. Some commands may not work.")
            self.print_info("Run [bold]/init[/bold] to initialize a workspace in the current directory.")
        
        # Main REPL loop
        while self.running:
            try:
                # Get the prompt text
                prompt_text = self._get_prompt_text()
                
                # Get user input asynchronously
                user_input = await self.session.prompt_async(prompt_text) # Use prompt_async
                
                # Process the input
                if not user_input.strip():
                    continue
                
                await self._process_input(user_input) # Await input processing
                
            except KeyboardInterrupt:
                # Handle Ctrl+C
                self.print_warning("Operation cancelled.")
                continue
            except EOFError:
                # Handle Ctrl+D
                self.print_success("Goodbye!")
                self.running = False
                break
            except Exception as e:
                # Handle unexpected errors
                self.print_error(f"Error: {str(e)}")
    
    def _initialize_workspace(self):
        """Initialize the workspace if a path is provided and load default document."""
        workspace_loaded = False
        if self.workspace_path:
            try:
                with workspace_context(self.workspace_path) as workspace:
                    self.workspace = workspace
                    workspace_loaded = True
            except WorkspaceValidationError as e:
                self.print_warning(f"Failed to load workspace at {self.workspace_path}: {e}")
                self.workspace = None # Ensure workspace is None if loading fails
        else:
            # Try to find workspace from current directory
            try:
                with workspace_context() as workspace:
                    self.workspace = workspace
                    workspace_loaded = True
            except WorkspaceValidationError:
                # No valid workspace found
                self.workspace = None

        # If workspace loaded successfully, try opening default document
        if workspace_loaded and self.workspace:
            self._open_default_document()
    
    def _open_default_document(self):
        """Try to open README.md or index.md as the default document."""
        default_candidates = ["README.md", "index.md"]
        opened_default = False
        for filename in default_candidates:
            path = self.workspace.root_path / filename
            if path.exists():
                try:
                    # Use internal logic similar to _handle_open but without user messages for initial load
                    document = Document(path)
                    self.active_document = document
                    self.active_doctype = document.doctype
                    self.active_agent = document.agent
                    self.print_info(f"Opened default document: {filename}") # Inform user
                    opened_default = True
                    break # Stop after opening the first found default
                except DocumentError as e:
                    self.print_warning(f"Error opening default document {filename}: {str(e)}")
       
        # if not opened_default:
            # self.print_info("No default document (README.md or index.md) found.")
            # Optionally create one if desired, or just start with no active doc
    
    def _get_prompt_text(self) -> str:
        """Generate the prompt text based on current context."""
        if self.active_document:
            doc_name = self.active_document.name
            if self.active_agent:
                prompt = f"[{doc_name}|{self.active_agent}] > "
            else:
                prompt = f"[{doc_name}] > "
        else:
            prompt = "airic > "
        
        return HTML(f"<prompt>{prompt}</prompt>")
    
    async def _process_input(self, user_input: str): # Make process_input async
        """
        Process user input, differentiating between commands and text input.
        
        Args:
            user_input: The user's input string
        """
        stripped_input = user_input.strip()
        
        # Check if it's a command (starts with /)
        if stripped_input.startswith('/'):
            # Commands are typically synchronous, no need to await here unless a command becomes async
            self._handle_command(stripped_input[1:])  # Remove the / prefix
        else:
            # It's free text for AI, handle asynchronously
            await self._handle_text_input(stripped_input) # Await text input handler
    
    def _handle_command(self, command_input: str):
        """
        Process a command input.
        
        Args:
            command_input: The command string without the / prefix
        """
        # Split into command and arguments
        parts = command_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Check if we have a handler for this command
        if command in self.commands:
            self.commands[command](args)
        else:
            self.print_error(f"Unknown command: {command}")
            self.print_info("Type [bold]/help[/bold] for a list of available commands.")
    
    async def _handle_text_input(self, text: str): # Make _handle_text_input async
        """
        Process free text input by sending it to the Google ADK agent via the runner.

        Args:
            text: The text to process
        """
        self.print_info("Sending request to AI agent...") # Indicate processing

        try:
            # Context packaging (Task 8.2) - Basic version for now
            context_info = f"\n\nCurrent Document Context ({self.active_document.name}):\n{self.active_document.body}" if self.active_document else ""
            full_input = text + context_info

            # Use the user ID defined in core.agent or make it dynamic if needed
            # For REPL, a single user ID per session is likely fine.
            # from airic.core.agent import DEFAULT_USER_ID # Optionally import
            user_id_for_agent = "repl_user" # Or use DEFAULT_USER_ID

            # Call the agent interaction function which uses the runner
            response_text = await interact_with_agent(
                user_input=full_input,
                user_id=user_id_for_agent
            )

            # History is managed by the SessionService used by the runner in core.agent
            # No need to manually append here.

            # TODO: Implement Markdown formatting with Rich (Task 8.3)
            self.print_markdown(response_text)

        except Exception as e: # Catch potential errors from the agent call
            self.print_error(f"Error interacting with AI agent: {str(e)}")
            # History management is handled by ADK, no need to pop here
    
    def _handle_exit(self, args: str = ""):
        """
        Handle the /exit or /quit command.
        
        Args:
            args: Any arguments passed to the command (not used)
        """
        self.print_success("Goodbye!")
        self.running = False  # Set the flag to stop the REPL loop
    
    def _handle_help(self, args: str = ""):
        """
        Handle the /help command.
        
        Args:
            args: Any arguments passed to the command
        """
        # Create a panel with help information
        help_text = Text()
        help_text.append("Available Commands:\n", style="bold")
        
        # Basic commands
        help_text.append("Basic Commands:\n", style="bold")
        help_text.append("  /help            ", style="green")
        help_text.append("Show this help message\n")
        help_text.append("  /exit, /quit     ", style="green")
        help_text.append("Exit the REPL\n")
        help_text.append("  /init [path]     ", style="green")
        help_text.append("Initialize a workspace at the current or specified path\n\n")
        
        # Document commands
        help_text.append("Document Commands:\n", style="bold")
        help_text.append("  /list [pattern]  ", style="green")
        help_text.append("List documents in the workspace\n")
        help_text.append("  /open <path>     ", style="green")
        help_text.append("Open a document for editing\n")
        help_text.append("  /new <path>      ", style="green")
        help_text.append("Create and open a new document\n")
        help_text.append("  /info            ", style="green")
        help_text.append("Show information about the active document\n")
        help_text.append("  /close           ", style="green")
        help_text.append("Close the active document\n")
        help_text.append("  /edit            ", style="green")
        help_text.append("Edit the active document\n")
        help_text.append("  /save            ", style="green")
        help_text.append("Save changes to the active document\n\n")
        
        # AI commands
        help_text.append("AI Commands:\n", style="bold")
        help_text.append("  /ai              ", style="green")
        help_text.append("Display AI service information\n")
        help_text.append("  /ai info         ", style="green")
        help_text.append("Show details about the current AI service\n")
        help_text.append("  /ai settings ... ", style="green")
        help_text.append("Configure AI service settings (e.g., '/ai settings model=gpt-4')\n\n")
        
        help_text.append("Type any text without a leading / to interact with the AI.", style="dim")
        
        help_panel = Panel(
            help_text,
            title="Airic Help",
            border_style="blue",
            box=box.ROUNDED
        )
        
        self.console.print(help_panel)
    
    def _handle_list(self, args: str = ""):
        """
        Handle the /list command.
        
        Args:
            args: Optional glob pattern for filtering documents
        """
        if not self.workspace:
            self.print_error("No active workspace. Use /init to initialize a workspace.")
            return
        
        pattern = args.strip() if args else "*.md"
        
        self.print_info(f"Listing documents matching pattern: {pattern}")
        
        # Find documents in the workspace
        documents = find_documents(self.workspace.root_path, pattern)
        
        if not documents:
            self.print_info("No documents found.")
            return
        
        # Create a table to display the documents
        from rich.table import Table
        table = Table(title=f"Documents in {self.workspace.root_path}")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Path", style="green")
        
        # Add each document to the table
        for doc in sorted(documents, key=lambda d: d.name):
            rel_path = doc.path.relative_to(self.workspace.root_path)
            table.add_row(
                doc.name,
                doc.doctype or "unknown",
                str(rel_path)
            )
        
        self.console.print(table)
        self.print_info(f"Found {len(documents)} document(s)")
    
    def _resolve_document_path(self, path_str: str) -> Optional[Path]:
        """
        Resolve a path string (absolute, relative, or WikiLink) to a document Path.
        Handles specific logic for resolving potential new WikiLink paths.
        """
        path_str = path_str.strip()
        if not path_str:
            return None

        # Check for WikiLink format [[Link Name]]
        wikilink_match = re.match(r'^\[\[(.+)\]\]$', path_str)
        if wikilink_match:
            link_content = wikilink_match.group(1).strip()
            target_filename = f"{link_content.lstrip('/')}.md" # Ensure no leading slash in filename itself
            
            # Check if it's an absolute path within the workspace (starts with /)
            if link_content.startswith('/'):
                # Resolve relative to workspace root
                return self.workspace.root_path / target_filename
            else:
                # Relative WikiLink: Resolve relative to current doc or workspace root
                if self.active_document and self.active_document.path:
                    # Resolve relative to the *parent directory* of the active document
                    base_dir = self.active_document.path.parent
                    return base_dir / target_filename
                else:
                    # No active document, resolve relative to workspace root
                    return self.workspace.root_path / target_filename

        # Handle regular paths (non-WikiLink)
        path = Path(path_str)
        if not path.is_absolute():
            # Resolve relative paths relative to workspace root for consistency
            # Could potentially resolve relative to active doc dir here too if desired
            return self.workspace.root_path / path
        return path # It's already an absolute path

    def _handle_open(self, args: str = ""):
        """
        Handle the /open command.
        
        Args:
            args: Path to the document to open (relative, absolute, or [[WikiLink]])
                  If empty, reloads the current document.
        """
        if not self.workspace:
            self.print_error("No active workspace. Use /init to initialize a workspace.")
            return

        path_str = args.strip()

        # Handle empty args: Reload current document
        if not path_str:
            if not self.active_document:
                self.print_error("No active document to reload. Use /open <path> to open one.")
                return
            try:
                self.active_document._load()  # Use the internal load method to refresh
                self.print_success(f"Reloaded document: {self.active_document.name}")
                self.print_markdown(self.active_document.body) # Optionally redisplay content
            except DocumentError as e:
                self.print_error(f"Error reloading document: {str(e)}")
            return

        # Resolve the path (handles relative, absolute, WikiLink)
        resolved_path = self._resolve_document_path(path_str)
        if not resolved_path:
            self.print_error("Invalid path provided.")
            return

        # Check if the document exists
        if not resolved_path.exists():
            # Special handling for non-existent WikiLinks: Create and open
            if re.match(r'^\[\[(.+)\]\]$', path_str):
                self.print_info(f"Creating new document from WikiLink: {resolved_path}")
                try:
                    # Ensure parent directory exists
                    resolved_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Use the same creation logic as /new
                    document = Document.create_empty(resolved_path) 
                    document.save()
                    # Set as active document
                    self.active_document = document
                    self.active_doctype = document.doctype
                    self.active_agent = document.agent
                    self.print_success(f"Created and opened new document: {resolved_path.name}")
                    # Display the document content
                    self.print_markdown(document.body)
                except DocumentError as e:
                    self.print_error(f"Error creating document from WikiLink: {str(e)}")
            else:
                # Standard file not found error
                self.print_error(f"Document not found: {resolved_path}")
                self.print_info("Use /new to create a new document.")
            return # Return after handling non-existent case

        # Check if it's the same document already open
        if self.active_document and self.active_document.path == resolved_path:
            self.print_info(f"Document '{resolved_path.name}' is already open.")
            # Optionally force a reload here if desired, or just do nothing.
            # self._handle_open("") # Could call reload logic
            return

        try:
            # Load the document
            document = Document(resolved_path)
            self.active_document = document
            self.active_doctype = document.doctype
            self.active_agent = document.agent
            self.print_success(f"Opened document: {resolved_path.name}")

            # Display the document content
            self.print_markdown(document.body)

        except DocumentError as e:
            self.print_error(f"Error opening document: {str(e)}")
    
    def _handle_new(self, args: str = ""):
        """
        Handle the /new command.
        
        Args:
            args: Path to the new document to create
        """
        if not self.workspace:
            self.print_error("No active workspace. Use /init to initialize a workspace.")
            return
        
        if not args:
            self.print_error("Missing document path. Usage: /new <path>")
            return
        
        path_str = args.strip()
        path = Path(path_str)
        
        # Convert to absolute path if it's relative
        if not path.is_absolute():
            path = self.workspace.root_path / path
        
        # Check if the document already exists
        if path.exists():
            self.print_error(f"Document already exists: {path}")
            self.print_info("Use /open to open an existing document.")
            return
        
        try:
            # Create the document
            document = Document.create_empty(path)
            document.save()
            
            # Set as active document
            self.active_document = document
            self.active_doctype = document.doctype
            
            self.print_success(f"Created and opened new document: {path.name}")
            
            # Display the document content
            self.print_markdown(document.body)
            
        except DocumentError as e:
            self.print_error(f"Error creating document: {str(e)}")
    
    def _handle_info(self, args: str = ""):
        """
        Handle the /info command.
        
        Args:
            args: Not used
        """
        if not self.active_document:
            self.print_error("No active document. Use /open or /new to open a document.")
            return
        
        # Create a table for document metadata
        from rich.table import Table
        meta_table = Table(title="Document Metadata")
        meta_table.add_column("Property", style="cyan")
        meta_table.add_column("Value", style="green")
        
        # Add document properties
        meta_table.add_row("Name", self.active_document.name)
        meta_table.add_row("Path", str(self.active_document.path))
        meta_table.add_row("Type", self.active_document.doctype or "unknown")
        if self.active_agent: # Display agent if set
            meta_table.add_row("Agent", self.active_agent)
        
        # Add custom metadata
        for key, value in self.active_document.metadata.items():
            if key not in ['doctype', 'agent']:  # Avoid duplicating already shown fields
                meta_table.add_row(key, str(value))
        
        self.console.print(meta_table)
        
        # Display document content preview
        if self.active_document.body:
            preview = self.active_document.body[:500]  # First 500 chars
            if len(self.active_document.body) > 500:
                preview += "..."
            
            self.print_panel(
                Markdown(preview),
                title="Content Preview",
                style="blue"
            )
    
    def _handle_close(self, args: str = ""):
        """
        Handle the /close command.
        
        Args:
            args: Not used
        """
        if not self.active_document:
            self.print_error("No active document to close.")
            return
        
        doc_name = self.active_document.name
        self.active_document = None
        self.active_doctype = None
        
        self.print_success(f"Closed document: {doc_name}")
    
    def _handle_init(self, args: str = ""):
        """
        Handle the /init command.
        
        Args:
            args: Optional path to initialize workspace at
        """
        # Use current directory if no path is provided
        path_str = args.strip() if args else "."
        path = Path(path_str).expanduser().absolute()
        
        if self.workspace:
            self.print_warning(f"Already in workspace: {self.workspace.root_path}")
            if self.workspace.root_path == path:
                self.print_info("This is already the active workspace.")
                return
            self.print_info("Use /exit and start a new REPL session to switch workspaces.")
            return
        
        # Check if the path exists
        if not path.exists():
            try:
                path.mkdir(parents=True)
                self.print_info(f"Created directory: {path}")
            except Exception as e:
                self.print_error(f"Failed to create directory: {str(e)}")
                return
        
        # Initialize or validate the workspace
        try:
            # First, check if this is already a valid workspace
            try:
                with workspace_context(path) as workspace:
                    self.workspace = workspace
                    self.workspace_path = path
                    self.print_success(f"Opened existing workspace: {path}")
                    return
            except WorkspaceValidationError:
                # Not a valid workspace, initialize it
                pass
            
            # Import the initialization function
            from airic.core.init import initialize_workspace
            
            # Initialize the workspace
            success, messages = initialize_workspace(path)
            
            if success:
                # Load the newly initialized workspace
                with workspace_context(path) as workspace:
                    self.workspace = workspace
                    self.workspace_path = path
                
                self.print_success(f"Initialized new workspace: {path}")
                for msg in messages:
                    self.print_info(msg)
            else:
                self.print_error("Failed to initialize workspace:")
                for msg in messages:
                    self.print_error(f"  - {msg}")
                
        except Exception as e:
            self.print_error(f"Error during workspace initialization: {str(e)}")
    
    def _handle_edit(self, args: str = ""):
        """
        Handle the /edit command.
        
        Args:
            args: Not used
        """
        if not self.active_document:
            self.print_error("No active document to edit.")
            self.print_info("Use /open <path> or /new <path> to open or create a document.")
            return
        
        self.print_info(f"Editing document: {self.active_document.name}")
        
        # Display current content
        self.print_panel(
            Markdown(self.active_document.body),
            title="Current Content",
            style="blue"
        )
        
        # Use prompt_toolkit for multi-line input
        from prompt_toolkit.shortcuts import prompt
        from prompt_toolkit.lexers import PygmentsLexer
        from pygments.lexers.markup import MarkdownLexer
        
        self.print_info("Enter new content below (press Ctrl+D or Ctrl+Z on a new line to finish):")
        
        try:
            # Get multi-line input with Markdown highlighting
            new_content = prompt(
                "Edit> ",
                multiline=True,
                lexer=PygmentsLexer(MarkdownLexer),
                default=self.active_document.body
            )
            
            # Update document body
            self.active_document.update_body(new_content)
            
            self.print_success("Document content updated.")
            self.print_info("Use /save to save the changes to disk.")
            
        except KeyboardInterrupt:
            self.print_warning("Edit cancelled.")
        except Exception as e:
            self.print_error(f"Error during edit: {str(e)}")
    
    def _handle_save(self, args: str = ""):
        """
        Handle the /save command.
        
        Args:
            args: Not used
        """
        if not self.active_document:
            self.print_error("No active document to save.")
            return
        
        try:
            # Save the document
            self.active_document.save()
            self.print_success(f"Document saved: {self.active_document.path}")
        except DocumentError as e:
            self.print_error(f"Error saving document: {str(e)}")
        except Exception as e:
            self.print_error(f"Unexpected error during save: {str(e)}")
    
    def _handle_ai(self, args: str = ""):
        """
        Handle the /ai command.
        
        Args:
            args: Optional arguments like "settings" or "info"
        """
        if not args:
            self._show_ai_info()
            return
        
        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower()
        subargs = parts[1] if len(parts) > 1 else ""
        
        if subcommand == "info":
            self._show_ai_info()
        elif subcommand == "settings":
            self._handle_ai_settings(subargs)
        else:
            self.print_error(f"Unknown AI subcommand: {subcommand}")
            self.print_info("Available subcommands: info, settings")
    
    def _show_ai_info(self):
        """Display information about the current AI service."""
        # Create a table for AI service information
        from rich.table import Table
        table = Table(title="AI Service Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        # Add service properties
        service_type = self.ai_service.__class__.__name__
        table.add_row("Service Type", service_type)
        
        # Add configuration
        for key, value in self.ai_service.config.items():
            table.add_row(key, str(value))
        
        if not self.ai_service.config:
            table.add_row("Config", "No custom configuration")
        
        self.console.print(table)
        
        # Add help text
        self.print_info("Use '/ai settings <key>=<value>' to configure the AI service")
        
        # Example commands
        self.print_panel(
            "Examples:\n"
            "/ai settings model=gpt-4\n"
            "/ai settings temperature=0.7",
            title="AI Configuration Examples",
            style="blue"
        )
    
    def _handle_ai_settings(self, args: str):
        """
        Handle AI settings configuration.
        
        Args:
            args: Settings arguments in the format "key=value"
        """
        if not args:
            self._show_ai_info()
            return
        
        # Parse key=value pairs
        try:
            # Split by spaces and then by =
            settings = {}
            for pair in args.split():
                if "=" not in pair:
                    self.print_error(f"Invalid setting format: {pair}. Use key=value")
                    continue
                    
                key, value = pair.split("=", 1)
                
                # Try to convert value to appropriate type
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit():
                    value = float(value)
                
                settings[key] = value
            
            if not settings:
                self.print_error("No valid settings provided")
                return
            
            # Update AI service config
            self.ai_service.config.update(settings)
            
            # Recreate the AI service with the new config
            service_type = "mock"  # Currently only mock is supported
            self.ai_service = get_ai_service(service_type, self.ai_service.config)
            
            self.print_success("AI settings updated successfully")
            self._show_ai_info()
            
        except Exception as e:
            self.print_error(f"Error updating AI settings: {str(e)}")
    
    def _print_welcome_message(self):
        """Print a welcome message when starting the REPL."""
        welcome_panel = Panel(
            Text(
                "Your AI-assisted document workspace.\n"
                "Type [bold]/help[/bold] for available commands.\n"
                "Type any text without a leading [bold]/[/bold] to talk with the AI.",
                justify="center"
            ),
            title="[bold]Welcome to Airic![/bold]",
            border_style="green",
            box=box.DOUBLE
        )
        self.console.print(welcome_panel)
    
    # Rich output formatting helpers
    
    def print_info(self, message: str):
        """Print an informational message."""
        self.console.print(f"[blue]{message}[/blue]")
    
    def print_success(self, message: str):
        """Print a success message."""
        self.console.print(f"[green]{message}[/green]")
    
    def print_warning(self, message: str):
        """Print a warning message."""
        self.console.print(f"[yellow]{message}[/yellow]")
    
    def print_error(self, message: str):
        """Print an error message."""
        self.console.print(f"[bold red]{message}[/bold red]")
    
    def print_markdown(self, markdown_text: str):
        """
        Render and print Markdown text.
        
        Args:
            markdown_text: Markdown formatted text
        """
        self.console.print(Markdown(markdown_text))
    
    def print_code(self, code: str, language: str = "python"):
        """
        Print code with syntax highlighting.
        
        Args:
            code: The code to print
            language: The programming language for syntax highlighting
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)
    
    def print_panel(self, content: Union[str, Any], title: str = None, style: str = "none"):
        """
        Print content in a panel.
        
        Args:
            content: The content to display in the panel
            title: Optional title for the panel
            style: Style for the panel border
        """
        if isinstance(content, str):
            content = Text(content)
        
        panel = Panel(
            content,
            title=title,
            border_style=style,
            box=box.ROUNDED
        )
        self.console.print(panel)


async def start_repl(workspace_path: Optional[Path] = None): # Make start_repl async
    """
    Start the Airic REPL asynchronously.
    
    Args:
        workspace_path: Optional path to an Airic workspace
    """
    repl = AiricREPL(workspace_path)
    await repl.start() # Await the start method


if __name__ == "__main__":
    # When run as a script, start the REPL using asyncio
    try:
        asyncio.run(start_repl()) # Use asyncio.run
    except KeyboardInterrupt:
        print("\nExiting...") 