#!/usr/bin/env python3
"""
Web-based UI for the Image Categorizer using Flask

A user-friendly interface for categorizing images using the OpenAI API.
This tool allows users to categorize multiple images at once and apply
common categories to all images for faster processing.
"""

import os
import sys

import json
import logging
import threading
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import keyring
import secrets
import webbrowser

# Add parent directory to path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration modules
from config.settings import setup_logging, APP_NAME, APP_VERSION, SERVICE_NAME, KEY_NAME, CONFIG_FILE, FIRST_RUN_FLAG, load_config, save_config
from config.category_manager import category_manager

# Import the image_categorizer module
try:
    # Try relative import for when used as a module
    from . import image_categorizer
except ImportError:
    # Fall back to direct import for when run as a script
    import image_categorizer

# Import our fixed OpenAI client
from app.openai_fixed import OpenAI

# Configure logging
logger = setup_logging('web_categorizer')

# Create Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Global variables
processing_thread = None
progress = {"current": 0, "total": 0, "message": "", "complete": False, "success": False}
stop_requested = False

def get_api_key():
    """Get the API key from keyring"""
    try:
        return keyring.get_password(SERVICE_NAME, KEY_NAME)
    except Exception as e:
        logger.error(f"Error retrieving API key: {str(e)}")
        return None

def save_api_key(api_key):
    """Save the API key to keyring"""
    try:
        keyring.set_password(SERVICE_NAME, KEY_NAME, api_key)
        return True
    except Exception as e:
        logger.error(f"Error saving API key: {str(e)}")
        return False

# Note: load_config and save_config are now imported from config.settings

def update_progress(current, total, message=""):
    """Update the progress information"""
    global progress
    progress["current"] = current
    progress["total"] = total
    progress["message"] = message
    logger.info(f"Progress: {current}/{total} - {message}")

