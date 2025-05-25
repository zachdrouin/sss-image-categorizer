# Image Categorizer

A user-friendly tool for categorizing images using OpenAI's GPT-4 Vision API. Perfect for non-technical users who need to categorize images for WooCommerce import.

## Features

- Automatically analyze images using AI to assign appropriate categories
- Web-based interface for easy use by non-technical users
- Bulk categorization support for multiple images
- Apply common categories to all images at once
- Resume interrupted processing
- CSV import and export compatible with WooCommerce

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd image-categorizer
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

## Usage

### Web Interface (Recommended for non-technical users)

To start the web interface:

```
python app/web_categorizer.py
```

This will open a browser window with the application interface. From there, you can:
1. Provide your OpenAI API key
2. Select your input CSV file
3. Choose where to save the output file
4. Configure processing options
5. Start the categorization process

### Command Line Interface

For advanced users who prefer the command line:

```
python app/image_categorizer.py --input your_input.csv --output your_output.csv [options]
```

Options:
- `--batch-size N`: Number of images to process in each batch (default: 5)
- `--start-row N`: Row to start processing from (useful for resuming) (default: 0)
- `--api-key KEY`: Your OpenAI API key (can also be set as OPENAI_API_KEY environment variable)
- `--mock`: Run in mock mode without making API calls (for testing)

## Category Reference

The categorizer supports the following category groups:

### Main Categories
- Workspace, Lifestyle, Parenting + Motherhood, Fall + Winter
- Fashion + Beauty, Flowers + Greenery, Food + Beverage
- Health + Fitness, Home + Interiors, Mockups
- Nature + Landscapes, Holidays, Travel
- Weddings + Celebrations, Self-Care + Wellness, Spring + Summer

### Colors
Black, Blue, Light Blue, Dark Blue, Coral, Cream, Gold, Gray, Green,
Dark Green, Light Pink, Bright Pink, Rose Pink, Orange, Peach,
Purple, Red, Rose Gold, Silver, Dark Brown, Tan, Turquoise, White, Yellow

### People Categories
- No People, Faceless
- Age groups: <20, 20s, 30s, 40s, 50s, 60+
- Group size: Single, 2 People, 3+ People
- Ethnicity: Asian, Black/African American, Hispanic/Latina/o, Indigenous/Native American, Multiracial, White/Caucasian

### Technical Categories
- Orientation: Horizontal, Vertical
- Mockups: Computer, Frame, Mug, Phone, Stationery, Tablet, Other
- Copy Space: Large, Small

## Bulk Category Application

The web interface allows you to select categories to apply to all images in your CSV. This is useful for:
- Adding common categories (like your brand style)
- Applying seasonal categories to entire collections
- Setting technical aspects that apply to all images (orientation, copy space)

## Development

### Project Structure

```
image-categorizer/
├── app/                    # Application code
│   ├── image_categorizer.py  # CLI application
│   ├── web_categorizer.py    # Web interface
│   ├── static/               # CSS, JS files
│   └── templates/            # HTML templates
├── config/                 # Configuration
│   ├── settings.py           # Global settings
│   ├── category_manager.py   # Category handling
│   └── categories.json       # Category definitions
├── tests/                  # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test data
├── data/                   # Sample data directory
├── venv/                   # Virtual environment
├── requirements.txt        # Dependencies
├── pytest.ini              # Test configuration
└── run_tests.py            # Test runner
```

### Running Tests

To run the test suite:

```
./run_tests.py
```

For specific test groups:

```
./run_tests.py tests/unit        # Run only unit tests
./run_tests.py tests/integration  # Run only integration tests
```

### Extending Categories

To add or modify categories, edit the `config/categories.json` file. Changes will be automatically loaded the next time you run the application.

## Troubleshooting

### API Key Issues
- Ensure your OpenAI API key has access to the GPT-4 Vision API
- Check that your account has sufficient credits

### CSV Format
- The input CSV must have an 'Images' column with image URLs
- Optionally include a 'Description' column for better categorization
- The 'Categories' column will be created or updated by the tool

### Performance Tips
- Process in smaller batches to avoid timeouts
- Use the resume feature for large datasets
- For very large datasets, consider running overnight

## Requirements

- Python 3.8+
- OpenAI API key with GPT-4 Vision access
- Internet connection for API calls and image access
