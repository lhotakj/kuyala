#!/bin/bash
# File: debug.sh
# Development startup script for Kuyala

set -e

echo "Starting Kuyala in development mode..."
echo "========================================"

# Set development environment variables
export FLASK_APP=app/app.py
export FLASK_ENV=development
export LOG_LEVEL=DEBUG

# Kubeconfig setup - try multiple locations
if [ -f "$HOME/.kube/config" ]; then
    export KUBECONFIG="$HOME/.kube/config"
    echo "Using kubeconfig from: $KUBECONFIG"
elif [ -n "$KUBECONFIG" ]; then
    echo "Using kubeconfig from env: $KUBECONFIG"
else
    echo "Warning: No kubeconfig found. Set KUBECONFIG env variable or ensure ~/.kube/config exists"
fi

echo "Environment:"
echo "  FLASK_APP: $FLASK_APP"
echo "  FLASK_ENV: $FLASK_ENV"
echo "  LOG_LEVEL: $LOG_LEVEL"
echo "  KUBECONFIG: $KUBECONFIG"
echo "========================================"
echo ""

# Check if flask is installed
if ! command -v flask &> /dev/null; then
    echo "Error: Flask is not installed. Run: pip install -r requirements.txt"
    exit 1
fi

# Start Flask development server
echo "Starting Flask development server..."
echo "Access the application at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

flask run --reload --host=0.0.0.0 --port=5000