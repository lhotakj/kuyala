#!/bin/bash
#
# This script sets up the local development environment for the Kuyala application.
# It creates a Python virtual environment and installs the required dependencies.
#

set -e  # Exit immediately if a command exits with a non-zero status.

VENV_DIR="venv"
PYTHON_CMD="python3"

# Check if Python 3 is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: '$PYTHON_CMD' is not installed or not in your PATH."
    echo "Please install Python 3.8 or higher."
    exit 1
fi

echo "Creating virtual environment in './$VENV_DIR'..."

# Create the virtual environment
$PYTHON_CMD -m venv $VENV_DIR

# Activate the virtual environment to install packages
# Note: The 'source' command only affects the current script's execution.
# The user must activate it manually in their own shell.
source "$VENV_DIR/bin/activate"

echo "Installing dependencies from requirements.txt..."

# Upgrade pip to the latest version
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

echo ""
echo "--------------------------------------------------"
echo "Setup complete!"
echo ""
echo "To activate the virtual environment in your shell, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "After activation, you can run the development server with:"
echo "  ./kuyala_development.sh"
echo "--------------------------------------------------"
