#!/bin/bash

# ImageCategorizer Launcher
# Created for Elle Drouin

# Display welcome message with styled text
echo -e "\033[1;35m✨ Image Categorizer ✨\033[0m"
echo -e "\033[0;36mA tool to easily categorize your images\033[0m"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$SCRIPT_DIR/app"

echo -e "\033[0;32mStarting application...\033[0m"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "\033[1;31mError: Python 3 is not installed.\033[0m"
    echo "Please install Python 3 from https://www.python.org/downloads/"
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Check if virtualenv exists, if not create one
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up virtual environment (this will only happen once)..."
    python3 -m venv "$VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Check if requirements are installed
if [ ! -f "$VENV_DIR/.requirements_installed" ]; then
    echo "Installing required packages (this will only happen once)..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
    touch "$VENV_DIR/.requirements_installed"
fi

# Navigate to the application directory
cd "$APP_DIR"

# Run the application
python web_categorizer.py

# Keep the window open after the app exits
echo ""
echo -e "\033[1;31mApplication has been closed.\033[0m"
echo "Press any key to exit this window..."
read -n 1
