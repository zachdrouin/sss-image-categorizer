#!/usr/bin/env python3
"""
Diagnostic script to test OpenAI client initialization methods
This helps identify which initialization method works in bundled macOS apps
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_openai_initialization(api_key):
    """Test various OpenAI client initialization methods"""
    
    results = []
    
    # Method 1: Direct initialization
    logger.info("\n=== Testing Method 1: Direct initialization ===")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        logger.info("✅ Method 1 SUCCESS: Direct initialization worked")
        results.append(("Direct initialization", True, None))
        
        # Test if client can make calls
        try:
            # Just check if the client has the expected attributes
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                logger.info("✅ Client appears to be properly initialized with chat completion support")
        except Exception as e:
            logger.warning(f"⚠️  Client attribute check failed: {str(e)}")
            
    except Exception as e:
        logger.error(f"❌ Method 1 FAILED: {str(e)}")
        results.append(("Direct initialization", False, str(e)))
    
    # Method 2: Module-level API key
    logger.info("\n=== Testing Method 2: Module-level API key ===")
    try:
        import openai
        openai.api_key = api_key
        client = openai.OpenAI()
        logger.info("✅ Method 2 SUCCESS: Module-level API key worked")
        results.append(("Module-level API key", True, None))
    except Exception as e:
        logger.error(f"❌ Method 2 FAILED: {str(e)}")
        results.append(("Module-level API key", False, str(e)))
    
    # Method 3: No parameters after setting module API key
    logger.info("\n=== Testing Method 3: No parameters client ===")
    try:
        import openai
        openai.api_key = api_key
        # Try to access the client differently
        from openai import OpenAI as OpenAIClient
        client = OpenAIClient()
        logger.info("✅ Method 3 SUCCESS: No parameters client worked")
        results.append(("No parameters client", True, None))
    except Exception as e:
        logger.error(f"❌ Method 3 FAILED: {str(e)}")
        results.append(("No parameters client", False, str(e)))
    
    # Method 4: Environment variable
    logger.info("\n=== Testing Method 4: Environment variable ===")
    try:
        # Set environment variable
        os.environ['OPENAI_API_KEY'] = api_key
        from openai import OpenAI
        client = OpenAI()  # No api_key parameter
        logger.info("✅ Method 4 SUCCESS: Environment variable worked")
        results.append(("Environment variable", True, None))
    except Exception as e:
        logger.error(f"❌ Method 4 FAILED: {str(e)}")
        results.append(("Environment variable", False, str(e)))
    
    # Method 5: Legacy compatibility mode
    logger.info("\n=== Testing Method 5: Legacy compatibility ===")
    try:
        import openai
        openai.api_key = api_key
        # Use the module itself as client
        client = openai
        # Check if we can access completion methods
        if hasattr(openai, 'ChatCompletion') or hasattr(openai, 'chat'):
            logger.info("✅ Method 5 SUCCESS: Legacy compatibility mode available")
            results.append(("Legacy compatibility", True, None))
        else:
            logger.warning("⚠️  Method 5 PARTIAL: Module imported but may lack expected methods")
            results.append(("Legacy compatibility", True, "Limited functionality"))
    except Exception as e:
        logger.error(f"❌ Method 5 FAILED: {str(e)}")
        results.append(("Legacy compatibility", False, str(e)))
    
    # Summary
    logger.info("\n=== SUMMARY ===")
    successful_methods = [r for r in results if r[1]]
    failed_methods = [r for r in results if not r[1]]
    
    if successful_methods:
        logger.info(f"✅ {len(successful_methods)} methods succeeded:")
        for method, _, error in successful_methods:
            logger.info(f"   - {method}")
    
    if failed_methods:
        logger.info(f"❌ {len(failed_methods)} methods failed:")
        for method, _, error in failed_methods:
            logger.info(f"   - {method}: {error}")
    
    # Check for proxies error specifically
    proxies_errors = [r for r in results if not r[1] and 'proxies' in str(r[2])]
    if proxies_errors:
        logger.warning("\n⚠️  PROXIES PARAMETER ERROR DETECTED!")
        logger.warning("This is the specific error affecting bundled macOS apps.")
        logger.warning("Use one of the successful methods above to avoid this issue.")
    
    return results

def main():
    """Main function"""
    # Try to get API key from various sources
    api_key = None
    
    # 1. Command line argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        logger.info("Using API key from command line argument")
    
    # 2. Environment variable
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            logger.info("Using API key from OPENAI_API_KEY environment variable")
    
    # 3. Config file (if exists)
    if not api_key:
        config_file = os.path.join(os.path.expanduser("~"), ".image_categorizer_config.json")
        if os.path.exists(config_file):
            try:
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    api_key = config.get('api_key')
                    if api_key:
                        logger.info("Using API key from config file")
            except:
                pass
    
    if not api_key:
        logger.error("No API key found. Please provide via:")
        logger.error("1. Command line: python test_openai_init.py YOUR_API_KEY")
        logger.error("2. Environment: export OPENAI_API_KEY=YOUR_API_KEY")
        logger.error("3. Config file: ~/.image_categorizer_config.json")
        sys.exit(1)
    
    # Mask API key for security
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    logger.info(f"Testing with API key: {masked_key}")
    
    # Run tests
    test_openai_initialization(api_key)

if __name__ == "__main__":
    main()
