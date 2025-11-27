#!/bin/bash
# File: production.sh
# Production startup script for Kuyala using Gunicorn

set -e

echo "Starting Kuyala in production mode..."
echo "========================================"

# Set production environment variables
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
export GUNICORN_ACCESS_LOG=${GUNICORN_ACCESS_LOG:--}
export GUNICORN_ERROR_LOG=${GUNICORN_ERROR_LOG:--}

echo "Environment:"
echo "  LOG_LEVEL: $LOG_LEVEL"
echo "  GUNICORN_WORKERS: $GUNICORN_WORKERS"
echo "  KUBECONFIG: ${KUBECONFIG:-[in-cluster or default]}"
echo "========================================"
echo ""

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Error: Gunicorn is not installed. Run: pip install -r requirements.txt"
    exit 1
fi

# Start Gunicorn with gevent workers for SSE support
echo "Starting Gunicorn server..."
echo "Access the application at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

exec gunicorn \
    --config gunicorn_config.py \
    --bind 0.0.0.0:5000 \
    --workers $GUNICORN_WORKERS \
    --worker-class gevent \
    --worker-connections 1000 \
    --timeout 300 \
    --graceful-timeout 120 \
    --log-level $LOG_LEVEL \
    --preload \
    --access-logfile $GUNICORN_ACCESS_LOG \
    --error-logfile $GUNICORN_ERROR_LOG \
    app.app:app