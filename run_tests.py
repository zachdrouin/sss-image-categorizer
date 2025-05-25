#!/usr/bin/env python3
"""
Test runner for Image Categorizer
Provides an easy way to run tests with common options
"""

import sys
import os
import subprocess

def main():
    """Run the tests with appropriate options"""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Default command to run all tests
    cmd = ["pytest", "--cov=app", "--cov=config", "--cov-report=term-missing"]
    
    # Add any arguments passed to this script
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    # Run the tests
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
