#!/usr/bin/env python3
"""
OpenAI Client Initialization Module

This module provides a reliable way to initialize the OpenAI client
that works in both regular Python environments and bundled macOS apps.
It handles the 'proxies' parameter error that can occur in bundled apps.
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)


def get_openai_client(api_key=None):
    """
    Initialize and return an OpenAI client using the most reliable method.
    
    This function tries multiple initialization methods to handle various
    environment issues, particularly the 'proxies' parameter error that
    can occur in bundled macOS applications.
    
    Args:
        api_key: OpenAI API key. If not provided, will try to get from environment.
    
    Returns:
        OpenAI client instance
        
    Raises:
        Exception: If all initialization methods fail
    """
    # If no API key provided, try to get from environment
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("No API key provided and OPENAI_API_KEY environment variable not set")
    
    # Clean the environment to prevent proxy-related issues
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
            logger.debug(f"Removed {var} from environment")
    
    # Method 1: Try environment variable approach first (most reliable for bundled apps)
    try:
        logger.info("Attempting OpenAI client initialization via environment variable")
        os.environ['OPENAI_API_KEY'] = api_key
        from openai import OpenAI
        client = OpenAI()  # No parameters - uses environment variable
        
        # Verify the client is properly initialized
        if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
            logger.info("✅ OpenAI client initialized successfully via environment variable")
            return client
    except Exception as e:
        logger.warning(f"Environment variable method failed: {str(e)}")
    
    # Method 2: Try direct initialization with minimal parameters
    try:
        logger.info("Attempting direct OpenAI client initialization")
        # Fresh import to avoid any module-level contamination
        if 'openai' in sys.modules:
            del sys.modules['openai']
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
            logger.info("✅ OpenAI client initialized successfully via direct method")
            return client
    except Exception as e:
        logger.warning(f"Direct initialization failed: {str(e)}")
    
    # Method 3: Try module-level API key setting
    try:
        logger.info("Attempting module-level API key initialization")
        import openai
        openai.api_key = api_key
        
        # Try to create client without parameters
        from openai import OpenAI
        client = OpenAI()
        
        if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
            logger.info("✅ OpenAI client initialized successfully via module-level API key")
            return client
    except Exception as e:
        logger.warning(f"Module-level API key method failed: {str(e)}")
    
    # Method 4: Legacy compatibility mode as last resort
    try:
        logger.info("Attempting legacy compatibility mode")
        import openai
        openai.api_key = api_key
        
        # Return the module itself as a client-like object
        if hasattr(openai, 'ChatCompletion') or hasattr(openai, 'chat'):
            logger.info("✅ OpenAI module loaded in legacy compatibility mode")
            logger.warning("Note: Using legacy mode - some features may be limited")
            return openai
    except Exception as e:
        logger.warning(f"Legacy compatibility mode failed: {str(e)}")
    
    # If all methods fail, raise an error with helpful information
    error_msg = (
        "Failed to initialize OpenAI client. This may be due to:\n"
        "1. Invalid API key\n"
        "2. Network connectivity issues\n"
        "3. OpenAI library version incompatibility\n"
        "4. Environment configuration issues\n"
        "\nPlease check the logs above for specific error messages."
    )
    logger.error(error_msg)
    raise Exception(error_msg)


def test_client(client):
    """
    Test if the OpenAI client is working properly.
    
    Args:
        client: OpenAI client instance
        
    Returns:
        bool: True if client is working, False otherwise
    """
    try:
        # Check basic attributes
        if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
            logger.info("Client has expected chat completion attributes")
            return True
        elif hasattr(client, 'ChatCompletion'):
            logger.info("Client has legacy ChatCompletion attribute")
            return True
        else:
            logger.warning("Client missing expected attributes")
            return False
    except Exception as e:
        logger.error(f"Error testing client: {str(e)}")
        return False
