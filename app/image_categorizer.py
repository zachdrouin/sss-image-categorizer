import os
import pandas as pd
import requests
import logging
from openai import OpenAI
from io import BytesIO
import base64
import time
from typing import List, Set
import json
from pathlib import Path
import sys
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client - will be set in main function
client = None

# These will be set in main function
MOCK_MODE = False
STOP_PROCESSING = False

# Define all valid categories
VALID_CATEGORIES = {
    # Main Categories
    'Category > Workspace',
    'Category > Lifestyle',
    'Category > Parenting + Motherhood',
    'Category > Fall + Winter',
    'Category > Fashion + Beauty',
    'Category > Flowers + Greenery',
    'Category > Food + Beverage',
    'Category > Health + Fitness',
    'Category > Home + Interiors',
    'Category > Mockups',
    'Category > Nature + Landscapes',
    'Category > Holidays',
    'Category > Travel',
    'Category > Weddings + Celebrations',
    'Category > Self-Care + Wellness',
    'Category > Spring + Summer',
    
    # Colors
    'Colors > Black', 'Colors > Blue', 'Colors > Light Blue', 'Colors > Dark Blue',
    'Colors > Coral', 'Colors > Cream', 'Colors > Gold', 'Colors > Gray', 'Colors > Green',
    'Colors > Dark Green', 'Colors > Light Pink', 'Colors > Bright Pink', 'Colors > Rose Pink',
    'Colors > Orange', 'Colors > Peach', 'Colors > Purple', 'Colors > Red', 'Colors > Rose Gold',
    'Colors > Silver', 'Colors > Dark Brown', 'Colors > Tan', 'Colors > Turquoise', 'Colors > White',
    'Colors > Yellow',
    
    # Mockups
    'MOCKUPS > Computer', 'MOCKUPS > Frame', 'MOCKUPS > Mug', 'MOCKUPS > Other',
    'MOCKUPS > Phone', 'MOCKUPS > Stationery', 'MOCKUPS > Tablet',
    
    # Orientation
    'ORIENTATION > Horizontal', 'ORIENTATION > Vertical',
    
    # People
    'PEOPLE > No People', 'PEOPLE > Faceless', 'PEOPLE > Any Age',
    'PEOPLE > Any Age > < 20', 'PEOPLE > Any Age > 20s', 'PEOPLE > Any Age > 30s',
    'PEOPLE > Any Age > 40s', 'PEOPLE > Any Age > 50s', 'PEOPLE > Any Age > 60+',
    'PEOPLE > Any People', 'PEOPLE > Any People > 2 People', 'PEOPLE > Any People > 3+ People',
    'PEOPLE > Any Ethnicity', 'PEOPLE > Any Ethnicity > Asian',
    'PEOPLE > Any Ethnicity > Black / African American', 'PEOPLE > Any Ethnicity > Hispanic / Latina/o',
    'PEOPLE > Any Ethnicity > Indigenous / Native American', 'PEOPLE > Any Ethnicity > Multiracial',
    'PEOPLE > Any Ethnicity > White / Caucasian',
    
    # Copy Space
    'Copy Space > Large', 'Copy Space > Small'
}

def encode_image(image_url: str) -> str:
    """Download and encode image to base64"""
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        logger.error(f"Error downloading image {image_url}: {str(e)}")
        return None

def mock_analyze_image() -> List[str]:
    """Generate mock categories for testing without API key"""
    # Select random categories from each main type
    mock_categories = [
        random.choice([c for c in VALID_CATEGORIES if c.startswith('Category >')]),
        random.choice([c for c in VALID_CATEGORIES if c.startswith('Colors >')]),
        random.choice([c for c in VALID_CATEGORIES if c.startswith('ORIENTATION >')]),
        random.choice([c for c in VALID_CATEGORIES if c.startswith('PEOPLE >')])
    ]
    
    # Maybe add a mockup or copy space
    if random.random() > 0.7:
        mock_categories.append(random.choice([c for c in VALID_CATEGORIES if c.startswith('MOCKUPS >')]))
    if random.random() > 0.7:
        mock_categories.append(random.choice([c for c in VALID_CATEGORIES if c.startswith('Copy Space >')]))
    
    # Sleep to simulate API call
    time.sleep(0.5)
    return mock_categories

