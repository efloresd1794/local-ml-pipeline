#!/bin/bash

# Script to build Lambda layer for ML dependencies
# This creates a layer compatible with AWS Lambda Python 3.9 runtime

set -e

LAYER_DIR="ml-dependencies"
BUILD_DIR="${LAYER_DIR}/python"

echo "Building Lambda layer for ML dependencies..."

# Clean previous builds
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# Install dependencies
# Note: For production on AWS, you'd want to build this in a Lambda-compatible environment
# For LocalStack testing, this should work fine
pip install -r "${LAYER_DIR}/requirements.txt" -t "${BUILD_DIR}" --upgrade

# Clean up unnecessary files to reduce size
echo "Cleaning up unnecessary files..."
find "${BUILD_DIR}" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}" -name "*.pyc" -delete 2>/dev/null || true
find "${BUILD_DIR}" -name "*.pyo" -delete 2>/dev/null || true
find "${BUILD_DIR}" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

echo "Lambda layer built successfully at ${BUILD_DIR}"
echo "Layer size:"
du -sh "${BUILD_DIR}"
