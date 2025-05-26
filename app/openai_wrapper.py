#!/usr/bin/env python3
"""
OpenAI Client Wrapper

This module provides a simple wrapper around the OpenAI client that avoids
the 'proxies' parameter error by directly importing and using the OpenAI client
without any proxy configuration.
"""

import os
import logging
from openai import OpenAI as OriginalOpenAI

logger = logging.getLogger(__name__)

class OpenAI:
    """
    Wrapper for OpenAI client that avoids the 'proxies' parameter error.
    """
    
    def __init__(self, api_key=None, **kwargs):
        """
        Initialize the OpenAI client without the proxies parameter.
        
        Args:
            api_key: OpenAI API key
            **kwargs: Other parameters to pass to the OpenAI client
        """
        # Set API key in environment if provided
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
            logger.debug("Set OPENAI_API_KEY environment variable")
        
        # Remove proxies parameter if present
        if 'proxies' in kwargs:
            logger.debug("Removing 'proxies' parameter")
            del kwargs['proxies']
        
        # Initialize the original client
        try:
            logger.debug(f"Initializing OpenAI client with kwargs: {kwargs}")
            self._client = OriginalOpenAI(**kwargs)
            logger.debug("Successfully initialized OpenAI client")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise
    
    def __getattr__(self, name):
        """
        Forward attribute access to the wrapped client.
        
        Args:
            name: Attribute name
            
        Returns:
            The attribute from the wrapped client
        """
        return getattr(self._client, name)
