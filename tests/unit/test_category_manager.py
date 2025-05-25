"""
Unit tests for category manager module
"""

import os
import json
import pytest
import tempfile
from config.category_manager import CategoryManager

class TestCategoryManager:
    """Test suite for CategoryManager class"""
    
    @pytest.fixture
    def sample_categories(self):
        """Create sample categories for testing"""
        return {
            "main_categories": ["Category > Test1", "Category > Test2"],
            "colors": ["Colors > Red", "Colors > Blue"],
            "mockups": ["MOCKUPS > Test"]
        }
    
    @pytest.fixture
    def temp_categories_file(self, sample_categories):
        """Create a temporary categories file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(sample_categories, f)
            temp_file = f.name
            
        yield temp_file
        
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    def test_load_categories(self, temp_categories_file, sample_categories):
        """Test loading categories from file"""
        # Create instance with the temp file
        manager = CategoryManager(temp_categories_file)
        
        # Check if categories were loaded correctly
        assert len(manager.valid_categories) == 5  # Total number of categories
        assert len(manager.categories_by_group) == 3  # Number of category groups
        
        # Check specific categories
        assert "Category > Test1" in manager.valid_categories
        assert "Colors > Blue" in manager.valid_categories
        
        # Check category groups
        assert "main_categories" in manager.categories_by_group
        assert len(manager.categories_by_group["colors"]) == 2
    
    def test_validate_category(self, temp_categories_file):
        """Test category validation"""
        manager = CategoryManager(temp_categories_file)
        
        # Valid category
        assert manager.validate_category("Category > Test1") is True
        
        # Invalid category
        assert manager.validate_category("Invalid > Category") is False
    
    def test_validate_categories(self, temp_categories_file):
        """Test validating multiple categories"""
        manager = CategoryManager(temp_categories_file)
        
        # Mix of valid and invalid categories
        categories = ["Category > Test1", "Invalid > Category", "Colors > Blue"]
        valid_categories = manager.validate_categories(categories)
        
        # Should return only valid categories
        assert len(valid_categories) == 2
        assert "Category > Test1" in valid_categories
        assert "Colors > Blue" in valid_categories
        assert "Invalid > Category" not in valid_categories
    
    def test_get_categories_in_group(self, temp_categories_file):
        """Test retrieving categories by group"""
        manager = CategoryManager(temp_categories_file)
        
        # Get categories for a specific group
        colors = manager.get_categories_in_group("colors")
        assert len(colors) == 2
        assert "Colors > Red" in colors
        assert "Colors > Blue" in colors
        
        # Non-existent group
        assert manager.get_categories_in_group("nonexistent") == []
    
    def test_missing_file(self):
        """Test behavior with missing file"""
        # Non-existent file
        manager = CategoryManager("nonexistent_file.json")
        
        # Should initialize with empty sets
        assert len(manager.valid_categories) == 0
        assert isinstance(manager.categories_by_group, dict)
