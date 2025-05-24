# Image Categorizer

A powerful AI-driven tool to automatically categorize your images using OpenAI's GPT-4 Vision API.

## Getting Started

### Installation

No installation required! Just double-click the `ImageCategorizer.command` file to start the application.

### First Time Setup

1. **API Key**: The first time you run the application, you'll need to set up your OpenAI API key.
   - You can get an API key from [OpenAI's website](https://platform.openai.com/api-keys)
   - Enter your API key in the Settings page

2. **Sample Data**: Use the "Get Sample CSV" button on the welcome page to create a sample CSV file with image URLs.

## How to Use

### Step 1: Prepare Your CSV File

Your CSV file should contain a column with image URLs. The application will analyze these images and categorize them automatically.

**Required columns:**
- A column containing image URLs (can be named anything like "Images", "image_url", etc.)

**Optional columns:**
- `Description`: Text descriptions that help improve categorization accuracy
- Any other data you want to preserve

### Step 2: Select Categories to Apply to All Images (Optional)

Before processing, you can select common categories that apply to most of your images. This feature:
- **Saves time**: Apply bulk categories instantly without AI processing
- **Ensures consistency**: Guarantees certain categories are applied to all images
- **Reduces API costs**: Less reliance on AI for obvious categories

**Available Category Groups:**

#### Main Categories
- Workspace, Lifestyle, Parenting + Motherhood
- Fall + Winter, Spring + Summer
- Fashion + Beauty, Flowers + Greenery
- Food + Beverage, Health + Fitness
- Home + Interiors, Nature + Landscapes
- Holidays, Travel, Weddings + Celebrations
- Self-Care + Wellness, Mockups

#### Colors
- All major colors: Black, Blue, Brown, Gold, Gray, Green, Orange, Peach, Purple, Red, Rose Gold, Silver, Dark Brown, Tan, Turquoise, White, Yellow

#### People Categories
- **Presence**: No People, Faceless, Any People
- **Count**: 2 People, 3+ People
- **Age Groups**: <20, 20s, 30s, 40s, 50s, 60+
- **Ethnicity**: Asian, Black/African American, Hispanic/Latino, Indigenous/Native American, Multiracial, White/Caucasian

#### Technical Categories
- **Orientation**: Horizontal, Vertical
- **Mockups**: Computer, Frame, Mug, Phone, Stationery, Tablet, Other
- **Copy Space**: Large, Small

### Step 3: Process Images

1. **Select Input File**: Click "Browse" to select your CSV file
2. **Choose Output Location**: Specify where to save the categorized results
3. **Configure Settings**:
   - **Batch Size**: Number of images to process at once (default: 5)
   - **Start Row**: Resume processing from a specific row if interrupted
   - **Mock Mode**: Test the interface without making API calls
4. **Start Processing**: Click "Start Processing" to begin AI categorization

### Step 4: Monitor Progress

- Real-time progress updates show current status
- Processing can be stopped and resumed at any time
- Results are saved incrementally to prevent data loss

### Step 5: View Results

Your output CSV file will contain:
- All original data from your input file
- New `Categories` column with AI-generated categories
- Categories are stored as comma-separated values for easy filtering

## Advanced Features

### Bulk Category Application

Use the "Apply Categories to All" feature to:
1. Select multiple categories from organized groups
2. Apply them instantly to all images in your CSV
3. Combine with AI processing for comprehensive categorization

### Smart Category Processing

The AI system:
- **Analyzes visual content** using GPT-4 Vision
- **Considers descriptions** when available for better accuracy
- **Avoids duplicates** when combining bulk and AI categories
- **Uses hierarchical categories** for precise classification

### Resume Processing

If processing is interrupted:
1. Note the last processed row number
2. Enter it in the "Start Row" field
3. Resume processing from that point

## Tips for Best Results

### CSV File Preparation
- **Use high-quality image URLs** that are publicly accessible
- **Include descriptions** when possible for better categorization
- **Ensure URLs are valid** and images load properly

### Category Selection Strategy
- **Apply obvious categories first** using bulk selection
- **Use specific categories** rather than general ones when possible
- **Consider your end use** - select categories that match your workflow

### Processing Optimization
- **Start with small batches** (5-10 images) to test
- **Use mock mode** to familiarize yourself with the interface
- **Monitor API usage** to manage costs effectively
- **Process during off-peak hours** for faster response times

### Error Prevention
- **Save your work frequently** - results are auto-saved after each image
- **Keep backup copies** of your original CSV files
- **Test with sample data** before processing large datasets

## Troubleshooting

### Common Issues
- **API Key Errors**: Verify your OpenAI API key is valid and has sufficient credits
- **Image Loading Failures**: Check that image URLs are accessible and properly formatted
- **Processing Interruptions**: Use the "Start Row" feature to resume from where you left off

### Performance Tips
- **Reduce batch size** if experiencing timeouts
- **Check internet connection** for stable processing
- **Close other applications** to free up system resources

## Technical Details

### Supported Formats
- **Input**: CSV files with image URLs
- **Images**: Any format supported by web browsers (JPG, PNG, GIF, etc.)
- **Output**: CSV files with added categorization data

### API Requirements
- OpenAI API key with GPT-4 Vision access
- Stable internet connection
- Sufficient API credits for your image volume

## Need Help?

If you encounter any issues or need assistance:
1. Check the application logs for detailed error messages
2. Verify your API key and internet connection
3. Try processing a smaller batch to isolate issues
4. Contact support with specific error details

Happy categorizing! 🎯📸
