"""
Tests for the AI service module.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from airic.core.ai_service import (
    AIService, MockAIService, get_ai_service, AIServiceError
)
from airic.core.document import Document


class TestAIService:
    """Test suite for the AIService base class."""
    
    def test_base_class_methods(self):
        """Test that base class methods raise NotImplementedError."""
        service = AIService()
        
        with pytest.raises(NotImplementedError):
            service.process_text("Hello")
        
        with pytest.raises(NotImplementedError):
            mock_doc = MagicMock()
            service.process_document(mock_doc, "Hello")
    
    def test_config_initialization(self):
        """Test configuration initialization."""
        # Test with default config
        service = AIService()
        assert service.config == {}
        
        # Test with custom config
        config = {"model": "test-model", "temperature": 0.7}
        service = AIService(config)
        assert service.config == config


class TestMockAIService:
    """Test suite for the MockAIService class."""
    
    def test_process_text(self):
        """Test processing text with mock service."""
        service = MockAIService()
        
        # Test greeting responses
        response = service.process_text("hello")
        assert "Hello!" in response
        
        response = service.process_text("hi there")
        assert "Hello!" in response
        
        # Test help responses
        response = service.process_text("help me")
        assert "I can help you with" in response
        
        # Test question responses
        response = service.process_text("What is this?")
        assert "interesting question about" in response
        
        # Test default response
        response = service.process_text("some random text")
        assert "I received your input" in response
    
    def test_process_document(self):
        """Test processing documents with mock service."""
        service = MockAIService()
        
        # Create a mock document
        doc = MagicMock()
        doc.name = "test.md"
        doc.doctype = "test"
        doc.metadata = {"title": "Test Document"}
        doc.body = "# Test Document\n\nThis is a test document."
        
        # Test summary responses
        response = service.process_document(doc, "summarize this")
        assert "Summary of Test Document" in response
        
        # Test extraction responses
        response = service.process_document(doc, "extract key information")
        assert "Key Information from Test Document" in response
        
        # Test question responses
        response = service.process_document(doc, "What is this document about?")
        assert "Regarding your question about Test Document" in response
        
        # Test default response
        response = service.process_document(doc, "some random text")
        assert "I've analyzed the test titled" in response


class TestGetAIService:
    """Test suite for the get_ai_service factory function."""
    
    def test_get_mock_service(self):
        """Test getting a mock service."""
        service = get_ai_service("mock")
        assert isinstance(service, MockAIService)
        
        # Test with config
        config = {"model": "test-model"}
        service = get_ai_service("mock", config)
        assert isinstance(service, MockAIService)
        assert service.config == config
    
    def test_unknown_service_type(self):
        """Test error on unknown service type."""
        with pytest.raises(AIServiceError):
            get_ai_service("unknown")


class TestIntegration:
    """Integration tests for AI services with actual Document instances."""
    
    def test_document_integration(self):
        """Test AI service with real Document instances."""
        # Create a test document
        doc_path = Path("test.md")
        content = """---
title: Test Integration
doctype: test
---

# Test Document

This is a test document for AI service integration.
"""
        doc = Document(doc_path, content)
        
        # Process with mock service
        service = MockAIService()
        response = service.process_document(doc, "Summarize this document")
        
        # Check response contains document information
        assert "Test Integration" in response
        assert "test" in response
        assert "characters long" in response 