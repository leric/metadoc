"""
Tests for the AI-related functionality in the REPL.
"""
import pytest
from unittest.mock import patch, MagicMock, call

from airic.cli.repl import AiricREPL
from airic.core.document import Document
from airic.core.ai_service import MockAIService, AIServiceError


class TestReplAI:
    """Test suite for REPL AI functionality."""
    
    @pytest.fixture
    def repl(self):
        """Create a REPL instance for testing."""
        with patch('airic.cli.repl.PromptSession'):
            with patch('airic.cli.repl.FileHistory'):
                with patch('airic.cli.repl.workspace_context'):
                    with patch('airic.cli.repl.WordCompleter'):
                        with patch('airic.cli.repl.get_ai_service') as mock_get_service:
                            # Create a mock service
                            mock_service = MagicMock()
                            mock_get_service.return_value = mock_service
                            
                            repl = AiricREPL()
                            # Verify the service was created
                            assert repl.ai_service == mock_service
                            return repl
    
    def test_handle_text_input_no_document(self, repl):
        """Test processing text with no active document."""
        text = "Hello, AI!"
        
        # Configure mock service
        repl.ai_service.process_text.return_value = "Mock AI response"
        
        with patch.object(repl, 'print_markdown') as mock_print:
            repl._handle_text_input(text)
            
            # Check that process_text was called with the input text
            repl.ai_service.process_text.assert_called_once_with(text)
            
            # Check that response was printed as markdown
            mock_print.assert_called_once_with("Mock AI response")
    
    def test_handle_text_input_with_document(self, repl):
        """Test processing text with an active document."""
        text = "Summarize this document"
        
        # Set up an active document
        mock_doc = MagicMock()
        repl.active_document = mock_doc
        repl.active_doctype = "test"
        
        # Configure mock service
        repl.ai_service.process_document.return_value = "Mock document analysis"
        
        with patch.object(repl, 'print_info') as mock_info:
            with patch.object(repl, 'print_markdown') as mock_print:
                repl._handle_text_input(text)
                
                # Check that process_document was called with the document and input text
                repl.ai_service.process_document.assert_called_once_with(mock_doc, text)
                
                # Check that the document context was announced
                assert mock_info.call_count >= 1
                assert "context of document" in mock_info.call_args[0][0]
                
                # Check that response was printed as markdown
                mock_print.assert_called_once_with("Mock document analysis")
    
    def test_handle_text_input_service_error(self, repl):
        """Test handling service errors during text processing."""
        # Configure mock service to raise an error
        repl.ai_service.process_text.side_effect = AIServiceError("Test error")
        
        with patch.object(repl, 'print_error') as mock_error:
            repl._handle_text_input("Hello")
            
            # Check that the error was reported
            mock_error.assert_called_with("AI processing error: Test error")
    
    def test_handle_ai_command(self, repl):
        """Test the /ai command."""
        # Test without arguments
        with patch.object(repl, '_show_ai_info') as mock_show_info:
            repl._handle_ai("")
            mock_show_info.assert_called_once()
        
        # Test with info subcommand
        with patch.object(repl, '_show_ai_info') as mock_show_info:
            repl._handle_ai("info")
            mock_show_info.assert_called_once()
        
        # Test with settings subcommand
        with patch.object(repl, '_handle_ai_settings') as mock_settings:
            repl._handle_ai("settings model=test")
            mock_settings.assert_called_once_with("model=test")
        
        # Test with unknown subcommand
        with patch.object(repl, 'print_error') as mock_error:
            with patch.object(repl, 'print_info') as mock_info:
                repl._handle_ai("unknown")
                mock_error.assert_called_once()
                assert "Unknown AI subcommand" in mock_error.call_args[0][0]
                mock_info.assert_called_once()
    
    def test_show_ai_info(self, repl):
        """Test displaying AI service information."""
        # Configure mock service
        repl.ai_service.__class__.__name__ = "MockAIService"
        repl.ai_service.config = {"model": "test-model", "temperature": 0.7}
        
        with patch.object(repl.console, 'print') as mock_print:
            with patch.object(repl, 'print_info') as mock_info:
                with patch.object(repl, 'print_panel') as mock_panel:
                    repl._show_ai_info()
                    
                    # Check that a table was printed
                    mock_print.assert_called_once()
                    
                    # Check that help text was displayed
                    assert mock_info.call_count >= 1
                    
                    # Check that example commands were shown
                    mock_panel.assert_called_once()
    
    def test_handle_ai_settings(self, repl):
        """Test updating AI service settings."""
        # Configure initial service state
        repl.ai_service.config = {}
        
        with patch('airic.cli.repl.get_ai_service') as mock_get_service:
            # Create a new mock service for the update
            new_service = MagicMock()
            new_service.config = {"model": "test-model", "temperature": 0.7}
            mock_get_service.return_value = new_service
            
            with patch.object(repl, '_show_ai_info') as mock_show_info:
                with patch.object(repl, 'print_success') as mock_success:
                    # Test updating settings
                    repl._handle_ai_settings("model=test-model temperature=0.7")
                    
                    # Check that service was configured with correct settings
                    mock_get_service.assert_called_once_with(
                        "mock", {"model": "test-model", "temperature": 0.7}
                    )
                    
                    # Check that the service was replaced
                    assert repl.ai_service == new_service
                    
                    # Check that the config is accessible
                    assert repl.ai_service.config == {"model": "test-model", "temperature": 0.7}
                    
                    # Check that success was reported
                    mock_success.assert_called_once()
                    assert "updated successfully" in mock_success.call_args[0][0]
                    
                    # Check that updated info was shown
                    mock_show_info.assert_called_once()
    
    def test_handle_ai_settings_type_conversion(self, repl):
        """Test type conversion for AI settings."""
        repl.ai_service.config = {}
        
        with patch('airic.cli.repl.get_ai_service') as mock_get_service:
            # Create a new mock service with properly typed config values
            new_service = MagicMock()
            new_service.config = {
                "bool_val": True,
                "int_val": 42, 
                "float_val": 3.14,
                "str_val": "text"
            }
            mock_get_service.return_value = new_service
            
            # Test with different value types
            repl._handle_ai_settings("bool_val=true int_val=42 float_val=3.14 str_val=text")
            
            # Verify the service was created with correct parameters
            mock_get_service.assert_called_once_with("mock", {
                "bool_val": True,
                "int_val": 42, 
                "float_val": 3.14,
                "str_val": "text"
            })
            
            # Check that the service was updated
            assert repl.ai_service == new_service
            
            # Check that values were converted to appropriate types
            assert repl.ai_service.config["bool_val"] is True
            assert repl.ai_service.config["int_val"] == 42
            assert repl.ai_service.config["float_val"] == 3.14
            assert repl.ai_service.config["str_val"] == "text"
    
    def test_handle_ai_settings_error(self, repl):
        """Test error handling in AI settings."""
        # Configure service to raise an error
        repl.ai_service.config = {}
        
        with patch('airic.cli.repl.get_ai_service') as mock_get_service:
            mock_get_service.side_effect = AIServiceError("Test error")
            
            with patch.object(repl, 'print_error') as mock_error:
                repl._handle_ai_settings("model=test")
                
                # Check that the error was reported
                mock_error.assert_called_with("Error updating AI settings: Test error") 