def process_images(input_file, output_file, api_key, batch_size=5, start_row=0, mock_mode=False, selected_categories=None, skip_analysis=False):
    """Process images from a CSV file and update with categories"""
    global progress, stop_requested
    
    try:
        # Initialize the OpenAI client using our wrapper
        try:
            # Create the OpenAI client with our wrapper
            client = OpenAI(api_key=api_key)
            image_categorizer.client = client
            logger.info("OpenAI client initialized successfully for image processing")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            progress["message"] = f"Error: Failed to initialize OpenAI client - {str(e)}"
            progress["complete"] = True
            progress["success"] = False
            return
        
        # Validate if selected_categories is None or empty
        has_selected_categories = selected_categories and len(selected_categories) > 0
        logger.info(f"Processing with selected_categories: {has_selected_categories}, skip_analysis: {skip_analysis}")
        
        # Check if file exists
        if not os.path.exists(input_file):
            progress["message"] = f"Input file does not exist: {input_file}"
            progress["complete"] = True
            return
        
        # Read the CSV file
        df = pd.read_csv(input_file)
        total_rows = len(df) - start_row
        
        if total_rows <= 0:
            progress["message"] = "No rows to process or invalid start row."
            progress["complete"] = True
            return
        
        # Update progress
        progress["total"] = total_rows
        progress["current"] = 0
        
        # Validate Images column
        if 'Images' not in df.columns:
            progress["message"] = "CSV must have an 'Images' column."
            progress["complete"] = True
            return
        
        # Ensure Categories column exists
        if 'Categories' not in df.columns:
            df['Categories'] = ''
        
        # Initialize OpenAI client if needed
        if not mock_mode and not skip_analysis:
            image_categorizer.client = image_categorizer.OpenAI(api_key=api_key)
        
        # Process rows in batches
        for batch_start in range(0, total_rows, batch_size):
            if stop_requested:
                progress["message"] = "Processing stopped by user."
                progress["complete"] = True
                return
            
            batch_end = min(batch_start + batch_size, total_rows)
            progress["message"] = f"Processing rows {batch_start + 1} to {batch_end} of {total_rows}..."
            
            # Process each row in the batch
            for current_row in range(batch_start, batch_end):
                if stop_requested:
                    break
                
                # Update progress
                progress["current"] = current_row + 1
                row = df.iloc[current_row + start_row]
                
                # Get existing categories if any
                existing_categories = df.at[current_row + start_row, 'Categories']
                if pd.isna(existing_categories):
                    existing_categories = ''
                
                # If we have selected categories, apply them
                if has_selected_categories:
                    # Combine existing with selected categories
                    combined_categories = set()
                    
                    # Add existing categories if any
                    if existing_categories:
                        existing_list = [c.strip() for c in existing_categories.split(',')]
                        combined_categories.update(existing_list)
                    
                    # Add selected categories
                    combined_categories.update(selected_categories)
                    
                    # If we're using the combined approach (not skipping analysis), we'll continue to AI analysis
                    # Otherwise, update the dataframe with just the manual categories
                    if skip_analysis:
                        # Update the dataframe with just manual categories
                        df.at[current_row + start_row, 'Categories'] = ', '.join(sorted(combined_categories))
                        logger.info(f"Applied ONLY manual categories to image {current_row + 1} of {total_rows} (skipping AI analysis)")
                        
                        # Save after each batch in case of interruption
                        df.to_csv(output_file, index=False)
                        logger.info(f"Saved progress to {output_file}")
                        continue
                    else:
                        # We'll store these for the AI to use as constraints
                        # The actual update will happen after AI analysis
                        logger.info(f"Using SMART COMBINED approach for image {current_row + 1} of {total_rows} with {len(selected_categories)} manual categories")
                
                # Analyze with API if:
                # 1. There are no existing categories, OR
                # 2. We're using the SMART COMBINED approach (not skipping analysis)
                if not existing_categories or not skip_analysis:
                    try:
                        # Analyze the image
                        if mock_mode:
                            logger.info(f"Using mock analysis for image {current_row + 1} of {total_rows}")
                            categories = image_categorizer.mock_analyze_image()
                        else:
                            # Pass selected categories to the analyze function if we have them
                            if has_selected_categories:
                                logger.info(f"Analyzing image {current_row + 1} of {total_rows} with GPT-4V using {len(selected_categories)} manual categories as constraints")
                                categories = image_categorizer.analyze_image_with_gpt4v(row['Images'], selected_categories)
                            else:
                                logger.info(f"Analyzing image {current_row + 1} of {total_rows} with GPT-4V without constraints")
                                categories = image_categorizer.analyze_image_with_gpt4v(row['Images'])
                        
                        # Post-process people categories using description if available
                        description = row.get('Description', '')
                        if categories and pd.notna(description):
                            categories = image_categorizer.post_process_people_categories(categories, description)
                        
                        # Combine with existing categories if any
                        combined_categories = set()
                        if existing_categories:
                            existing_list = [c.strip() for c in existing_categories.split(',')]
                            combined_categories.update(existing_list)
                        
                        # Add AI-generated categories
                        if categories:
                            combined_categories.update(categories)
                        
                        # Update the dataframe
                        if combined_categories:
                            df.at[current_row + start_row, 'Categories'] = ', '.join(sorted(combined_categories))
                            if has_selected_categories and not skip_analysis:
                                logger.info(f"SMART COMBINED result for image {current_row + 1} of {total_rows}: {len(combined_categories)} categories applied")
                                logger.info(f"Manual categories: {selected_categories}")
                                logger.info(f"AI categories: {categories}")
                                logger.info(f"Combined result: {combined_categories}")
                            else:
                                logger.info(f"Updated categories for row {current_row + 1}: {combined_categories}")
                        
                        # Save after each image in case of interruption
                        df.to_csv(output_file, index=False)
                        
                        # Rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        error_msg = f"Error processing row {current_row + 1}: {str(e)}"
                        logger.error(error_msg)
                        progress["message"] = error_msg
        
        # Set completion message based on what was done        
        if has_selected_categories:
            progress["message"] = f"Successfully processed {total_rows} images with {len(selected_categories)} manual categories!"
        else:
            progress["message"] = f"Successfully processed {total_rows} images with AI categorization!"
        
        progress["success"] = True
        
        # Final save to ensure all changes are saved
        df.to_csv(output_file, index=False)
        logger.info(f"Completed processing. Results saved to {output_file}")
        
    except Exception as e:
        error_msg = f"Error during processing: {str(e)}"
        logger.error(error_msg)
        progress["message"] = error_msg
    
    # Mark processing as complete
    progress["complete"] = True

