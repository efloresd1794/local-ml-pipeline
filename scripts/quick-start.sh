#!/bin/bash

# Quick Start Script - Working LocalStack + FastAPI Setup
# This script demonstrates the working development workflow

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "ML Pipeline - Quick Start (LocalStack + FastAPI)"
echo "==========================================${NC}"

# 1. Check if LocalStack is running
echo -e "\n${GREEN}[1/4] Checking LocalStack status...${NC}"
if ! docker ps | grep -q localstack-ml-pipeline; then
    echo -e "${YELLOW}LocalStack not running. Starting it now...${NC}"
    docker-compose -f docker-compose.localstack.yml up -d
    echo "Waiting for LocalStack to be ready..."
    sleep 10
else
    echo "LocalStack is running ✓"
fi

# 2. Process data (if needed)
echo -e "\n${GREEN}[2/4] Processing training data...${NC}"
if [ ! -f "data/processed/processed_data.pkl" ]; then
    source venv/bin/activate
    python -m src.data.data_pipeline
    echo "Data processing completed ✓"
else
    echo "Processed data already exists ✓"
fi

# 3. Train model and upload to LocalStack S3
echo -e "\n${GREEN}[3/4] Training ML model and uploading to LocalStack S3...${NC}"
source venv/bin/activate
python -m src.models.train_s3
echo "Model training and upload completed ✓"

# 4. Instructions for running the API
echo -e "\n${GREEN}[4/4] Ready to run the API!${NC}"
echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}✓ LocalStack is running (port 4566)${NC}"
echo -e "${GREEN}✓ Models uploaded to S3 (ml-model-artifacts bucket)${NC}"
echo -e "${GREEN}✓ Ready to start API server${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo -e "1. ${BLUE}Start the FastAPI server:${NC}"
echo "   source venv/bin/activate"
echo "   python src/api/main.py"
echo ""
echo -e "2. ${BLUE}In a new terminal, start the web GUI:${NC}"
echo "   cd web"
echo "   python -m http.server 8080"
echo ""
echo -e "3. ${BLUE}Test the API:${NC}"
echo "   curl http://localhost:8000/health"
echo ""
echo "   curl -X POST http://localhost:8000/predict \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"features\": [8.3252, 41, 6.984, 1.024, 322, 2.556, 37.88, -122.23]}'"
echo ""
echo -e "4. ${BLUE}Open the web GUI:${NC}"
echo "   http://localhost:8080"
echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${YELLOW}Note:${NC} CDK Lambda deployment to LocalStack is not supported due to"
echo "LocalStack's IAM/STS limitations with asset publishing. This hybrid"
echo "approach (S3 in LocalStack, API in FastAPI) provides the same"
echo "functionality for development and testing."
echo ""
echo -e "${GREEN}For production AWS deployment, use:${NC}"
echo "   cd infrastructure && npm run deploy"
echo ""
