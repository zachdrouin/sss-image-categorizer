"""
Global settings and configuration for the Image Categorizer application.
This centralizes all configurable parameters that were previously scattered across the codebase.
"""

import os
import json
import logging
from pathlib import Path

# Application Information
APP_NAME = "Image Categorizer"
APP_VERSION = "1.0.0"
SERVICE_NAME = "ImageCategorizerApp"
KEY_NAME = "OpenAIApiKey"

# Paths and Files
HOME_DIR = os.path.expanduser("~")
CONFIG_DIR = os.path.join(HOME_DIR, ".image_categorizer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
FIRST_RUN_FLAG = os.path.join(CONFIG_DIR, "first_run")
LOG_DIR = os.path.join(HOME_DIR, "ImageCategorizerLogs")

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Logging Configuration
def setup_logging(name=None):
    """Configure logging with consistent format"""
    from datetime import datetime
    
    log_file = os.path.join(LOG_DIR, f"{name or 'app'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name or __name__)

# Default Configuration
DEFAULT_CONFIG = {
    "batch_size": 5,
    "api_timeout": 30,
    "rate_limit_delay": 1.0,
    "mock_mode": False,
    "recent_files": [],
    "max_recent_files": 5
}

def load_config():
    """Load configuration from file with fallback to defaults"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                config = DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
        except Exception as e:
            logging.error(f"Error loading config: {str(e)}")
    
    # If file doesn't exist or has error, create with defaults
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving config: {str(e)}")
        return False

# OpenAI API Configuration
def get_openai_config():
    """Get configuration for OpenAI API"""
    return {
        "model": "gpt-4-vision-preview",
        "max_tokens": 300,
        "temperature": 0.5,
        "timeout": DEFAULT_CONFIG["api_timeout"]
    }
