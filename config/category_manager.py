"""
Category management for the Image Categorizer application.
Handles loading, validating, and accessing categories from external configuration.
"""

import os
import json
import logging
from typing import List, Set, Dict, Optional

logger = logging.getLogger(__name__)

# Path to the categories JSON file
CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), 'categories.json')

class CategoryManager:
    """Manages categories for image classification"""
    
    def __init__(self, categories_file: str = CATEGORIES_FILE):
        self.categories_file = categories_file
        self.categories_by_group: Dict[str, List[str]] = {}
        self.valid_categories: Set[str] = set()
        self._load_categories()
    
    def _load_categories(self) -> None:
        """Load categories from JSON file"""
        try:
            if not os.path.exists(self.categories_file):
                logger.error(f"Categories file not found: {self.categories_file}")
                return
                
            with open(self.categories_file, 'r') as f:
                self.categories_by_group = json.load(f)
                
            # Create a flat set of all valid categories
            self.valid_categories = set()
            for category_group in self.categories_by_group.values():
                self.valid_categories.update(category_group)
                
            logger.info(f"Loaded {len(self.valid_categories)} categories from {self.categories_file}")
            
        except Exception as e:
            logger.error(f"Error loading categories: {str(e)}")
            # Initialize with empty set as fallback
            self.valid_categories = set()
    
    def get_all_categories(self) -> Set[str]:
        """Get the set of all valid categories"""
        return self.valid_categories
    
    def get_categories_by_group(self) -> Dict[str, List[str]]:
        """Get categories organized by their groups"""
        return self.categories_by_group
    
    def validate_category(self, category: str) -> bool:
        """Check if a category is valid"""
        return category in self.valid_categories
    
    def validate_categories(self, categories: List[str]) -> List[str]:
        """Filter list to only include valid categories"""
        return [cat for cat in categories if self.validate_category(cat)]
    
    def get_category_groups(self) -> List[str]:
        """Get list of available category groups"""
        return list(self.categories_by_group.keys())
    
    def get_categories_in_group(self, group: str) -> List[str]:
        """Get categories belonging to a specific group"""
        return self.categories_by_group.get(group, [])

# Singleton instance for easy import
category_manager = CategoryManager()
