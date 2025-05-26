#!/usr/bin/env python3
"""
OpenAI Library Patch for Proxies Parameter Error

This script patches the OpenAI library to handle the 'proxies' parameter gracefully,
preventing the "Client.__init__() got an unexpected keyword argument 'proxies'" error.

Usage:
    import openai_patch
    openai_patch.apply()  # Apply the patch before importing OpenAI
"""

import sys
import os
import logging
import importlib
from types import ModuleType
from typing import Any, Dict, Optional, Type

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Original OpenAI Client class
original_openai_client = None

# Patched OpenAI Client class that handles proxies parameter
class PatchedOpenAIClient:
    """Patched version of the OpenAI Client class that handles the proxies parameter"""
    
    def __new__(cls, *args, **kwargs):
        # Print all kwargs for debugging
        logger.debug(f"OpenAI Client initialization with kwargs: {kwargs}")
        
        # Remove proxies parameter if present
        if 'proxies' in kwargs:
            logger.info("Removing 'proxies' parameter from OpenAI client initialization")
            del kwargs['proxies']
        
        # Print environment variables for debugging
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                      'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
        for var in proxy_vars:
            if var in os.environ:
                logger.debug(f"Environment variable {var}={os.environ[var]}")
                # Remove proxy environment variables
                del os.environ[var]
                logger.debug(f"Removed {var} from environment")
        
        # Create the original client with cleaned kwargs
        logger.debug(f"Creating OpenAI client with cleaned kwargs: {kwargs}")
        try:
            client = original_openai_client(*args, **kwargs)
            logger.debug("Successfully created OpenAI client")
            return client
        except Exception as e:
            logger.error(f"Error creating OpenAI client: {str(e)}")
            raise

def patch_openai_module():
    """Patch the OpenAI module to handle proxies parameter"""
    try:
        logger.debug("Starting to patch OpenAI module")
        
        # Print Python path for debugging
        logger.debug(f"Python path: {sys.path}")
        
        # Print loaded modules for debugging
        logger.debug(f"Loaded modules: {list(sys.modules.keys())}")
        
        # Import the OpenAI module
        if 'openai' in sys.modules:
            # If already imported, reload it
            logger.debug("OpenAI module already imported, reloading it")
            openai_module = importlib.reload(sys.modules['openai'])
        else:
            # Otherwise import it fresh
            logger.debug("Importing OpenAI module fresh")
            openai_module = importlib.import_module('openai')
        
        # Get the original OpenAI class
        global original_openai_client
        original_openai_client = openai_module.OpenAI
        logger.debug(f"Original OpenAI client: {original_openai_client}")
        
        # Replace it with our patched version
        openai_module.OpenAI = PatchedOpenAIClient
        logger.debug(f"Replaced OpenAI.OpenAI with PatchedOpenAIClient")
        
        # Verify the patch was applied
        if openai_module.OpenAI == PatchedOpenAIClient:
            logger.info("✅ Successfully patched OpenAI module to handle proxies parameter")
            return True
        else:
            logger.error("❌ Patch verification failed: OpenAI.OpenAI is not PatchedOpenAIClient")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to patch OpenAI module: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def apply():
    """Apply the OpenAI patch"""
    return patch_openai_module()

# If run directly, apply the patch
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if apply():
        print("✅ OpenAI patch applied successfully")
    else:
        print("❌ Failed to apply OpenAI patch")