def categorize_valid_categories():
    """Categorize the valid categories into groups for easier selection"""
    # Get categories by group from the category manager
    category_groups = category_manager.get_categories_by_group()
    
    # Map category manager groups to UI groups
    categories = {
        'main': category_groups.get('main_categories', []),
        'colors': category_groups.get('colors', []),
        'mockups': category_groups.get('mockups', []),
        'orientation': category_groups.get('orientation', []),
        'copy_space': category_groups.get('copy_space', [])
    }
    
    # Process people categories which have a more complex structure
    people_categories = category_groups.get('people', [])
    
    # Create a 'people' category for the UI to use
    categories['people'] = people_categories
    
    # Filter people categories into subgroups for more specific UI organization
    categories['people_main'] = [
        c for c in people_categories 
        if '>' not in c[8:] or c.endswith('Any Age') or c.endswith('Any People') or c.endswith('Any Ethnicity')
    ]
    
    categories['people_age'] = [
        c for c in people_categories 
        if c.startswith('PEOPLE > Any Age >')
    ]
    
    categories['people_count'] = [
        c for c in people_categories 
        if c.startswith('PEOPLE > Any People >')
    ]
    
    categories['people_ethnicity'] = [
        c for c in people_categories 
        if c.startswith('PEOPLE > Any Ethnicity >')
    ]
    
    # Sort each category list alphabetically
    for key in categories:
        categories[key].sort()
    
    # Log loaded categories for debugging
    logger.info(f"Loaded categories: {len(category_manager.get_all_categories())} total")
    for group, cats in categories.items():
        logger.info(f"  {group}: {len(cats)} categories")
    
    return categories

@app.route('/')
def index():
    """Main page"""
    api_key = get_api_key()
    config = load_config()
    categories = categorize_valid_categories()
    
    # Check if this is the first run
    is_first_run = not os.path.exists(FIRST_RUN_FLAG)
    if is_first_run:
        return redirect(url_for('welcome'))
    
    return render_template('index.html', 
                           has_api_key=bool(api_key), 
                           config=config,
                           categories=categories)

