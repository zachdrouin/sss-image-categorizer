# Building Image Categorizer macOS App

## Quick Build Instructions

1. **Build the app**:
   ```bash
   python3 create_macos_app.py
   ```

2. **Wait for completion** (this may take 2-5 minutes)

3. **Find the built app**:
   - The app will be in: `dist/Image Categorizer.app`

4. **Copy to your wife's Mac**:
   - Copy the entire `Image Categorizer.app` folder to her Applications folder
   - Or copy it anywhere on her Mac (Desktop, Documents, etc.)

## Running the App on Your Wife's Mac

1. **First time only**: 
   - Right-click on "Image Categorizer.app"
   - Select "Open" 
   - Click "Open" in the security dialog

2. **After that**: Just double-click to run normally

## What the App Does

When your wife runs the app:
1. It starts a local web server (invisible to her)
2. Opens her web browser automatically
3. Shows the Image Categorizer interface
4. She can start categorizing images immediately

## Requirements

- **For building** (your Mac): Python 3.7+
- **For running** (wife's Mac): macOS 10.15 or newer
- No Python installation needed on your wife's Mac

## Troubleshooting

If the app won't open on your wife's Mac:
1. Make sure she right-clicks and selects "Open" the first time
2. Check System Preferences > Security & Privacy if macOS blocks it
3. Ensure her macOS is version 10.15 or newer

## Notes

- The app is completely self-contained
- All settings and data stay on her local machine
- She'll need to enter the OpenAI API key when first using the app
