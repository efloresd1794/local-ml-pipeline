#!/bin/bash

# Build Lambda layer using Docker with Python 3.9 (same as Lambda runtime)
# This ensures compatibility between the layer and Lambda execution environment

set -e

LAYER_DIR="ml-dependencies"
BUILD_DIR="${LAYER_DIR}/python"

echo "Building Lambda layer using Python 3.9 Docker image..."

# Clean previous builds
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# Build using Python 3.9 Docker image (compatible with Lambda Python 3.9)
docker run --rm \
  -v "$(pwd)/${LAYER_DIR}":/var/task \
  -w /var/task \
  python:3.9-slim \
  pip install -r requirements.txt -t python --upgrade --no-cache-dir

# Clean up unnecessary files to reduce size
echo "Cleaning up unnecessary files..."
find "${BUILD_DIR}" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}" -name "*.pyc" -delete 2>/dev/null || true
find "${BUILD_DIR}" -name "*.pyo" -delete 2>/dev/null || true
find "${BUILD_DIR}" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

echo "Lambda layer built successfully using Python 3.9!"
echo "Layer size:"
du -sh "${BUILD_DIR}"

echo ""
echo "✓ Layer is now compatible with Lambda Python 3.9 runtime"
