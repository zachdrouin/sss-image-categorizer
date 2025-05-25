"""
Integration tests for CSV processing functionality
"""

import os
import sys
import pytest
import pandas as pd
import tempfile
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.image_categorizer import process_csv_with_progress

class TestCSVProcessing:
    """Integration tests for CSV processing workflow"""
    
    @pytest.fixture
    def sample_csv_data(self):
        """Create sample CSV data for testing"""
        return pd.DataFrame({
            'Images': [
                'https://example.com/image1.jpg',
                'https://example.com/image2.jpg',
                'https://example.com/image3.jpg',
            ],
            'Description': [
                'Mountain landscape with blue sky',
                'Woman in her 30s with child',
                'Office desk with computer and plants',
            ],
            'Categories': [
                '',
                '',
                '',
            ]
        })
    
    @pytest.fixture
    def temp_csv_files(self, sample_csv_data):
        """Create temporary input and output CSV files"""
        # Create input file
        input_fd, input_path = tempfile.mkstemp(suffix='.csv')
        sample_csv_data.to_csv(input_path, index=False)
        os.close(input_fd)
        
        # Create output file path (but don't create the file)
        output_fd, output_path = tempfile.mkstemp(suffix='.csv')
        os.close(output_fd)
        os.unlink(output_path)  # Delete the file so process_csv can create it
        
        yield input_path, output_path
        
        # Clean up temporary files
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    @pytest.fixture
    def mock_analyze_func(self):
        """Create a mock for the analyze_image_with_gpt4v function"""
        mock_categories = {
            'https://example.com/image1.jpg': [
                'Category > Nature + Landscapes',
                'Colors > Blue',
                'ORIENTATION > Horizontal',
                'PEOPLE > No People'
            ],
            'https://example.com/image2.jpg': [
                'Category > Lifestyle',
                'PEOPLE > Any People',
                'PEOPLE > Any Age > 30s',
                'ORIENTATION > Vertical'
            ],
            'https://example.com/image3.jpg': [
                'Category > Workspace',
                'MOCKUPS > Computer',
                'Colors > Green',
                'PEOPLE > No People'
            ]
        }
        
        def mock_analyze(image_url):
            return mock_categories.get(image_url, [])
        
        return mock_analyze
    
    def test_process_csv_full(self, temp_csv_files, mock_analyze_func, monkeypatch):
        """Test processing a full CSV file"""
        input_path, output_path = temp_csv_files
        
        # Mock the analyze_image_with_gpt4v function
        monkeypatch.setattr('app.image_categorizer.analyze_image_with_gpt4v', mock_analyze_func)
        
        # Mock OpenAI client (not used but needs to be set)
        mock_client = MagicMock()
        monkeypatch.setattr('app.image_categorizer.client', mock_client)
        
        # Create a mock progress callback
        progress_updates = []
        def mock_progress_callback(current, total):
            progress_updates.append((current, total))
        
        # Process the CSV
        process_csv_with_progress(
            input_path, 
            output_path, 
            start_row=0, 
            batch_size=2,
            mock_mode=False,
            progress_callback=mock_progress_callback
        )
        
        # Check that the output file was created
        assert os.path.exists(output_path)
        
        # Load the output file and check the results
        result_df = pd.read_csv(output_path)
        
        # Check dimensions
        assert len(result_df) == 3
        
        # Check that categories were updated
        assert 'Category > Nature + Landscapes' in result_df.iloc[0]['Categories']
        assert 'PEOPLE > Any Age > 30s' in result_df.iloc[1]['Categories']
        assert 'Category > Workspace' in result_df.iloc[2]['Categories']
        
        # Check progress callback was called
        assert len(progress_updates) > 0
        assert progress_updates[-1][0] == 3  # Final count
        assert progress_updates[-1][1] == 3  # Total
    
    def test_process_csv_with_start_row(self, temp_csv_files, mock_analyze_func, monkeypatch):
        """Test processing a CSV file starting from a specific row"""
        input_path, output_path = temp_csv_files
        
        # Mock the analyze_image_with_gpt4v function
        monkeypatch.setattr('app.image_categorizer.analyze_image_with_gpt4v', mock_analyze_func)
        
        # Mock OpenAI client
        mock_client = MagicMock()
        monkeypatch.setattr('app.image_categorizer.client', mock_client)
        
        # Process the CSV starting from row 1
        process_csv_with_progress(
            input_path, 
            output_path, 
            start_row=1,  # Skip the first row
            batch_size=2,
            mock_mode=False
        )
        
        # Load the output file and check the results
        result_df = pd.read_csv(output_path)
        
        # The first row should not have categories (skipped)
        assert result_df.iloc[0]['Categories'] == ''
        
        # The other rows should have categories
        assert 'PEOPLE > Any Age > 30s' in result_df.iloc[1]['Categories']
        assert 'Category > Workspace' in result_df.iloc[2]['Categories']
    
    def test_process_csv_mock_mode(self, temp_csv_files, monkeypatch):
        """Test processing in mock mode"""
        input_path, output_path = temp_csv_files
        
        # Mock the mock_analyze_image function to return predictable results
        def mock_mock_analyze():
            return ['Category > Test', 'Colors > Test', 'ORIENTATION > Horizontal']
        
        monkeypatch.setattr('app.image_categorizer.mock_analyze_image', mock_mock_analyze)
        
        # Process in mock mode
        process_csv_with_progress(
            input_path, 
            output_path, 
            mock_mode=True
        )
        
        # Load the output file
        result_df = pd.read_csv(output_path)
        
        # All rows should have the same mock categories
        for i in range(3):
            assert 'Category > Test' in result_df.iloc[i]['Categories']
            assert 'Colors > Test' in result_df.iloc[i]['Categories']
