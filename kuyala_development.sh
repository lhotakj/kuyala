#!/bin/bash
#
# Development startup script for Kuyala.
# This script should be run after activating the virtual environment.
#

set -e

echo "Starting Kuyala in development mode..."
echo "========================================"

# --- Environment Setup ---
# Set Flask-specific variables for development mode
export FLASK_APP="app/app.py"
export FLASK_ENV="development"

# Set application-specific environment variables
export LOG_LEVEL=${LOG_LEVEL:-"DEBUG"}

# Kubeconfig setup - check for the file and export the path
# The application will handle the logic of finding the config,
# but we can provide a default here for clarity.
if [ -z "$KUBECONFIG" ] && [ -f "$HOME/.kube/config" ]; then
    export KUBECONFIG="$HOME/.kube/config"
fi

echo "Environment:"
echo "  - FLASK_APP: $FLASK_APP"
echo "  - FLASK_ENV: $FLASK_ENV"
echo "  - LOG_LEVEL: $LOG_LEVEL"
if [ -n "$KUBECONFIG" ]; then
    echo "  - KUBECONFIG: $KUBECONFIG"
else
    echo "  - KUBECONFIG: Not set, will use in-cluster or default logic."
fi
echo "========================================"
echo ""

# --- Pre-flight Check ---
# Check if flask is available in the current environment
if ! command -v flask &> /dev/null; then
    echo "Error: 'flask' command not found."
    echo "Have you activated the virtual environment? Run: source venv/bin/activate"
    exit 1
fi

# --- Run Application ---
echo "Starting Flask development server with auto-reload..."
echo "Access the application at: http://localhost:5000"
echo "Press Ctrl+C to stop."
echo ""

# Start the Flask development server
# --reload: Automatically reloads the server when code changes are detected
# --host=0.0.0.0: Makes the server accessible from outside the container/VM
flask run --reload --host=0.0.0.0 --port=5000
