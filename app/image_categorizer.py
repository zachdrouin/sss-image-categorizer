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
from PIL import Image

# Import from configuration module
from config.settings import setup_logging
from config.category_manager import category_manager

# Configure logging
logger = setup_logging(__name__)

# Initialize OpenAI client - will be set in main function
client = None

# These will be set in main function
MOCK_MODE = False
STOP_PROCESSING = False

# Get valid categories from the category manager
VALID_CATEGORIES = category_manager.get_all_categories()

def encode_image(image_url: str) -> tuple:
    """Download and encode image to base64, also return the raw content for dimension analysis"""
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8'), response.content
    except Exception as e:
        logger.error(f"Error downloading image {image_url}: {str(e)}")
        return None, None

def determine_orientation(image_content: bytes) -> str:
    """Determine image orientation based on actual dimensions"""
    if not image_content:
        # Default to horizontal if we can't determine
        return "ORIENTATION > Horizontal"
    
    try:
        # Open the image using PIL
        img = Image.open(BytesIO(image_content))
        width, height = img.size
        
        # Determine orientation based on aspect ratio
        if width >= height:
            return "ORIENTATION > Horizontal"
        else:
            return "ORIENTATION > Vertical"
    except Exception as e:
        logger.error(f"Error determining image orientation: {str(e)}")
        # Default to horizontal if there's an error
        return "ORIENTATION > Horizontal"

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