@app.route('/welcome')
def welcome():
    """Welcome page for first-time users"""
    # Check if this is the first run
    is_first_run = not os.path.exists(FIRST_RUN_FLAG)
    
    # Create the first run flag file if it doesn't exist
    if is_first_run:
        with open(FIRST_RUN_FLAG, 'w') as f:
            f.write(f"First run completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    api_key = get_api_key()
    
    return render_template('welcome.html', 
                           has_api_key=bool(api_key),
                           is_first_run=is_first_run,
                           app_version=APP_VERSION)

@app.route('/')
def index_route():
    return index()

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page"""
    if request.method == 'POST':
        api_key = request.form.get('api_key', '').strip()
        if api_key:
            if save_api_key(api_key):
                flash('API key saved successfully!', 'success')
            else:
                flash('Failed to save API key.', 'error')
        return redirect(url_for('index'))
    
    api_key = get_api_key()
    return render_template('settings.html', api_key=api_key)

@app.route('/process', methods=['POST'])
def process():
    """Start processing images"""
    global processing_thread, progress, stop_requested
    
    # Check if already processing
    if processing_thread and processing_thread.is_alive():
        flash("Already processing images. Please wait or stop the current process.", "warning")
        return redirect(url_for('index'))
    
    # Get form data
    input_file = request.form.get('input_file')
    output_file = request.form.get('output_file')
    batch_size = int(request.form.get('batch_size', 5))
    start_row = int(request.form.get('start_row', 0))
    mock_mode = 'mock_mode' in request.form
    
    # Check if we should use the combined approach
    use_combined_approach = 'use_combined_approach' in request.form
    logger.info(f"use_combined_approach: {use_combined_approach}")
    
    # Set skip_analysis based on the combined approach checkbox
    # If use_combined_approach is True, we don't want to skip analysis
    # If use_combined_approach is False, we do want to skip analysis
    skip_analysis = not use_combined_approach
    logger.info(f"skip_analysis: {skip_analysis}")
    
    # For backward compatibility, also check the hidden skip_analysis field
    if 'skip_analysis' in request.form and request.form.get('skip_analysis') == '1':
        skip_analysis = True
        logger.info("Overriding with skip_analysis=1 from hidden field")
    
    # Get selected categories (if any)
    selected_categories = []
    selected_categories_json = request.form.get('selected_categories', '')
    if selected_categories_json:
        try:
            selected_categories = json.loads(selected_categories_json)
            logger.info(f"Selected categories to apply to all images: {selected_categories}")
        except Exception as e:
            logger.error(f"Error parsing selected categories: {str(e)}")    
    
    # Validate input file
    if not input_file or not os.path.exists(input_file):
        flash(f"Input file does not exist: {input_file}", "error")
        return redirect(url_for('index'))
    
    # Set default output file if not provided
    if not output_file:
        input_path = Path(input_file)
        output_file = str(input_path.with_name(f"{input_path.stem}_categorized{input_path.suffix}"))
    
    # Get API key
    api_key = get_api_key()
    if not api_key and not mock_mode:
        flash("No API key set. Please set your OpenAI API key in Settings or use Mock Mode.", "error")
        return redirect(url_for('index'))
    
    # Save configuration
    config = load_config()
    config['last_input_file'] = input_file
    config['last_output_file'] = output_file
    config['batch_size'] = batch_size
    config['start_row'] = start_row
    config['mock_mode'] = mock_mode
    save_config(config)
    
    # Reset progress
    progress = {"current": 0, "total": 0, "message": "Starting...", "complete": False}
    stop_requested = False
    
    # Start processing in a separate thread
    processing_thread = threading.Thread(
        target=process_images,
        args=(input_file, output_file, api_key, batch_size, start_row, mock_mode, selected_categories, skip_analysis)
    )
    processing_thread.daemon = True
    processing_thread.start()
    
    flash("Processing started", "success")
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    """Stop processing"""
    global stop_requested
    stop_requested = True
    image_categorizer.STOP_PROCESSING = True
    flash('Processing will stop after the current batch.', 'info')
    return redirect(url_for('index'))

@app.route('/progress')
def get_progress():
    """Get the current progress"""
    global progress
    return jsonify(progress)

@app.route('/reset', methods=['POST'])
def reset_app():
    """Reset the application state but preserve API key"""
    global processing_thread, progress, stop_requested
    
    # Stop any running process
    stop_requested = True
    image_categorizer.STOP_PROCESSING = True
    
    # Wait for thread to finish if it's running
    if processing_thread and processing_thread.is_alive():
        # Give it a moment to stop gracefully
        processing_thread.join(1.0)
    
    # Reset progress state
    progress = {
        "current": 0, 
        "total": 0, 
        "message": "Ready", 
        "complete": False,
        "success": False
    }
    
    # Reset processing flags
    stop_requested = False
    image_categorizer.STOP_PROCESSING = False
    
    # Preserve API key but reset other config to defaults
    config = load_config()
    api_key = config.get('api_key', '')
    
    # Reset to defaults but keep API key
    config = {
        'api_key': api_key,
        'last_input_file': '',
        'last_output_file': '',
        'batch_size': 5,
        'start_row': 0,
        'mock_mode': False
    }
    save_config(config)
    
    # Return success
    return jsonify({"success": True, "message": "Application has been reset"})

@app.route('/browse', methods=['GET'])
def browse():
    """Browse for input or output file"""
    try:
        browse_type = request.args.get('type', 'input')
        if browse_type == 'input':
            return browse_input_internal()
        elif browse_type == 'output':
            return browse_output_internal()
        else:
            return jsonify({"error": "Invalid browse type"})
    except Exception as e:
        logger.error(f"Error in browse: {str(e)}")
        return jsonify({"error": str(e)})

# Lock to prevent multiple file dialogs from appearing simultaneously
import threading
file_dialog_lock = threading.Lock()

def browse_input_internal():
    """Internal function to browse for input file"""
    try:
        # Use a lock to prevent multiple dialogs
        if not file_dialog_lock.acquire(blocking=False):
            logger.warning("File dialog already in progress, ignoring duplicate request")
            return jsonify({"error": "File dialog already in progress"})
            
        try:
            # Use a system dialog instead of Tkinter to avoid threading issues
            import subprocess
            import platform
            import tempfile
            
            if platform.system() == 'Darwin':  # macOS
                # Create a temporary AppleScript file
                with tempfile.NamedTemporaryFile(suffix='.applescript', delete=False) as script_file:
                    script = '''
                    set theFile to choose file with prompt "Select Input CSV File" of type {"csv"}
                    set thePath to POSIX path of theFile
                    return thePath
                    '''
                    script_file.write(script.encode('utf-8'))
                    script_path = script_file.name
                
                # Run the AppleScript
                result = subprocess.run(['osascript', script_path], capture_output=True, text=True)
                os.unlink(script_path)  # Delete the temporary file
                
                input_file = result.stdout.strip()
                
                if input_file:
                    # Auto-generate output filename
                    input_path = Path(input_file)
                    output_file = str(input_path.with_name(f"{input_path.stem}_categorized{input_path.suffix}"))
                    
                    return jsonify({"path": input_file, "output_file": output_file})
        finally:
            # Always release the lock
            file_dialog_lock.release()
        
        return jsonify({})
    except Exception as e:
        logger.error(f"Error in browse_input_internal: {str(e)}")
        return jsonify({"error": str(e)})

@app.route('/browse_input', methods=['POST'])
def browse_input():
    """Browse for input file (legacy route)"""
    return browse_input_internal()

def browse_output_internal():
    """Internal function to browse for output file"""
    try:
        # Use a lock to prevent multiple dialogs
        if not file_dialog_lock.acquire(blocking=False):
            logger.warning("File dialog already in progress, ignoring duplicate request")
            return jsonify({"error": "File dialog already in progress"})
            
        try:
            # Use a system dialog instead of Tkinter to avoid threading issues
            import subprocess
            import platform
            import tempfile
            
            if platform.system() == 'Darwin':  # macOS
                # Create a temporary AppleScript file
                with tempfile.NamedTemporaryFile(suffix='.applescript', delete=False) as script_file:
                    script = '''
                    set theFile to choose file name with prompt "Save As" default name "categorized_output.csv"
                    set thePath to POSIX path of theFile
                    return thePath
                    '''
                    script_file.write(script.encode('utf-8'))
                    script_path = script_file.name
                
                # Run the AppleScript
                result = subprocess.run(['osascript', script_path], capture_output=True, text=True)
                os.unlink(script_path)  # Delete the temporary file
                
                output_file = result.stdout.strip()
                
                if output_file:
                    # Ensure the file has a .csv extension
                    if not output_file.lower().endswith('.csv'):
                        output_file += '.csv'
                    return jsonify({"path": output_file})
        finally:
            # Always release the lock
            file_dialog_lock.release()
        
        return jsonify({})
    except Exception as e:
        logger.error(f"Error in browse_output_internal: {str(e)}")
        return jsonify({"error": str(e)})

@app.route('/browse_output', methods=['POST'])
def browse_output():
    """Browse for output file (legacy route)"""
    return browse_output_internal()

def create_templates_folder():
    """Ensure the templates folder exists"""
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    logger.info(f"Ensured templates directory exists at: {templates_dir}")
    
    # Also ensure static folders exist
    for static_folder in ['css', 'js', 'img']:
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', static_folder)
        os.makedirs(static_dir, exist_ok=True)

# Welcome route is already defined above

# Add a route for applying categories to all images
@app.route('/apply_categories_to_all', methods=['POST'])
def apply_categories_to_all():
    """Apply selected categories to all images in the input file"""
    try:
        data = request.json
        categories = data.get('categories', [])
        input_file = data.get('input_file', '')
        
        if not categories:
            return jsonify({"success": False, "message": "No categories selected"})
            
        if not input_file or not os.path.exists(input_file):
            return jsonify({"success": False, "message": "Input file not found"})
            
        # Load the CSV file
        df = pd.read_csv(input_file)
        
        # Check if the 'categories' column exists
        if 'categories' not in df.columns:
            df['categories'] = ''
            
        # Apply the selected categories to all rows
        for index, row in df.iterrows():
            current_categories = row['categories']
            
            # Parse existing categories if they exist
            existing_categories = []
            if current_categories and isinstance(current_categories, str):
                try:
                    existing_categories = json.loads(current_categories)
                except:
                    # If not valid JSON, treat as comma-separated list
                    existing_categories = [c.strip() for c in current_categories.split(',') if c.strip()]
            
            # Add new categories, avoiding duplicates
            for category in categories:
                if category not in existing_categories:
                    existing_categories.append(category)
            
            # Update the categories column
            df.at[index, 'categories'] = json.dumps(existing_categories)
        
        # Save the updated CSV file
        df.to_csv(input_file, index=False)
        
        logger.info(f"Applied {len(categories)} categories to all images in {input_file}")
        return jsonify({"success": True, "message": f"Applied {len(categories)} categories to all images"})
        
    except Exception as e:
        logger.error(f"Error applying categories to all images: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# Add a route for sample data
@app.route('/sample_data')
def get_sample_data_route():
    """Provide a sample CSV to get started"""
    sample_file = create_sample_data()
    return jsonify({"sample_file": sample_file})

def create_sample_data():
    """Create sample data file and return its path"""
    sample_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(sample_data_dir, exist_ok=True)
    sample_file = os.path.join(sample_data_dir, 'sample_images.csv')
    
    # Create sample data if it doesn't exist
    if not os.path.exists(sample_file):
        with open(sample_file, 'w') as f:
            f.write("image_url,description\n")
            f.write("https://images.unsplash.com/photo-1504593811423-6dd665756598,Mountain landscape\n")
            f.write("https://images.unsplash.com/photo-1523531294919-4bcd7c65e216,Beach sunset\n")
            f.write("https://images.unsplash.com/photo-1501963422762-3d89bd989568,Urban cityscape\n")
    
    return sample_file

# Helper function to check for updates
def check_for_updates():
    """Check if a newer version is available"""
    try:
        # This is a placeholder. In a real app, you'd query a server
        return {"has_update": False, "latest_version": APP_VERSION}
    except Exception as e:
        logger.error(f"Error checking for updates: {str(e)}")
        return {"has_update": False, "latest_version": APP_VERSION}

def main():
    """Main entry point for the application"""
    # Create templates and static folders
    create_templates_folder()
    
    # Ensure sample data exists
    create_sample_data()
    
    # Get a free port
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    
    # Open browser
    url = f"http://localhost:{port}"
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    
    print(f"✨ Starting Image Categorizer v{APP_VERSION} web interface at {url}")
    print("💡 Your wife will be able to easily categorize images with this tool!")
    app.run(host='localhost', port=port, debug=False)

if __name__ == "__main__":
    main()
