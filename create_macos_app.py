#!/usr/bin/env python3
"""
Create a standalone macOS app bundle for Image Categorizer

This script packages the Flask-based image categorizer into a fully self-contained
macOS application that can be run without Python installation.
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

# Configuration
APP_NAME = "Image Categorizer"
APP_BUNDLE_ID = "com.styledstock.imagecategorizer"
APP_VERSION = "1.0.0"
APP_ICON = "ImageCategorizer.icns"  # Will be provided by user

def check_requirements():
    """Check if required tools are installed"""
    print("Checking requirements...")
    
    # Check for PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
    
    # Check for Pillow (for icon conversion if needed)
    try:
        import PIL
        print("✓ Pillow found")
    except ImportError:
        print("✗ Pillow not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        print("✓ Pillow installed")

def create_app_icon():
    """Create a placeholder icon or convert existing image to .icns"""
    icon_path = Path(APP_ICON)
    
    if icon_path.exists():
        print(f"✓ Using existing icon: {APP_ICON}")
        return str(icon_path)
    
    print("⚠ No .icns file found. Creating placeholder...")
    
    # Create a simple placeholder icon using Pillow
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a gradient background
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a gradient background
    for i in range(512):
        color = int(255 * (1 - i/512))
        draw.rectangle([(0, i), (512, i+1)], fill=(color, color, 255))
    
    # Add text
    try:
        # Try to use a system font
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
    except:
        font = ImageFont.load_default()
    
    # Draw "IC" in the center
    text = "IC"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((512 - text_width) // 2, (512 - text_height) // 2)
    draw.text(position, text, fill='white', font=font)
    
    # Save as PNG first
    png_path = "placeholder_icon.png"
    img.save(png_path)
    
    # Convert to .icns using iconutil (macOS built-in tool)
    iconset_path = "ImageCategorizer.iconset"
    os.makedirs(iconset_path, exist_ok=True)
    
    # Create different sizes required for .icns
    sizes = [16, 32, 64, 128, 256, 512]
    for size in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f"{iconset_path}/icon_{size}x{size}.png")
        # Also save @2x versions
        if size <= 256:
            resized2x = img.resize((size*2, size*2), Image.Resampling.LANCZOS)
            resized2x.save(f"{iconset_path}/icon_{size}x{size}@2x.png")
    
    # Convert iconset to icns
    try:
        subprocess.check_call(["iconutil", "-c", "icns", iconset_path])
        print("✓ Created placeholder icon: ImageCategorizer.icns")
        # Clean up
        os.remove(png_path)
        shutil.rmtree(iconset_path)
        return "ImageCategorizer.icns"
    except subprocess.CalledProcessError:
        print("✗ Failed to create .icns file")
        return None

def create_pyinstaller_spec():
    """Create PyInstaller spec file for macOS app bundle"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/static', 'app/static'),
        ('app/templates', 'app/templates'),
        ('openai_client.py', '.'),
        ('config', 'config'),  # Include config directory if it exists
    ],
    hiddenimports=[
        'flask',
        'openai',
        'pandas',
        'PIL',
        'PIL.Image',
        'requests',
        'httpx',
        'webbrowser',
        'keyring',
        'app.web_categorizer',
        'app.image_categorizer',
        'app.openai_fixed',
        'app.openai_wrapper',
        'openai_client',
        'werkzeug',
        'werkzeug.serving',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
        'certifi',
        'charset_normalizer',
        'idna',
        'urllib3',
        'numpy',
        'pytz',
        'dateutil',
        'openpyxl',
        'et_xmlfile',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'notebook'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{APP_ICON}',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{APP_NAME}',
)

