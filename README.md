# Image Categorizer

A tool for automatically categorizing images for Styled Stock Society using OpenAI's GPT-4 Vision API. This application helps the Styled Stock Society Team quickly add relevant categories to product images for import into WooCommerce.

Builds a standalone MacOS application that Elle can use locally without complicated installs. 

Created with curiousity (and windsurf) in a weekend 

:)

## Features

- Analyze images with AI to automatically suggest appropriate categories
- Manually select categories to apply to all images
- Smart integration of manual and AI categorization
- Automatic image orientation detection based on actual dimensions
- Intelligent people category handling with conflict resolution
- Process images in batches to optimize API usage
- Export categorized images as a CSV file ready for import
- User-friendly web interface with progress tracking

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/image-categorizer.git
cd image-categorizer
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Obtain an API key from OpenAI (https://platform.openai.com/api-keys)
2. Enter your API key in the settings page
3. Upload a CSV file with image URLs in the 'Images' column
4. Select categories manually or use AI analysis
5. Process the images and download the results

## Category Reference

The Image Categorizer uses a comprehensive set of categories organized into groups:

### Main Categories
- Beauty + Fashion, Business, DIY + Crafts, Education
- Food + Drink, Flatlays, Graphics + Textures
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

## User-Friendly Guide for Image Categorization

This guide is simple and step-by-step for beginners. It explains how the app categorizes images when you select categories yourself versus when it uses AI only.

### How Categorization Works
- **When You Select Categories Manually:**
  - You choose categories (like "Nature + Landscapes" or "Colors > Blue") from a list. The app applies these directly to your images without AI help. It's fast and gives you full control, like picking tags yourself for accuracy.

- **When Using AI Only:**
  - The app uses smart AI (powered by OpenAI) to analyze the image and suggest categories based on what it sees (e.g., colors, people, or scene type). It's like having an automatic helper that guesses tags, but you can review and change them if needed.

- **When Using Both Manual Selection and AI (SMART COMBINED Approach):**
  - This powerful combination gives you the best results! You select important categories you know should apply, and the AI fills in the rest while respecting your choices.
  - **Intelligent People Detection:** The AI will override all people-related categories if it detects no people in the image, ensuring accurate tagging.
  - **Automatic Orientation Detection:** The system analyzes actual image dimensions to determine if an image is horizontal or vertical, eliminating guesswork.
  - **Smart Category Harmonization:** For content and colors, both your selections and AI suggestions are combined for comprehensive tagging.
  - **Mockup and Copy Space Prioritization:** Your manual selections for mockups and copy space take priority over AI suggestions.
  - This smart integration ensures consistency while leveraging AI's ability to detect details you might miss.

### Step-by-Step Instructions for Using the App
1. **Upload Your Photos:** Go to the home page, click "Upload", and select your image files or CSV with photo links.
2. **Choose Your Mode:**
   - For manual control, select categories from the dropdowns before starting.
   - For AI help, just click "Analyze with AI" to let it do the work.
   - For the best results, select some key categories AND use AI analysis together.
3. **Review and Save:** See the suggested or applied categories, make changes if you want, then save to a file for WooCommerce import.
4. **Reset if Needed:** Use the reset button to clear everything and start fresh without losing your settings.

### Tips for Best Results
- Start with a few photos to test the system
- For product collections, manually select common categories (like your brand style or season)
- Let the AI handle specific details like colors and technical aspects
- If your images contain people, manually select ethnicity and age range for consistency
- **People Categories:** The system will automatically remove all people categories if no people are detected in an image
- **Orientation Detection:** The system automatically determines if an image is horizontal or vertical based on its dimensions
- **Combined Approach:** Use the "SMART COMBINED Approach" checkbox in the Processing Options for the best results
- **Detailed Logs:** Check the application logs for insights into how categories are being applied
- Use the reset button if you want to start over without losing your API key

## Technical Details

### Smart Categorization Logic

#### Automatic Orientation Detection
The application uses the Python Imaging Library (PIL) to analyze the actual dimensions of each image:
```python
def determine_orientation(image_content):
    # Open the image using PIL
    img = Image.open(BytesIO(image_content))
    width, height = img.size
    
    # Determine orientation based on aspect ratio
    if width >= height:
        return "ORIENTATION > Horizontal"
    else:
        return "ORIENTATION > Vertical"
```

#### Intelligent People Category Handling
When the AI detects no people in an image, the system ensures only the "No People" category is applied:
```python
# If AI says no people, respect that regardless of manual selection
if ai_no_people:
    # Add only the 'No People' category and remove any other people categories
    result_categories.add('PEOPLE > No People')
    # Remove any other people categories that might have been manually selected
    result_categories = {cat for cat in result_categories 
                        if not (cat.startswith('PEOPLE >') and cat != 'PEOPLE > No People')}
```

## Development

### Project Structure
```
image-categorizer/
├── app/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   ├── image_categorizer.py  # Core image analysis logic
│   └── web_categorizer.py    # Flask web application
├── config/
│   ├── categories.json       # Category definitions
│   ├── category_manager.py   # Category management
│   └── settings.py           # Application settings
├── tests/
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── requirements.txt          # Python dependencies
└── run.py                    # Application entry point
```

### Testing
Run the tests with:
```bash
python run_tests.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for the GPT-4 Vision API
- Style Stock Society and Elle Drouin for the application concept and design
- Windsurf&co for development
