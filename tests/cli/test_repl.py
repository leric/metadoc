"""
Tests for the REPL interface.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from airic.cli.repl import AiricREPL
from prompt_toolkit.formatted_text import HTML
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel


class TestAiricREPL:
    """Test suite for the AiricREPL class."""
    
    @pytest.fixture
    def repl(self):
        """Create a REPL instance for testing."""
        with patch('airic.cli.repl.PromptSession'):
            with patch('airic.cli.repl.FileHistory'):
                with patch('airic.cli.repl.workspace_context'):
                    with patch('airic.cli.repl.WordCompleter'):
                        return AiricREPL()
    
    def test_initialization(self, repl):
        """Test REPL initialization."""
        assert repl is not None
        assert repl.workspace is None
        assert repl.active_document is None
        assert repl.active_doctype is None
    
    def test_get_prompt_text(self, repl):
        """Test prompt text generation."""
        # Default prompt
        prompt_text = repl._get_prompt_text()
        assert isinstance(prompt_text, HTML)
        assert 'airic' in prompt_text.value
        
        # With workspace
        repl.workspace = MagicMock()
        repl.workspace.config.get.return_value = 'test-workspace'
        prompt_text = repl._get_prompt_text()
        assert 'test-workspace' in prompt_text.value
        
        # With active document
        repl.active_document = MagicMock()
        repl.active_document.name = 'test-document.md'
        prompt_text = repl._get_prompt_text()
        assert 'test-document.md' in prompt_text.value
    
    def test_status_bar(self, repl):
        """Test status bar generation."""
        # Default status (no workspace, no document)
        status_bar = repl._get_status_bar()
        assert isinstance(status_bar, HTML)
        assert 'No active workspace' in status_bar.value
        assert 'No active document' in status_bar.value
        
        # With workspace only
        repl.workspace = MagicMock()
        repl.workspace.config.get.return_value = 'test-workspace'
        status_bar = repl._get_status_bar()
        assert 'test-workspace' in status_bar.value
        assert 'No active document' in status_bar.value
        
        # With workspace and document, no doctype
        repl.active_document = MagicMock()
        repl.active_document.name = 'test-document.md'
        repl.active_doctype = None
        status_bar = repl._get_status_bar()
        assert 'test-workspace' in status_bar.value
        assert 'test-document.md' in status_bar.value
        assert 'Type:' in status_bar.value
        assert 'none' in status_bar.value
        
        # With workspace, document, and doctype
        repl.active_doctype = 'markdown'
        status_bar = repl._get_status_bar()
        assert 'test-workspace' in status_bar.value
        assert 'test-document.md' in status_bar.value
        assert 'Type:' in status_bar.value
        assert 'markdown' in status_bar.value
    
    def test_handle_command(self, repl):
        """Test command handling."""
        # Replace the command handlers with mocks
        help_mock = MagicMock()
        exit_mock = MagicMock()
        
        # Store the original handlers to restore later
        original_commands = repl.commands.copy()
        
        try:
            # Replace with our mocks
            repl.commands = {
                'help': help_mock,
                'exit': exit_mock,
            }
            
            # Test help command
            repl._handle_command('help')
            help_mock.assert_called_once_with('')
            
            # Test with arguments
            repl._handle_command('help some args')
            help_mock.assert_called_with('some args')
            
            # Test unknown command
            with patch.object(repl, 'print_error') as mock_error:
                with patch.object(repl, 'print_info') as mock_info:
                    repl._handle_command('unknown_command')
                    mock_error.assert_called_once()
                    mock_info.assert_called_once()
                
        finally:
            # Restore original handlers
            repl.commands = original_commands
    
    def test_process_input_command(self, repl):
        """Test processing command input."""
        with patch.object(repl, '_handle_command') as mock_handle:
            repl._process_input('/help')
            mock_handle.assert_called_once_with('help')
    
    def test_process_input_text(self, repl):
        """Test processing text input."""
        with patch.object(repl, '_handle_text_input') as mock_handle:
            repl._process_input('Hello AI')
            mock_handle.assert_called_once_with('Hello AI')
    
    def test_rich_formatting_helpers(self, repl):
        """Test the Rich formatting helper methods."""
        # Mock the console.print method
        with patch.object(repl.console, 'print') as mock_print:
            # Test info message
            repl.print_info("Test info")
            mock_print.assert_called_with("[blue]Test info[/blue]")
            
            # Test success message
            repl.print_success("Test success")
            mock_print.assert_called_with("[green]Test success[/green]")
            
            # Test warning message
            repl.print_warning("Test warning")
            mock_print.assert_called_with("[yellow]Test warning[/yellow]")
            
            # Test error message
            repl.print_error("Test error")
            mock_print.assert_called_with("[bold red]Test error[/bold red]")
            
            # Test markdown formatting
            repl.print_markdown("**Bold text**")
            assert mock_print.call_args[0][0].__class__ == Markdown
            
            # Test code formatting
            repl.print_code("print('hello')")
            assert mock_print.call_args[0][0].__class__ == Syntax
            
            # Test panel display
            repl.print_panel("Test panel")
            assert mock_print.call_args[0][0].__class__ == Panel 