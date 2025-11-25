#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Get Version ---
# Run the Python script to get the application version.
# The script is expected to be in app/backend/get_version.py
# The command is run from the project root, so the path is relative to that.
echo "Fetching version..."
VERSION=$(cd ../app/backend && python3 ./get_version.py)

if [ -z "$VERSION" ]; then
    echo "Error: Could not retrieve version from get_version.py"
    exit 1
fi

echo "Building version: $VERSION"

# --- Docker Build ---
# Define the image name
IMAGE_NAME="kuyala"

# Build the Docker image and apply two tags:
# 1. The specific version (e.g., kuyala:0.1.0)
# 2. The 'latest' tag
docker build \
    --file ./dockerfile \
    -t "${IMAGE_NAME}:${VERSION}" \
    -t "${IMAGE_NAME}:latest" \
    ..

echo "Successfully built and tagged:"
echo "  - ${IMAGE_NAME}:${VERSION}"
echo "  - ${IMAGE_NAME}:latest"
