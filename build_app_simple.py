#!/usr/bin/env python3
"""
Simple build script for Image Categorizer macOS app
Just builds the .app bundle without creating DMG
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("=== Building Image Categorizer for macOS ===\n")
    
    # Check for PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
    
    # Check for icon
    if os.path.exists("ImageCategorizer.icns"):
        print("✓ Using ImageCategorizer.icns")
    else:
        print("⚠ No icon file found - app will use default icon")
    
    # Clean previous builds
    print("\nCleaning previous builds...")
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✓ Cleaned {dir_name} directory")
            except OSError as e:
                print(f"⚠️ Warning: Could not fully clean {dir_name}: {e}")
                print("Continuing with build anyway...")
                # Try to remove as much as possible
                for root, dirs, files in os.walk(dir_name, topdown=False):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except:
                            pass
    
    # Build the app
    print("\nBuilding app (this may take a few minutes)...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "ImageCategorizer.spec"
        ])
        
        print("\n✅ Build complete!")
        print("\n📦 Your app is ready at: dist/Image Categorizer.app")
        print("\nTo install on your wife's Mac:")
        print("1. Copy the entire 'Image Categorizer.app' folder")
        print("2. Paste it into her Applications folder (or anywhere)")
        print("3. She can right-click and select 'Open' the first time")
        
    except subprocess.CalledProcessError:
        print("\n❌ Build failed. Check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