def analyze_image_with_gpt4v(image_url: str, selected_categories: List[str] = None) -> List[str]:
    """Analyze image using GPT-4 Vision and return relevant categories"""
    base64_image, image_content = encode_image(image_url)
    if not base64_image:
        return []
        
    # Determine orientation based on actual image dimensions
    orientation_category = determine_orientation(image_content)
    logger.info(f"Determined orientation for {image_url}: {orientation_category}")
    
    categories_list = sorted(VALID_CATEGORIES)
    
    # Create specialized category groups for better prompting
    people_categories = [cat for cat in categories_list if cat.startswith('PEOPLE >')]    
    ethnicity_categories = [cat for cat in people_categories if 'Ethnicity' in cat]
    age_categories = [cat for cat in people_categories if 'Age >' in cat and not cat.endswith('Any Age')]
    color_categories = [cat for cat in categories_list if cat.startswith('Colors >')]
    main_content_categories = [cat for cat in categories_list if cat.startswith('Category >')]
    
    # Process selected categories if provided
    selected_constraints = ""
    if selected_categories and len(selected_categories) > 0:
        # Extract selected categories by type
        selected_main = [c for c in selected_categories if c.startswith('Category >') and c in main_content_categories]
        selected_colors = [c for c in selected_categories if c.startswith('Colors >') and c in color_categories]
        selected_people = [c for c in selected_categories if c.startswith('PEOPLE >') and c in people_categories]
        selected_ethnicity = [c for c in selected_people if 'Ethnicity >' in c]
        selected_age = [c for c in selected_people if 'Age >' in c and not c.endswith('Any Age')]
        
        # For orientation, we'll use our determined value instead of any selected value
        # But we'll keep track of any manual selection for reference
        selected_orientation = [c for c in selected_categories if c.startswith('ORIENTATION >')]
        if selected_orientation:
            logger.info(f"Overriding manually selected orientation {selected_orientation[0]} with detected orientation {orientation_category}")
        
        selected_mockups = [c for c in selected_categories if c.startswith('MOCKUPS >')]
        selected_copy_space = [c for c in selected_categories if c.startswith('Copy Space >')]
        
        # Build constraints for the prompt
        constraints = []
        if selected_main:
            constraints.append(f"Content categories should include or be compatible with: {', '.join(selected_main)}")
        if selected_colors:
            constraints.append(f"Colors should include: {', '.join(selected_colors)}")
        
        # Tell the AI to use our detected orientation instead of guessing
        constraints.append(f"Use exactly this orientation: {orientation_category}")
        
        if selected_mockups:
            constraints.append(f"Mockup types should include: {', '.join(selected_mockups)}")
        if selected_copy_space:
            constraints.append(f"Copy space should be: {', '.join(selected_copy_space)}")
        
        # Special handling for people categories
        if 'PEOPLE > No People' in selected_people:
            constraints.append("If there are NO people in the image, confirm 'PEOPLE > No People' category. If any people are visible, ignore this constraint.")
        elif selected_people:
            people_constraints = []
            if selected_ethnicity:
                people_constraints.append(f"Ethnicity should be one of: {', '.join(selected_ethnicity)}")
            if selected_age:
                people_constraints.append(f"Age range should be one of: {', '.join(selected_age)}")
            if people_constraints:
                constraints.append("For people in the image: " + "; ".join(people_constraints))
        
        if constraints:
            selected_constraints = "\nIMPORTANT CONSTRAINTS:\n" + "\n".join([f"- {c}" for c in constraints]) + "\n"
    
    prompt = f"""
    Analyze this image and return ONLY the relevant categories from the following list in a comma-separated format.
    Be thorough but only include categories that are clearly applicable.
    
    Instructions:
    1. Only return categories from the provided list
    2. Format as comma-separated values
    3. Be specific and precise in your analysis
    4. If there are NO people in the image, do not include any people-related categories except 'PEOPLE > No People'{selected_constraints}
    
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
        
        # If we have selected categories, harmonize with AI results
        if selected_categories and len(selected_categories) > 0:
            # Add our detected orientation to the valid categories
            if orientation_category not in valid_categories:
                valid_categories.append(orientation_category)
                
            valid_categories = harmonize_categories(valid_categories, selected_categories)
            
        # Make sure our detected orientation is in the final categories
        if orientation_category not in valid_categories:
            valid_categories.append(orientation_category)
        
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

def harmonize_categories(ai_categories: List[str], selected_categories: List[str]) -> List[str]:
    """
    Harmonize AI-generated categories with manually selected categories to ensure consistency
    and resolve conflicts according to these rules:
    1. If AI detects no people but people categories were selected, respect AI's detection
    2. For orientation, mockups, and copy space, prefer manually selected categories
    3. For content and colors, combine both sets
    4. For people subcategories (age, ethnicity), use manually selected if provided
    """
    result_categories = set()
    
    # Check if AI detected no people
    ai_no_people = 'PEOPLE > No People' in ai_categories
    
    # Extract categories by type
    ai_main = [c for c in ai_categories if c.startswith('Category >')]
    ai_colors = [c for c in ai_categories if c.startswith('Colors >')]
    ai_orientation = [c for c in ai_categories if c.startswith('ORIENTATION >')]
    ai_mockups = [c for c in ai_categories if c.startswith('MOCKUPS >')]
    ai_copy_space = [c for c in ai_categories if c.startswith('Copy Space >')]
    ai_people = [c for c in ai_categories if c.startswith('PEOPLE >')]
    
    selected_main = [c for c in selected_categories if c.startswith('Category >')]
    selected_colors = [c for c in selected_categories if c.startswith('Colors >')]
    selected_orientation = [c for c in selected_categories if c.startswith('ORIENTATION >')]
    selected_mockups = [c for c in selected_categories if c.startswith('MOCKUPS >')]
    selected_copy_space = [c for c in selected_categories if c.startswith('Copy Space >')]
    selected_people = [c for c in selected_categories if c.startswith('PEOPLE >')]
    
    # Rule 1: If AI says no people, respect that regardless of manual selection
    if ai_no_people:
        # Add only the 'No People' category and remove any other people categories
        result_categories.add('PEOPLE > No People')
        
        # Remove any other people categories that might have been manually selected
        result_categories = {cat for cat in result_categories if not (cat.startswith('PEOPLE >') and cat != 'PEOPLE > No People')}
    else:
        # For people categories, if AI detected people, use manual selections if available
        if ai_people and selected_people and 'PEOPLE > No People' not in selected_people:
            # Extract specific people subcategories
            selected_ethnicity = [c for c in selected_people if 'Ethnicity >' in c]
            selected_age = [c for c in selected_people if 'Age >' in c and not c.endswith('Any Age')]
            selected_count = [c for c in selected_people if '> 2 People' in c or '> 3+ People' in c]
            selected_faceless = [c for c in selected_people if 'Faceless' in c]
            
            # Add the basic 'Any People' category if needed
            if not any('> No People' in c for c in ai_people):
                result_categories.add('PEOPLE > Any People')
            
            # Add specific subcategories from manual selection if available, otherwise from AI
            if selected_ethnicity:
                result_categories.update(selected_ethnicity)
            else:
                result_categories.update([c for c in ai_people if 'Ethnicity >' in c])
                
            if selected_age:
                result_categories.update(selected_age)
            else:
                result_categories.update([c for c in ai_people if 'Age >' in c and not c.endswith('Any Age')])
                
            if selected_count:
                result_categories.update(selected_count)
            else:
                result_categories.update([c for c in ai_people if '> 2 People' in c or '> 3+ People' in c])
                
            if selected_faceless:
                result_categories.update(selected_faceless)
            elif any('Faceless' in c for c in ai_people):
                result_categories.add('PEOPLE > Faceless')
        else:
            # If no manual people categories, use AI's people categories
            result_categories.update(ai_people)
    
    # Rule 2: For orientation, always use the detected orientation from image dimensions
    # Remove any existing orientation categories
    result_categories = {cat for cat in result_categories if not cat.startswith('ORIENTATION >')}
    
    # Add the detected orientation (this was passed in via ai_categories)
    orientation_categories = [cat for cat in ai_categories if cat.startswith('ORIENTATION >')]
    if orientation_categories:
        result_categories.add(orientation_categories[0])
        
    # For mockups and copy space, prefer manual selection
    if selected_mockups:
        result_categories.update(selected_mockups)
    else:
        result_categories.update(ai_mockups)
        
    if selected_copy_space:
        result_categories.update(selected_copy_space)
    else:
        result_categories.update(ai_copy_space)
    
    # Rule 3: For content and colors, combine both sets
    result_categories.update(ai_main)
    result_categories.update(selected_main)
    result_categories.update(ai_colors)
    result_categories.update(selected_colors)
    
    return list(result_categories)


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
    from config.settings import load_config
    
    # Load configuration
    config = load_config()
    
    parser = argparse.ArgumentParser(description='Process images and update categories in WooCommerce CSV')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--batch-size', type=int, default=config.get('batch_size', 5), 
                        help='Number of images to process in a batch')
    parser.add_argument('--start-row', type=int, default=0, 
                        help='Row number to start processing from (0-based)')
    parser.add_argument('--api-key', help='OpenAI API key (overrides environment variable)')
    parser.add_argument('--mock', action='store_true', 
                        help='Run in mock mode without making API calls')
    
    args = parser.parse_args()
    
    # Set up API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    
    # Configure mock mode and client
    global MOCK_MODE, client
    
    if args.mock or config.get('mock_mode', False):
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