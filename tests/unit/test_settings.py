"""
Unit tests for settings module
"""

import os
import json
import pytest
import tempfile
from unittest.mock import patch, mock_open
from config.settings import load_config, save_config, DEFAULT_CONFIG

class TestSettings:
    """Test suite for settings functionality"""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({"batch_size": 10, "mock_mode": True}, f)
            temp_file = f.name
            
        yield temp_file
        
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    def test_load_config_file_exists(self, temp_config_file):
        """Test loading configuration when file exists"""
        # Patch CONFIG_FILE to use our temp file
        with patch('config.settings.CONFIG_FILE', temp_config_file):
            config = load_config()
            
            # Config should contain values from file merged with defaults
            assert config["batch_size"] == 10
            assert config["mock_mode"] is True
            assert "api_timeout" in config  # From default config
    
    def test_load_config_file_not_exists(self):
        """Test loading configuration when file doesn't exist"""
        # Patch CONFIG_FILE to a non-existent file
        with patch('config.settings.CONFIG_FILE', 'nonexistent_file.json'):
            # Also patch save_config to avoid actually creating the file
            with patch('config.settings.save_config'):
                config = load_config()
                
                # Should return default config
                assert config == DEFAULT_CONFIG
    
    def test_load_config_invalid_json(self):
        """Test loading configuration with invalid JSON"""
        # Create mock for open that returns invalid JSON
        mock = mock_open(read_data="not valid json")
        
        # Patch both open and os.path.exists
        with patch('builtins.open', mock):
            with patch('os.path.exists', return_value=True):
                with patch('config.settings.save_config'):
                    config = load_config()
                    
                    # Should return default config when file is invalid
                    assert config == DEFAULT_CONFIG
    
    def test_save_config(self, temp_config_file):
        """Test saving configuration to file"""
        test_config = {"test_key": "test_value"}
        
        # Patch CONFIG_FILE to use our temp file
        with patch('config.settings.CONFIG_FILE', temp_config_file):
            result = save_config(test_config)
            
            # Check save was successful
            assert result is True
            
            # Verify file contains the correct data
            with open(temp_config_file, 'r') as f:
                saved_config = json.load(f)
                assert saved_config == test_config
    
    def test_save_config_error(self):
        """Test saving configuration with error"""
        # Patch open to raise an exception
        with patch('builtins.open', side_effect=Exception("Test error")):
            result = save_config({"test": "value"})
            
            # Save should return False on error
            assert result is False
