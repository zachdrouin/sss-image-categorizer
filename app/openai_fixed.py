#!/usr/bin/env python3
"""
Fixed OpenAI Client

This module provides a fixed version of the OpenAI client that works around
the 'proxies' parameter error in bundled macOS applications.
"""

import os
import sys
import logging
import importlib
from typing import Optional, Dict, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the original OpenAI client
try:
    from openai import OpenAI as OriginalOpenAI
except ImportError:
    logger.error("Failed to import OpenAI. Make sure the openai package is installed.")
    raise

class OpenAI:
    """
    Fixed OpenAI client that works around the 'proxies' parameter error.
    This class wraps the original OpenAI client and handles all attribute access.
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
            **kwargs: Additional arguments to pass to the OpenAI client
        """
        # Remove proxies from kwargs if present
        if 'proxies' in kwargs:
            logger.info("Removing 'proxies' parameter from OpenAI client initialization")
            del kwargs['proxies']
        
        # Clean environment variables that might cause proxy issues
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                      'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
        for var in proxy_vars:
            if var in os.environ:
                logger.info(f"Removing {var} from environment")
                del os.environ[var]
        
        # Set API key in environment if provided
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
            logger.info("Set OPENAI_API_KEY environment variable")
        
        # Initialize the original client
        try:
            logger.info("Initializing OpenAI client...")
            self._client = OriginalOpenAI(**kwargs)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
    
    def __getattr__(self, name: str) -> Any:
        """
        Forward attribute access to the wrapped client.
        
        Args:
            name: Attribute name
            
        Returns:
            The attribute from the wrapped client
        """
        return getattr(self._client, name)

# Monkey patch the OpenAI module to use our fixed client
def apply_patch():
    """
    Apply the patch to the OpenAI module.
    
    This function replaces the OpenAI class in the openai module with our fixed version.
    """
    try:
        import openai
        openai.OpenAI = OpenAI
        logger.info("Successfully patched OpenAI module")
        return True
    except Exception as e:
        logger.error(f"Failed to patch OpenAI module: {str(e)}")
        return False

# Apply the patch when this module is imported
apply_patch()