app = BUNDLE(
    coll,
    name='{APP_NAME}.app',
    icon='{APP_ICON}',
    bundle_identifier='{APP_BUNDLE_ID}',
    info_plist={{
        'CFBundleName': '{APP_NAME}',
        'CFBundleDisplayName': '{APP_NAME}',
        'CFBundleExecutable': '{APP_NAME}',
        'CFBundleIdentifier': '{APP_BUNDLE_ID}',
        'CFBundleVersion': '{APP_VERSION}',
        'CFBundleShortVersionString': '{APP_VERSION}',
        'NSHumanReadableCopyright': '© 2025 Styled Stock',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15.0',
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'LSEnvironment': {{
            'MACOS_APP_BUNDLE': '1',
        }},
        'NSAppleEventsUsageDescription': 'This app needs to access the browser to display the web interface.',
        'NSAppTransportSecurity': {{
            'NSAllowsArbitraryLoads': True,
        }},
        'CFBundleDocumentTypes': [
            {{
                'CFBundleTypeName': 'Image Files',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': [
                    'public.jpeg',
                    'public.png',
                    'public.tiff',
                    'public.heic',
                    'com.compuserve.gif',
                    'com.microsoft.bmp',
                ],
            }}
        ],
    }},
)
'''
    
    spec_path = "ImageCategorizer.spec"
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    print(f"✓ Created PyInstaller spec file: {spec_path}")
    return spec_path

def build_app(spec_path):
    """Build the macOS app using PyInstaller"""
    print("\nBuilding macOS app...")
    
    # Clean previous builds
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Cleaned {dir_name} directory")
    
    # Run PyInstaller
    try:
        subprocess.check_call([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            spec_path
        ])
        print("✓ App built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False

def create_dmg():
    """Create a DMG file for easy distribution"""
    print("\nCreating DMG installer...")
    
    dmg_name = f"{APP_NAME}-{APP_VERSION}.dmg"
    app_path = f"dist/{APP_NAME}.app"
    
    if not os.path.exists(app_path):
        print("✗ App bundle not found")
        return
    
    # Create a temporary directory for DMG contents
    dmg_temp = "dmg_temp"
    if os.path.exists(dmg_temp):
        shutil.rmtree(dmg_temp)
    os.makedirs(dmg_temp)
    
    # Copy app to temp directory
    shutil.copytree(app_path, f"{dmg_temp}/{APP_NAME}.app")
    
    # Create a symbolic link to Applications folder
    os.symlink("/Applications", f"{dmg_temp}/Applications")
    
    # Create DMG
    try:
        # Remove old DMG if exists
        if os.path.exists(dmg_name):
            os.remove(dmg_name)
        
        subprocess.check_call([
            "hdiutil", "create",
            "-volname", APP_NAME,
            "-srcfolder", dmg_temp,
            "-ov",
            "-format", "UDZO",
            dmg_name
        ])
        print(f"✓ Created DMG: {dmg_name}")
        
        # Clean up
        shutil.rmtree(dmg_temp)
    except subprocess.CalledProcessError as e:
        print(f"✗ DMG creation failed: {e}")

def create_readme():
    """Create a simple readme for the packaged app"""
    readme_content = f"""# {APP_NAME} - macOS App

## Installation

1. Open the DMG file
2. Drag {APP_NAME} to your Applications folder
3. Double-click {APP_NAME} in Applications to run

## First Run

On first run, macOS may show a security warning. To open the app:

1. Right-click (or Control-click) on {APP_NAME}
2. Select "Open" from the menu
3. Click "Open" in the dialog that appears

## Usage

The app will automatically:
1. Start a local web server
2. Open your default web browser
3. Display the Image Categorizer interface

## Troubleshooting

If the app doesn't open:
- Make sure you've moved it to Applications folder
- Try the right-click → Open method described above
- Check that your macOS version is 10.15 or newer

## Support

For issues or questions, please contact support.
"""
    
    with open("README-macOS.txt", 'w') as f:
        f.write(readme_content)
    
    print("✓ Created README-macOS.txt")

def main():
    """Main packaging process"""
    print(f"=== {APP_NAME} macOS App Packager ===\n")
    
    # Check requirements
    check_requirements()
    
    # Create or verify icon
    icon_path = create_app_icon()
    if not icon_path:
        print("Warning: Proceeding without app icon")
    
    # Create spec file
    spec_path = create_pyinstaller_spec()
    
    # Build the app
    if build_app(spec_path):
        # Create DMG for distribution
        create_dmg()
        
        # Create readme
        create_readme()
        
        print(f"\n✅ {APP_NAME} has been successfully packaged!")
        print(f"📦 App location: dist/{APP_NAME}.app")
        print(f"💿 DMG installer: {APP_NAME}-{APP_VERSION}.dmg")
        print("\nTo use a custom icon:")
        print(f"1. Place your .icns file as '{APP_ICON}' in this directory")
        print("2. Run this script again")
    else:
        print("\n❌ Packaging failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
