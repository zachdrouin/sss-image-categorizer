"""
Integration tests for the web interface
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Now import the app modules
from app.web_categorizer import app, get_api_key, save_api_key

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestWebInterface:
    """Test suite for web interface functionality"""
    
    def test_index_route(self, client):
        """Test the index route redirects appropriately"""
        # Mock get_api_key to return None (first run)
        with patch('app.web_categorizer.get_api_key', return_value=None):
            with patch('app.web_categorizer.os.path.exists', return_value=False):
                response = client.get('/')
                # Should redirect to welcome page on first run
                assert response.status_code == 302
                assert 'welcome' in response.location
        
        # Mock get_api_key to return a value (not first run)
        with patch('app.web_categorizer.get_api_key', return_value='test_key'):
            with patch('app.web_categorizer.os.path.exists', return_value=True):
                response = client.get('/')
                # Should show the main page
                assert response.status_code == 200
    
    def test_welcome_page(self, client):
        """Test the welcome page"""
        response = client.get('/welcome')
        assert response.status_code == 200
        assert b'Welcome to Image Categorizer' in response.data
    
    def test_settings_page(self, client):
        """Test the settings page"""
        with patch('app.web_categorizer.get_api_key', return_value='test_key'):
            response = client.get('/settings')
            assert response.status_code == 200
            assert b'Settings' in response.data
            # API key should be masked
            assert b'*****' in response.data
    
    def test_api_key_management(self):
        """Test API key storage and retrieval"""
        test_key = 'test_api_key_123'
        
        # Mock keyring functions
        with patch('keyring.set_password', return_value=None) as mock_set:
            result = save_api_key(test_key)
            assert result is True
            mock_set.assert_called_once()
        
        # Mock keyring get_password
        with patch('keyring.get_password', return_value=test_key) as mock_get:
            key = get_api_key()
            assert key == test_key
            mock_get.assert_called_once()
    
    def test_process_route(self, client):
        """Test the process route"""
        with patch('app.web_categorizer.threading.Thread') as mock_thread:
            response = client.post('/process', data={
                'input_file': '/test/input.csv',
                'output_file': '/test/output.csv',
                'api_key': 'test_key',
                'batch_size': '5',
                'start_row': '0',
                'mock_mode': 'false'
            })
            
            # Should start processing thread and return success
            assert response.status_code == 200
            assert mock_thread.called
            
            # Response should be JSON
            json_data = response.get_json()
            assert json_data['success'] is True
    
    def test_get_progress(self, client):
        """Test getting progress information"""
        # Set up test progress data
        with patch('app.web_categorizer.progress', {
            'current': 5,
            'total': 10,
            'message': 'Processing...',
            'complete': False,
            'success': True
        }):
            response = client.get('/progress')
            
            # Should return progress information
            assert response.status_code == 200
            
            # Response should be JSON with progress data
            json_data = response.get_json()
            assert json_data['current'] == 5
            assert json_data['total'] == 10
            assert json_data['progress_percent'] == 50  # 5/10 = 50%
            assert json_data['message'] == 'Processing...'
    
    def test_apply_categories_to_all(self, client):
        """Test applying categories to all images"""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            f.write(b'images,categories\nhttp://example.com/img1.jpg,\nhttp://example.com/img2.jpg,\n')
            temp_file = f.name
        
        try:
            # Test the apply_categories_to_all route
            with patch('pandas.read_csv', return_value=pd.DataFrame({
                'images': ['http://example.com/img1.jpg', 'http://example.com/img2.jpg'],
                'categories': ['', '']
            })):
                with patch('pandas.DataFrame.to_csv'):
                    response = client.post('/apply_categories_to_all', json={
                        'input_file': temp_file,
                        'categories': ['Category > Test', 'Colors > Blue']
                    })
                    
                    # Should return success
                    assert response.status_code == 200
                    json_data = response.get_json()
                    assert json_data['success'] is True
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
