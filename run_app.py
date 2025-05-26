#!/usr/bin/env python3
"""
Custom launcher for Image Categorizer that fixes the OpenAI proxies issue

This script modifies the Python environment to intercept and fix the OpenAI
proxies issue before running the application.
"""

import os
import sys
import logging
import importlib.util
from types import ModuleType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_openai_proxies_issue():
    """
    Fix the OpenAI proxies issue by monkey patching the httpx library
    
    The issue occurs because the requests library is passing proxy configuration
    to the httpx library, which is used by the OpenAI client. By monkey patching
    the httpx.Client class, we can intercept the proxies parameter and remove it.
    """
    logger.info("Applying fix for OpenAI proxies issue...")
    
    # First, clean any proxy-related environment variables
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
    for var in proxy_vars:
        if var in os.environ:
            logger.info(f"Removing {var} from environment")
            del os.environ[var]
    
    # Now, monkey patch the httpx.Client class to ignore the proxies parameter
    try:
        import httpx
        
        # Store the original Client.__init__ method
        original_init = httpx.Client.__init__
        
        # Define a new __init__ method that removes the proxies parameter
        def patched_init(self, *args, **kwargs):
            if 'proxies' in kwargs:
                logger.info("Removing 'proxies' parameter from httpx.Client initialization")
                del kwargs['proxies']
            return original_init(self, *args, **kwargs)
        
        # Replace the original __init__ method with our patched version
        httpx.Client.__init__ = patched_init
        
        logger.info("Successfully patched httpx.Client.__init__ to ignore proxies parameter")
        return True
    except ImportError:
        logger.warning("httpx library not found, skipping patch")
        return False
    except Exception as e:
        logger.error(f"Failed to patch httpx.Client.__init__: {str(e)}")
        return False

def run_web_categorizer():
    """Run the web categorizer application"""
    logger.info("Starting Image Categorizer web application...")
    
    # Add the current directory to the Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import the web_categorizer module
    try:
        from app.web_categorizer import main
        main()
    except Exception as e:
        logger.error(f"Failed to run web categorizer: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Apply the fix for the OpenAI proxies issue
    fix_openai_proxies_issue()
    
    # Run the web categorizer application
    run_web_categorizer()
