"""
Tests for the document-related commands in the REPL.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from airic.cli.repl import AiricREPL
from airic.core.document import Document


class TestReplDocumentCommands:
    """Test suite for the REPL document commands."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary directory for workspace tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def repl(self):
        """Create a REPL instance for testing."""
        with patch('airic.cli.repl.PromptSession'):
            with patch('airic.cli.repl.FileHistory'):
                with patch('airic.cli.repl.workspace_context'):
                    with patch('airic.cli.repl.WordCompleter'):
                        return AiricREPL()
    
    def test_handle_list_no_workspace(self, repl):
        """Test list command with no active workspace."""
        with patch.object(repl, 'print_error') as mock_error:
            repl._handle_list("")
            mock_error.assert_called_once()
            assert "No active workspace" in mock_error.call_args[0][0]
    
    def test_handle_list(self, repl, temp_workspace):
        """Test list command with active workspace."""
        # Setup workspace and test documents
        repl.workspace = MagicMock()
        repl.workspace.root_path = temp_workspace
        
        # Create test documents
        doc1 = Document.create_empty(temp_workspace / "doc1.md", {"doctype": "test"}, "Test Doc 1")
        doc2 = Document.create_empty(temp_workspace / "doc2.md", {"doctype": "test"}, "Test Doc 2")
        doc1.save()
        doc2.save()
        
        with patch('airic.cli.repl.find_documents') as mock_find:
            mock_find.return_value = [doc1, doc2]
            
            with patch.object(repl.console, 'print') as mock_print:
                with patch.object(repl, 'print_info') as mock_info:
                    repl._handle_list("")
                    
                    # Check that find_documents was called with correct parameters
                    mock_find.assert_called_once_with(temp_workspace, "*.md")
                    
                    # Check that info messages were printed
                    assert mock_info.call_count >= 2
                    assert "Found 2 document(s)" in mock_info.call_args_list[-1][0][0]
                    
                    # Check that a table was printed
                    assert mock_print.call_count >= 1
    
    def test_handle_open_no_workspace(self, repl):
        """Test open command with no active workspace."""
        with patch.object(repl, 'print_error') as mock_error:
            repl._handle_open("doc.md")
            mock_error.assert_called_once()
            assert "No active workspace" in mock_error.call_args[0][0]
    
    def test_handle_open_missing_path(self, repl):
        """Test open command with missing path."""
        repl.workspace = MagicMock()
        
        with patch.object(repl, 'print_error') as mock_error:
            repl._handle_open("")
            mock_error.assert_called_once()
            assert "Missing document path" in mock_error.call_args[0][0]
    
    def test_handle_open_nonexistent_document(self, repl):
        """Test open command with non-existent document."""
        repl.workspace = MagicMock()
        repl.workspace.root_path = Path("/test")
        
        with patch.object(repl, 'print_error') as mock_error:
            with patch.object(repl, 'print_info') as mock_info:
                repl._handle_open("nonexistent.md")
                mock_error.assert_called_once()
                assert "Document not found" in mock_error.call_args[0][0]
                assert "Use /new" in mock_info.call_args[0][0]
    
    def test_handle_open(self, repl, temp_workspace):
        """Test open command with valid document."""
        # Setup workspace
        repl.workspace = MagicMock()
        repl.workspace.root_path = temp_workspace
        
        # Create a test document
        doc_path = temp_workspace / "test.md"
        doc = Document.create_empty(doc_path, {"doctype": "test"}, "Test Document")
        doc.save()
        
        with patch('airic.cli.repl.Document', return_value=doc) as mock_document:
            with patch.object(repl, 'print_success') as mock_success:
                with patch.object(repl, 'print_markdown') as mock_markdown:
                    repl._handle_open(str(doc_path))
                    
                    # Check that Document was created with correct path
                    mock_document.assert_called_once()
                    
                    # Check that success message was printed
                    mock_success.assert_called_once()
                    assert "Opened document" in mock_success.call_args[0][0]
                    
                    # Check that document content was displayed
                    mock_markdown.assert_called_once()
                    
                    # Check that active document was set
                    assert repl.active_document == doc
                    assert repl.active_doctype == doc.doctype
    
    def test_handle_new(self, repl, temp_workspace):
        """Test new command."""
        # Setup workspace
        repl.workspace = MagicMock()
        repl.workspace.root_path = temp_workspace
        
        doc_path = temp_workspace / "new_doc.md"
        
        # Mock the Document.create_empty and save methods
        mock_doc = MagicMock()
        mock_doc.path = doc_path
        mock_doc.name = "new_doc.md"
        
        with patch('airic.cli.repl.Document.create_empty', return_value=mock_doc) as mock_create:
            with patch.object(repl, 'print_success') as mock_success:
                with patch.object(repl, 'print_markdown') as mock_markdown:
                    repl._handle_new(str(doc_path))
                    
                    # Check that Document.create_empty was called
                    mock_create.assert_called_once()
                    
                    # Check that document was saved
                    mock_doc.save.assert_called_once()
                    
                    # Check that success message was printed
                    mock_success.assert_called_once()
                    assert "Created and opened" in mock_success.call_args[0][0]
                    
                    # Check that active document was set
                    assert repl.active_document == mock_doc
    
    def test_handle_info(self, repl):
        """Test info command."""
        # Test with no active document
        with patch.object(repl, 'print_error') as mock_error:
            repl._handle_info("")
            mock_error.assert_called_once()
            assert "No active document" in mock_error.call_args[0][0]
        
        # Test with active document
        mock_doc = MagicMock()
        mock_doc.name = "test.md"
        mock_doc.path = Path("/test/test.md")
        mock_doc.doctype = "test"
        mock_doc.metadata = {"title": "Test", "version": "1.0.0"}
        mock_doc.body = "# Test\n\nThis is a test document."
        
        repl.active_document = mock_doc
        
        with patch.object(repl.console, 'print') as mock_print:
            with patch.object(repl, 'print_panel') as mock_panel:
                repl._handle_info("")
                
                # Check that metadata table was printed
                assert mock_print.call_count >= 1
                
                # Check that content preview was displayed
                assert mock_panel.call_count >= 1
    
    def test_handle_close(self, repl):
        """Test close command."""
        # Test with no active document
        with patch.object(repl, 'print_error') as mock_error:
            repl._handle_close("")
            mock_error.assert_called_once()
            assert "No active document" in mock_error.call_args[0][0]
        
        # Test with active document
        mock_doc = MagicMock()
        mock_doc.name = "test.md"
        
        repl.active_document = mock_doc
        repl.active_doctype = "test"
        
        with patch.object(repl, 'print_success') as mock_success:
            repl._handle_close("")
            
            # Check that success message was printed
            mock_success.assert_called_once()
            assert "Closed document" in mock_success.call_args[0][0]
            
            # Check that active document was cleared
            assert repl.active_document is None
            assert repl.active_doctype is None 