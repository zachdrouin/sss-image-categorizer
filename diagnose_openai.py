#!/usr/bin/env python3
"""
Diagnostic script to identify the exact source of the 'proxies' parameter error
"""

import os
import sys
import inspect
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def inspect_openai_client():
    """Inspect the OpenAI client to identify the source of the proxies parameter error"""
    try:
        # Import the OpenAI module
        import openai
        logger.info(f"OpenAI version: {openai.__version__}")
        
        # Inspect the OpenAI client
        from openai import OpenAI
        logger.info(f"OpenAI client: {OpenAI}")
        
        # Get the signature of the OpenAI client
        signature = inspect.signature(OpenAI.__init__)
        logger.info(f"OpenAI client signature: {signature}")
        
        # Get the source code of the OpenAI client
        try:
            source = inspect.getsource(OpenAI.__init__)
            logger.info(f"OpenAI client source:\n{source}")
        except Exception as e:
            logger.error(f"Could not get source code: {str(e)}")
        
        # Try to create a client with various parameters
        logger.info("Attempting to create OpenAI client with no parameters")
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("No API key found in environment, using placeholder")
            api_key = "sk-placeholder"
        
        # Try with just api_key
        try:
            client1 = OpenAI(api_key=api_key)
            logger.info("✅ Successfully created client with api_key parameter")
        except Exception as e:
            logger.error(f"❌ Failed to create client with api_key parameter: {str(e)}")
        
        # Try with environment variable
        try:
            os.environ['OPENAI_API_KEY'] = api_key
            client2 = OpenAI()
            logger.info("✅ Successfully created client with environment variable")
        except Exception as e:
            logger.error(f"❌ Failed to create client with environment variable: {str(e)}")
        
        # Try with proxies parameter
        try:
            client3 = OpenAI(api_key=api_key, proxies={"http": None, "https": None})
            logger.info("✅ Successfully created client with proxies parameter")
        except Exception as e:
            logger.error(f"❌ Failed to create client with proxies parameter: {str(e)}")
            
        # Check if requests library is being used
        import requests
        logger.info(f"Requests version: {requests.__version__}")
        
        # Check if requests is using proxies
        session = requests.Session()
        logger.info(f"Requests session proxies: {session.proxies}")
        
        # Check environment variables
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                      'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
        for var in proxy_vars:
            if var in os.environ:
                logger.info(f"Environment variable {var}={os.environ[var]}")
        
        return True
    except Exception as e:
        logger.error(f"Inspection failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function"""
    logger.info("Starting OpenAI client inspection")
    if inspect_openai_client():
        logger.info("Inspection completed successfully")
    else:
        logger.error("Inspection failed")

if __name__ == "__main__":
    main()