def analyze_image_with_gpt4v(image_url: str) -> List[str]:
    """Analyze image using GPT-4 Vision and return relevant categories"""
    base64_image = encode_image(image_url)
    if not base64_image:
        return []
    
    categories_list = sorted(VALID_CATEGORIES)
    
    # Create specialized category groups for better prompting
    people_categories = [cat for cat in categories_list if cat.startswith('PEOPLE >')]    
    ethnicity_categories = [cat for cat in people_categories if 'Ethnicity' in cat]
    age_categories = [cat for cat in people_categories if 'Age >' in cat and not cat.endswith('Any Age')]
    color_categories = [cat for cat in categories_list if cat.startswith('Colors >')]
    main_content_categories = [cat for cat in categories_list if cat.startswith('Category >')]
    
    prompt = f"""
    Analyze this image and return ONLY the relevant categories from the following list in a comma-separated format.
    Be thorough but only include categories that are clearly applicable.
    
    Instructions:
    1. Only return categories from the provided list
    2. Format as comma-separated values
    3. Be specific and precise in your analysis
    
    For CONTENT CATEGORIES, select the most relevant ones (can select multiple):
    {', '.join(main_content_categories)}
    
    For COLORS, identify the dominant colors (select 1-3 most prominent):
    {', '.join(color_categories)}
    
    For ORIENTATION, determine if the image is:
    ORIENTATION > Horizontal, ORIENTATION > Vertical
    
    For PEOPLE in the image, be specific about:
    - Ethnicity (if visible): {', '.join(ethnicity_categories)}
    - Age range (if possible): {', '.join(age_categories)}
    - Number of people: PEOPLE > Any People, PEOPLE > Any People > 2 People, PEOPLE > Any People > 3+ People
    - If no people are in the image: PEOPLE > No People
    - If people are shown without visible faces: PEOPLE > Faceless
    
    For MOCKUPS, identify if the image contains:
    MOCKUPS > Computer, MOCKUPS > Frame, MOCKUPS > Mug, MOCKUPS > Other, MOCKUPS > Phone, MOCKUPS > Stationery, MOCKUPS > Tablet
    
    For COPY SPACE, determine if the image has:
    Copy Space > Large, Copy Space > Small
    
    Available Categories:
    {', '.join(categories_list)}
    """
    
    try:
        # If in mock mode, use mock analysis
        if MOCK_MODE:
            logger.info(f"MOCK MODE: Generating mock categories for {image_url}")
            return mock_analyze_image()
            
        # Real API call
        response = client.chat.completions.create(
            model="gpt-4o",  # Current vision-capable model as of May 2024
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"  # Higher detail for better analysis
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1,  # Lower temperature for more consistent results
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        # Parse response and validate categories
        response_text = response.choices[0].message.content
        categories = [c.strip() for c in response_text.split(',')]
        valid_categories = [c for c in categories if c in VALID_CATEGORIES]
        
        # Ensure we have at least one of each main category type
        main_categories = {
            'Category >': False,
            'Colors >': False,
            'ORIENTATION >': False,
            'PEOPLE >': False,
            'MOCKUPS >': False,
            'Copy Space >': False
        }
        
        # First pass: Add all specific categories
        final_categories = []
        for cat in valid_categories:
            # Check if this is a parent category and we already have a more specific child category
            # For example, don't add 'PEOPLE > Any Age' if we already have 'PEOPLE > Any Age > 30s'
            if cat.endswith('Any Age') and any(c.startswith(cat + ' >') for c in valid_categories):
                continue
            if cat.endswith('Any People') and any(c.startswith(cat + ' >') for c in valid_categories):
                continue
            if cat.endswith('Any Ethnicity') and any(c.startswith(cat + ' >') for c in valid_categories):
                continue
                
            # Otherwise add the category
            final_categories.append(cat)
            
            # Mark the main category type as covered
            for prefix in main_categories.keys():
                if cat.startswith(prefix):
                    main_categories[prefix] = True
                    break
        
        # Ensure we have at least one main category
        if not main_categories['Category >']:
            final_categories.append('Category > Lifestyle')  # Default fallback
            
        # Ensure we have orientation
        if not main_categories['ORIENTATION >']:
            # Try to determine from image dimensions if possible
            # For now, default to horizontal as most common
            final_categories.append('ORIENTATION > Horizontal')
            
        # Ensure we have at least one color
        if not main_categories['Colors >']:
            # Default to a neutral color if none detected
            final_categories.append('Colors > White')
        
        return list(dict.fromkeys(final_categories))  # Remove duplicates while preserving order
        
    except Exception as e:
        logger.error(f"Error analyzing image {image_url}: {str(e)}")
        return []

def post_process_people_categories(categories: List[str], description: str = None) -> List[str]:
    """
    Post-process people categories to ensure we have appropriate specific categories
    based on the image analysis and description
    """
    # Check if we already have people categories
    has_people = any(cat.startswith('PEOPLE >') for cat in categories)
    has_ethnicity = any('Ethnicity >' in cat for cat in categories)
    has_age = any('Age >' in cat and not cat.endswith('Any Age') for cat in categories)
    has_people_count = any(cat in ['PEOPLE > Any People > 2 People', 'PEOPLE > Any People > 3+ People'] for cat in categories)
    
    # If we have people but no ethnicity, try to infer from description
    if has_people and not has_ethnicity and description:
        description = description.lower()
        if 'asian' in description:
            categories.append('PEOPLE > Any Ethnicity > Asian')
        elif 'black' in description or 'african' in description:
            categories.append('PEOPLE > Any Ethnicity > Black / African American')
        elif 'hispanic' in description or 'latina' in description or 'latino' in description:
            categories.append('PEOPLE > Any Ethnicity > Hispanic / Latina/o')
        elif 'indigenous' in description or 'native american' in description:
            categories.append('PEOPLE > Any Ethnicity > Indigenous / Native American')
        elif 'white' in description or 'caucasian' in description:
            categories.append('PEOPLE > Any Ethnicity > White / Caucasian')
        else:
            # Default to generic ethnicity if we can't determine
            categories.append('PEOPLE > Any Ethnicity')
    
    # If we have people but no age range, try to infer from description
    if has_people and not has_age and description:
        description = description.lower()
        if 'child' in description or 'kid' in description or 'young' in description or 'teen' in description:
            categories.append('PEOPLE > Any Age > < 20')
        elif '20s' in description or 'twenties' in description or 'young adult' in description:
            categories.append('PEOPLE > Any Age > 20s')
        elif '30s' in description or 'thirties' in description:
            categories.append('PEOPLE > Any Age > 30s')
        elif '40s' in description or 'forties' in description:
            categories.append('PEOPLE > Any Age > 40s')
        elif '50s' in description or 'fifties' in description:
            categories.append('PEOPLE > Any Age > 50s')
        elif '60' in description or 'sixties' in description or 'senior' in description or 'elderly' in description:
            categories.append('PEOPLE > Any Age > 60+')
        else:
            # If we can't determine, add the generic age category
            categories.append('PEOPLE > Any Age')
    
    # If we have people but no count, default to single person
    if has_people and not has_people_count and 'PEOPLE > No People' not in categories:
        # Check description for multiple people
        if description and ('people' in description.lower() or 'persons' in description.lower() or 'group' in description.lower()):
            if 'three' in description.lower() or 'multiple' in description.lower() or 'group' in description.lower():
                categories.append('PEOPLE > Any People > 3+ People')
            elif 'two' in description.lower() or 'couple' in description.lower() or 'pair' in description.lower():
                categories.append('PEOPLE > Any People > 2 People')
            else:
                categories.append('PEOPLE > Any People')
        else:
            categories.append('PEOPLE > Any People')
    
    return list(dict.fromkeys(categories))  # Remove duplicates while preserving order

def process_csv_with_progress(input_file: str, output_file: str, start_row: int = 0, batch_size: int = 5, 
                             api_key: str = None, mock_mode: bool = False, progress_callback=None):
    """
    Process the CSV file with progress tracking
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        start_row: Row to start processing from (0-based)
        batch_size: Number of images to process in a batch
        api_key: OpenAI API key (optional, will use env var if not provided)
        mock_mode: If True, use mock mode without API calls
        progress_callback: Optional callback function(current, total) for progress updates
    """
    global STOP_PROCESSING, MOCK_MODE, client
    
    # Reset stop flag
    STOP_PROCESSING = False
    
    try:
        # Read CSV
        df = pd.read_csv(input_file)
        total_rows = len(df)
        rows_to_process = sum(pd.isna(row.get('Categories', '')) and pd.notna(row.get('Images', '')) 
                              for _, row in df.iloc[start_row:].iterrows())
        
        # Configure mock mode and API key
        MOCK_MODE = mock_mode
        if not mock_mode and api_key:
            client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized with provided API key")
        elif not mock_mode:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("No OpenAI API key provided. Use --api-key or set OPENAI_API_KEY environment variable.")
            client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized with environment API key")
        else:
            logger.info("Running in MOCK MODE - no API calls will be made")
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize progress counter
        processed_count = 0
        
        # Process rows in batches
        for i in range(start_row, total_rows, batch_size):
            if STOP_PROCESSING:
                logger.info("Processing stopped by user")
                break
                
            batch = df.iloc[i:i + batch_size]
            logger.info(f"Processing rows {i+1} to {min(i+batch_size, total_rows)} of {total_rows}")
            
            for idx, row in batch.iterrows():
                if STOP_PROCESSING:
                    break
                    
                if pd.isna(row.get('Categories', '')) and pd.notna(row.get('Images', '')):
                    try:
                        logger.info(f"Analyzing image {idx+1}: {row['Images']}")
                        categories = analyze_image_with_gpt4v(row['Images'])
                        
                        # Post-process people categories using description if available
                        description = row.get('Description', '')
                        if categories and pd.notna(description):
                            categories = post_process_people_categories(categories, description)
                        
                        if categories:
                            df.at[idx, 'Categories'] = ', '.join(categories)
                            logger.info(f"Updated categories: {categories}")
                        
                        # Update progress
                        processed_count += 1
                        if progress_callback:
                            progress_callback(processed_count, rows_to_process)
                            
                        # Save progress after each image
                        df.to_csv(output_file, index=False)
                        logger.info(f"Progress saved to {output_file}")
                        
                        # Rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error processing row {idx+1}: {str(e)}")
                        continue
            
            # Save batch progress
            df.to_csv(output_file, index=False)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
    finally:
        # Final save
        if 'df' in locals():
            df.to_csv(output_file, index=False)
            logger.info(f"Final results saved to {output_file}")

def main():
    """Main function to parse arguments and run the script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process images and update categories in WooCommerce CSV')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--batch-size', type=int, default=5, help='Number of images to process in a batch')
    parser.add_argument('--start-row', type=int, default=0, help='Row number to start processing from (0-based)')
    parser.add_argument('--api-key', help='OpenAI API key (overrides environment variable)')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode without making API calls')
    
    args = parser.parse_args()
    
    # Set up API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    
    # Configure mock mode and client
    global MOCK_MODE, client
    
    if args.mock:
        MOCK_MODE = True
        logger.info("Running in MOCK MODE - no API calls will be made")
    elif not api_key:
        logger.error("Error: No OpenAI API key provided. Use --api-key or set OPENAI_API_KEY environment variable.")
        logger.info("Alternatively, use --mock to run in mock mode without an API key.")
        sys.exit(1)
    else:
        # Initialize the OpenAI client with the API key
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized with API key")
    
    # Process the CSV file
    logger.info("Starting image category processing...")
    process_csv_with_progress(args.input, args.output, args.start_row, args.batch_size)
    logger.info("Processing completed!")

if __name__ == "__main__":
    main()