#!/usr/bin/env python3
"""
Test script to verify the OpenAI patch works correctly
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_openai_patch():
    """Test the OpenAI patch"""
    logger.info("Testing OpenAI patch...")
    
    # Apply the patch
    import openai_patch
    patch_result = openai_patch.apply()
    logger.info(f"Patch applied: {patch_result}")
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("No OpenAI API key found in environment")
        return False
    
    # Try to create an OpenAI client with proxies parameter
    try:
        logger.info("Creating OpenAI client with proxies parameter...")
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            proxies={"http": "http://localhost:8080", "https": "http://localhost:8080"}
        )
        logger.info("✅ Successfully created OpenAI client with proxies parameter")
        
        # Try to use the client
        try:
            logger.info("Testing client with models.list()...")
            models = client.models.list()
            logger.info(f"✅ Successfully listed models: {len(list(models))} models found")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to list models: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to create OpenAI client: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if test_openai_patch():
        print("✅ OpenAI patch test passed")
        sys.exit(0)
    else:
        print("❌ OpenAI patch test failed")
        sys.exit(1)
