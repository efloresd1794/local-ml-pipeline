#!/bin/bash

# Setup script for LocalStack deployment
# This script prepares the environment and installs dependencies

set -e

echo "=========================================="
echo "LocalStack ML Pipeline Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Mac
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${YELLOW}Warning: This script is optimized for macOS${NC}"
fi

# 1. Check Docker
echo -e "\n${GREEN}[1/6] Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo "Docker found: $(docker --version)"

# 2. Check Python
echo -e "\n${GREEN}[2/6] Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install Python 3.9+"
    exit 1
fi
echo "Python found: $(python3 --version)"

# 3. Install Python dependencies
echo -e "\n${GREEN}[3/6] Installing Python dependencies...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install boto3 awscli-local[ver1]
echo "Python dependencies installed"

# 4. Check Node.js and npm
echo -e "\n${GREEN}[4/6] Checking Node.js and npm...${NC}"
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Please install Node.js from https://nodejs.org/"
    exit 1
fi
echo "Node.js found: $(node --version)"
echo "npm found: $(npm --version)"

# 5. Install AWS CDK and cdklocal
echo -e "\n${GREEN}[5/6] Installing AWS CDK dependencies...${NC}"
cd infrastructure
npm install
npm install -g aws-cdk-local aws-cdk
cd ..
echo "CDK dependencies installed"

# 6. Build Lambda layer
echo -e "\n${GREEN}[6/6] Building Lambda layer...${NC}"
cd lambda-layers
./build-layer.sh
cd ..
echo "Lambda layer built"

# Create necessary directories
mkdir -p data/processed models localstack-data

echo -e "\n${GREEN}=========================================="
echo "Setup completed successfully!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Start LocalStack: docker-compose -f docker-compose.localstack.yml up -d"
echo "2. Run data pipeline: source venv/bin/activate && python -m src.data.data_pipeline"
echo "3. Train and upload model: python -m src.models.train_s3"
echo "4. Deploy infrastructure: cd infrastructure && npm run deploy:local"
echo "5. Test the API: python scripts/test-api.py"
echo ""
