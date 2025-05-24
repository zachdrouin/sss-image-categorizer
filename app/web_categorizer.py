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
import pandas as pd
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import keyring
import secrets
import webbrowser

# Add the current directory to the path so we can import the image_categorizer module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import image_categorizer

# Configure logging
log_dir = os.path.join(os.path.expanduser("~"), "ImageCategorizerLogs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"web_categorizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
APP_NAME = "Image Categorizer"
APP_VERSION = "1.0.0"
SERVICE_NAME = "ImageCategorizerApp"
KEY_NAME = "OpenAIApiKey"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".image_categorizer_config.json")
FIRST_RUN_FLAG = os.path.join(os.path.expanduser("~"), ".image_categorizer_first_run")

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

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
    return {}

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        return False

def update_progress(current, total, message=""):
    """Update the progress information"""
    global progress
    progress["current"] = current
    progress["total"] = total
    progress["message"] = message
    logger.info(f"Progress: {current}/{total} - {message}")

def process_images(input_file, output_file, api_key, batch_size=5, start_row=0, mock_mode=False, selected_categories=None):
    """Process images in a separate thread"""
    global progress, stop_requested
    
    progress["current"] = 0
    progress["total"] = 0
    progress["message"] = "Starting processing..."
    progress["complete"] = False
    progress["success"] = False
    stop_requested = False
    
    try:
        # Initialize the OpenAI client
        image_categorizer.client = image_categorizer.OpenAI(api_key=api_key)
        image_categorizer.MOCK_MODE = mock_mode
        image_categorizer.STOP_PROCESSING = False
        
        # Load the CSV file
        df = pd.read_csv(input_file)
        total_rows = len(df)
        progress["total"] = total_rows - start_row
        
        # Check if we have selected categories to apply to all images
        has_selected_categories = selected_categories and len(selected_categories) > 0
        if has_selected_categories:
            logger.info(f"Will apply {len(selected_categories)} selected categories to all images")
            progress["message"] = f"Applying {len(selected_categories)} selected categories to all images..."
        
        # Process the images
        for i, (_, row) in enumerate(df.iloc[start_row:].iterrows()):
            if stop_requested or image_categorizer.STOP_PROCESSING:
                progress["message"] = "Processing stopped by user."
                break
                
            current_row = start_row + i
            update_progress(i + 1, progress["total"], f"Processing row {current_row + 1}/{total_rows}")
            
            # Skip if no image URL
            if pd.isna(row.get('Images')):
                continue
            
            # Get existing categories if any
            existing_categories = []
            if pd.notna(row.get('Categories')) and row['Categories']:
                existing_categories = [cat.strip() for cat in row['Categories'].split(',')]
            
            # If we have selected categories to apply to all images
            if has_selected_categories:
                # Combine existing categories with selected categories (avoiding duplicates)
                combined_categories = list(set(existing_categories + selected_categories))
                df.at[current_row + start_row, 'Categories'] = ', '.join(combined_categories)
                logger.info(f"Applied selected categories to row {current_row + 1}")
                
                # Save periodically
                if i % 10 == 0 or i == len(df.iloc[start_row:]) - 1:
                    df.to_csv(output_file, index=False)
                    logger.info(f"Saved progress to {output_file}")
                
                continue  # Skip API analysis if we're just applying selected categories
            
            # Only analyze with API if not already processed and no selected categories
            if not existing_categories:
                try:
                    # Analyze the image
                    if mock_mode:
                        categories = image_categorizer.mock_analyze_image()
                    else:
                        categories = image_categorizer.analyze_image_with_gpt4v(row['Images'])
                    
                    # Post-process people categories using description if available
                    description = row.get('Description', '')
                    if categories and pd.notna(description):
                        categories = image_categorizer.post_process_people_categories(categories, description)
                    
                    # Update the dataframe
                    if categories:
                        df.at[current_row + start_row, 'Categories'] = ', '.join(categories)
                        logger.info(f"Updated categories for row {current_row + 1}: {categories}")
                    
                    # Save after each image in case of interruption
                    df.to_csv(output_file, index=False)
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Error processing row {current_row + 1}: {str(e)}"
                    logger.error(error_msg)
                    progress["message"] = error_msg
        
        if has_selected_categories:
            progress["message"] = f"Successfully applied {len(selected_categories)} categories to all images!"
        else:
            progress["message"] = "Processing completed successfully!"
        
        progress["success"] = True
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        progress["message"] = error_msg
        progress["success"] = False
    finally:
        progress["complete"] = True

def categorize_valid_categories():
    """Categorize the valid categories into groups for easier selection"""
    categories = {
        'main': [],
        'colors': [],
        'people': [],
        'orientation': [],
        'mockups': [],
        'copy_space': []
    }
    
    for category in image_categorizer.VALID_CATEGORIES:
        if category.startswith('Category >'):
            categories['main'].append(category)
        elif category.startswith('Colors >'):
            categories['colors'].append(category)
        elif category.startswith('PEOPLE >'):
            categories['people'].append(category)
        elif category.startswith('ORIENTATION >'):
            categories['orientation'].append(category)
        elif category.startswith('MOCKUPS >'):
            categories['mockups'].append(category)
        elif category.startswith('Copy Space >'):
            categories['copy_space'].append(category)
        else:
            # Add to the category that makes most sense
            if 'mockups' in category.lower():
                categories['mockups'].append(category)
            elif 'orientation' in category.lower():
                categories['orientation'].append(category)
            elif 'people' in category.lower():
                categories['people'].append(category)
            elif 'color' in category.lower():
                categories['colors'].append(category)
            elif 'space' in category.lower():
                categories['copy_space'].append(category)
            else:
                categories['main'].append(category)
    
    # Sort each category list alphabetically
    for key in categories:
        categories[key].sort()
    
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
        args=(input_file, output_file, api_key, batch_size, start_row, mock_mode, selected_categories)
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
