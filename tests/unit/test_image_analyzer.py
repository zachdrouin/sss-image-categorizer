"""
Unit tests for image analysis functionality
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
import base64
import requests
import tempfile
import pandas as pd
from io import BytesIO

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the module being tested
from app.image_categorizer import (
    analyze_image_with_gpt4v, 
    encode_image, 
    mock_analyze_image,
    post_process_people_categories
)

class TestImageAnalyzer:
    """Test suite for image analysis functionality"""
    
    @pytest.fixture
    def sample_image_url(self):
        """Return a sample image URL for testing"""
        return "https://example.com/test-image.jpg"
    
    @pytest.fixture
    def sample_api_response(self):
        """Create a sample API response in the format expected by the function"""
        # This matches the structure returned by the OpenAI client
        class MockResponse:
            def __init__(self, content):
                self.choices = [type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': content
                    })
                })]
        
        # Sample response content with categories
        content = """Based on analyzing this image, I would categorize it with the following tags:

1. Category > Nature + Landscapes
2. ORIENTATION > Horizontal
3. Colors > Blue
4. Colors > Green
5. PEOPLE > No People
6. Copy Space > Large

The image appears to be a scenic landscape with natural elements."""
        
        return MockResponse(content)
    
    def test_encode_image(self, sample_image_url, monkeypatch):
        """Test image encoding functionality"""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.content = b"test image content"
        mock_response.raise_for_status = MagicMock()
        
        # Mock the requests.get method
        def mock_get(*args, **kwargs):
            return mock_response
        
        # Apply the monkeypatch
        monkeypatch.setattr(requests, "get", mock_get)
        
        # Call the function
        result = encode_image(sample_image_url)
        
        # Check result is correctly base64 encoded
        expected = base64.b64encode(b"test image content").decode('utf-8')
        assert result == expected
    
    def test_encode_image_error(self, sample_image_url, monkeypatch):
        """Test image encoding error handling"""
        # Mock requests.get to raise an exception
        def mock_get_error(*args, **kwargs):
            raise requests.RequestException("Connection error")
        
        # Apply the monkeypatch
        monkeypatch.setattr(requests, "get", mock_get_error)
        
        # Call the function
        result = encode_image(sample_image_url)
        
        # Should return None on error
        assert result is None
    
    def test_mock_analyze_image(self, monkeypatch):
        """Test mock image analysis"""
        # Mock random.choice to return predictable results
        def mock_choice(choices):
            return choices[0]  # Always return the first item
        
        # Apply the monkeypatch
        monkeypatch.setattr("random.choice", mock_choice)
        
        # Call the function
        result = mock_analyze_image()
        
        # Check that we got expected categories
        assert isinstance(result, list)
        assert len(result) >= 4  # Should have at least 4 categories
        
        # Categories should be from specific groups
        category_prefixes = ["Category >", "Colors >", "ORIENTATION >", "PEOPLE >"]
        for prefix in category_prefixes:
            assert any(cat.startswith(prefix) for cat in result)
    
    @patch('app.image_categorizer.category_manager')
    @patch('app.image_categorizer.client')
    @patch('app.image_categorizer.encode_image')
    def test_analyze_image_with_gpt4v(self, mock_encode, mock_client, mock_category_manager, sample_image_url, sample_api_response):
        """Test GPT-4 Vision image analysis"""
        # Set up the mocks
        mock_encode.return_value = "base64_encoded_image_content"
        mock_client.chat.completions.create.return_value = sample_api_response
        
        # Mock the category validation to return True for our expected categories
        def validate_category_side_effect(category):
            expected_categories = [
                "Category > Nature + Landscapes",
                "ORIENTATION > Horizontal",
                "Colors > Blue",
                "Colors > Green",
                "PEOPLE > No People",
                "Copy Space > Large"
            ]
            return category in expected_categories
            
        mock_category_manager.validate_category.side_effect = validate_category_side_effect
        
        # Call the function
        result = analyze_image_with_gpt4v(sample_image_url)
        
        # Check that we have categories in the result
        assert len(result) > 0
        
        # Check that the mock was called
        assert mock_client.chat.completions.create.called
        assert mock_encode.called
    
    @patch('app.image_categorizer.client')
    @patch('app.image_categorizer.encode_image')
    def test_analyze_image_api_error(self, mock_encode, mock_client, sample_image_url):
        """Test handling API errors"""
        # Set up the mocks
        mock_encode.return_value = "base64_encoded_image_content"
        
        # Make the API call raise an exception
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Call the function
        result = analyze_image_with_gpt4v(sample_image_url)
        
        # Should return empty list on error
        assert result == []
    
    @patch('app.image_categorizer.category_manager')
    def test_post_process_people_categories(self, mock_category_manager):
        """Test post-processing of people categories"""
        # Set up mock for category_manager
        mock_category_manager.validate_category.return_value = True
        
        # Sample input categories - make sure there are only 3 to start
        input_categories = [
            "Category > Lifestyle",
            "PEOPLE > Any People",
            "Colors > Blue"
        ]
        
        # Sample description mentioning specific people attributes
        description = "A woman in her 30s with her children in the park"
        
        # Call the function
        result = post_process_people_categories(input_categories, description)
        
        # Check that the function returns a list
        assert isinstance(result, list)
        
        # Original categories should still be there
        assert "Category > Lifestyle" in result
        assert "Colors > Blue" in result
        
        # Check that we have categories in the result
        assert len(result) >= 3  # At least the original categories
