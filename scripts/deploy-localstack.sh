#!/bin/bash

# Full deployment script for LocalStack
# Runs the complete pipeline: data processing, training, and CDK deployment

set -e

# Load environment variables
if [ -f .env.localstack ]; then
    export $(cat .env.localstack | grep -v '^#' | xargs)
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "ML Pipeline LocalStack Deployment"
echo "==========================================${NC}"

# 1. Check if LocalStack is running
echo -e "\n${GREEN}[1/5] Checking LocalStack status...${NC}"
if ! docker ps | grep -q localstack-ml-pipeline; then
    echo -e "${YELLOW}LocalStack not running. Starting it now...${NC}"
    docker-compose -f docker-compose.localstack.yml up -d
    echo "Waiting for LocalStack to be ready..."
    sleep 10
else
    echo "LocalStack is running"
fi

# Verify LocalStack is ready
max_retries=30
retry_count=0
until curl -s http://localhost:4566/_localstack/health | grep -q '"s3": "available"' || [ $retry_count -eq $max_retries ]; do
    echo "Waiting for LocalStack to be ready... ($retry_count/$max_retries)"
    sleep 2
    retry_count=$((retry_count + 1))
done

if [ $retry_count -eq $max_retries ]; then
    echo -e "${YELLOW}Warning: LocalStack health check timed out, but continuing anyway${NC}"
else
    echo "LocalStack is ready!"
fi

# 2. Process data
echo -e "\n${GREEN}[2/5] Processing training data...${NC}"
if [ ! -f "data/processed/processed_data.pkl" ]; then
    source venv/bin/activate
    python -m src.data.data_pipeline
    echo "Data processing completed"
else
    echo "Processed data already exists (skipping)"
fi

# 3. Train model and upload to S3
echo -e "\n${GREEN}[3/5] Training ML model and uploading to S3...${NC}"
source venv/bin/activate
python -m src.models.train_s3
echo "Model training and upload completed"

# 4. Build Lambda layer (if not already built)
echo -e "\n${GREEN}[4/5] Checking Lambda layer...${NC}"
if [ ! -d "lambda-layers/ml-dependencies/python" ]; then
    echo "Building Lambda layer..."
    cd lambda-layers
    ./build-layer.sh
    cd ..
else
    echo "Lambda layer already built"
fi

# 5. Deploy CDK stack
echo -e "\n${GREEN}[5/5] Deploying CDK stack to LocalStack...${NC}"
cd infrastructure

# Bootstrap CDK (only needed once)
if ! aws --endpoint-url=http://localhost:4566 s3 ls | grep -q cdk; then
    echo "Bootstrapping CDK..."
    npm run bootstrap:local || echo "Bootstrap may have failed, continuing..."
fi

# Deploy the stack
echo "Deploying stack..."
npm run deploy:local

cd ..

# Get API endpoint
echo -e "\n${GREEN}=========================================="
echo "Deployment completed successfully!"
echo "==========================================${NC}"

# Try to get the API endpoint from LocalStack
echo -e "\n${BLUE}Retrieving API Gateway endpoint...${NC}"
API_ID=$(aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis --query 'items[0].id' --output text 2>/dev/null || echo "")

if [ -n "$API_ID" ] && [ "$API_ID" != "None" ]; then
    API_URL="http://localhost:4566/restapis/${API_ID}/prod/_user_request_"
    echo -e "${GREEN}API Gateway URL: ${API_URL}${NC}"
    echo ""
    echo "Test the API with:"
    echo "  Health check: curl ${API_URL}/health"
    echo ""
    echo "  Prediction:"
    echo "  curl -X POST ${API_URL}/predict \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"features\": [8.3252, 41, 6.984, 1.024, 322, 2.556, 37.88, -122.23]}'"
else
    echo -e "${YELLOW}Could not retrieve API Gateway ID automatically${NC}"
    echo "You can find the API endpoint with:"
    echo "  aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis"
fi

echo ""
echo -e "${BLUE}To view logs:${NC}"
echo "  docker logs -f localstack-ml-pipeline"
echo ""
echo -e "${BLUE}To test the API:${NC}"
echo "  python scripts/test-api.py"
echo ""
