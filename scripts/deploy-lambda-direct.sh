#!/bin/bash

# Direct Lambda deployment to LocalStack (bypasses CDK asset publishing)
# This script packages and deploys Lambda function without using CDK

set -e

# Set AWS credentials for LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

ENDPOINT="http://localhost:4566"
REGION="us-east-1"
BUCKET_NAME="ml-model-artifacts"
LAMBDA_NAME="ml-inference"
LAMBDA_ROLE="arn:aws:iam::000000000000:role/lambda-role"
DEPLOYMENT_PACKAGE="lambda-deployment.zip"

echo "================================================"
echo "Direct Lambda Deployment to LocalStack"
echo "================================================"
echo ""

# Check if LocalStack is running
echo "🔍 Checking LocalStack status..."
if ! curl -s "${ENDPOINT}/_localstack/health" > /dev/null; then
    echo "❌ LocalStack is not running! Start it with: make start-localstack"
    exit 1
fi
echo "✅ LocalStack is running"
echo ""

# Step 1: Create S3 bucket if it doesn't exist
echo "📦 Creating S3 bucket..."
aws --endpoint-url="${ENDPOINT}" s3 mb "s3://${BUCKET_NAME}" 2>/dev/null || echo "Bucket already exists"
echo ""

# Step 2: Check if models exist in S3
echo "🔍 Checking for models in S3..."
# Check specifically for the random forest model
if aws --endpoint-url="${ENDPOINT}" s3 ls "s3://${BUCKET_NAME}/models/house_price_random_forest_model.joblib" >/dev/null 2>&1; then
    echo "✅ Models found in S3"
    # List the models
    aws --endpoint-url="${ENDPOINT}" s3 ls "s3://${BUCKET_NAME}/models/" 2>/dev/null | grep -E '\.(joblib|pkl)$' || true
else
    echo "⚠️  No models found in S3. Please run: make train"
    echo "   This will train the model and upload to S3"
    echo ""
    echo "   Checking S3 contents:"
    aws --endpoint-url="${ENDPOINT}" s3 ls "s3://${BUCKET_NAME}/models/" 2>/dev/null || echo "   (models/ directory not found)"
    exit 1
fi
echo ""

# Step 3: Create lightweight Lambda deployment package
echo "📦 Creating Lambda deployment package..."
cd "$(dirname "$0")/.."

# Clean up old package
rm -f "${DEPLOYMENT_PACKAGE}"

# Create a temporary directory for packaging
TEMP_DIR=$(mktemp -d)
echo "   Using temp directory: ${TEMP_DIR}"

# Copy Lambda function code
cp src/lambda/inference.py "${TEMP_DIR}/"

# Install dependencies using Docker for correct architecture
echo "   Installing dependencies using Docker (for x86_64 compatibility)..."
echo "   This ensures packages work in Lambda regardless of your Mac architecture"

# Use Docker to install packages in Linux x86_64 environment
docker run --rm --platform linux/amd64 \
    --entrypoint "" \
    -v "${TEMP_DIR}:/var/task" \
    -w /var/task \
    public.ecr.aws/lambda/python:3.9 \
    pip install \
        boto3 \
        numpy \
        scikit-learn \
        joblib \
        --target /var/task \
        --no-cache-dir \
        --quiet

if [ $? -ne 0 ]; then
    echo "   ❌ Docker build failed. Make sure Docker is running."
    echo "   Alternative: Install packages locally (may not work in Lambda)"
    pip install --target "${TEMP_DIR}" \
        boto3 numpy scikit-learn joblib \
        --platform manylinux2014_x86_64 \
        --only-binary=:all: \
        --no-cache-dir --quiet 2>/dev/null || {
        echo "   ⚠️  Using local architecture - this may cause issues in Lambda"
        pip install --target "${TEMP_DIR}" \
            boto3 numpy scikit-learn joblib \
            --no-cache-dir --quiet
    }
fi

# Clean up unnecessary files to reduce size
echo "   Cleaning up package..."
find "${TEMP_DIR}" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "${TEMP_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${TEMP_DIR}" -name "*.pyc" -delete 2>/dev/null || true
find "${TEMP_DIR}" -name "*.pyo" -delete 2>/dev/null || true
find "${TEMP_DIR}" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

# Create ZIP file
echo "   Creating deployment package..."
cd "${TEMP_DIR}"
zip -r -q "${OLDPWD}/${DEPLOYMENT_PACKAGE}" .
cd "${OLDPWD}"

# Clean up temp directory
rm -rf "${TEMP_DIR}"

PACKAGE_SIZE=$(du -h "${DEPLOYMENT_PACKAGE}" | cut -f1)
echo "   ✅ Package created: ${DEPLOYMENT_PACKAGE} (${PACKAGE_SIZE})"
echo ""

# Step 4: Upload deployment package to S3
echo "📤 Uploading deployment package to S3..."
aws --endpoint-url="${ENDPOINT}" s3 cp \
    "${DEPLOYMENT_PACKAGE}" \
    "s3://${BUCKET_NAME}/lambda/${DEPLOYMENT_PACKAGE}"
echo "   ✅ Uploaded to s3://${BUCKET_NAME}/lambda/${DEPLOYMENT_PACKAGE}"
echo ""

# Step 5: Create IAM role for Lambda (if it doesn't exist)
echo "🔐 Creating IAM role for Lambda..."
aws --endpoint-url="${ENDPOINT}" iam create-role \
    --role-name lambda-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }' 2>/dev/null || echo "   Role already exists"

# Attach policies
aws --endpoint-url="${ENDPOINT}" iam attach-role-policy \
    --role-name lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AWSLambdaExecute 2>/dev/null || true
echo "   ✅ IAM role configured"
echo ""

# Step 6: Delete existing Lambda function (if it exists)
echo "🗑️  Removing existing Lambda function (if any)..."
aws --endpoint-url="${ENDPOINT}" lambda delete-function \
    --function-name "${LAMBDA_NAME}" 2>/dev/null || echo "   No existing function to delete"
echo ""

# Step 7: Create Lambda function
echo "🚀 Creating Lambda function..."
# Note: Lambda runs in Docker, so use host.docker.internal instead of localhost
LAMBDA_ENDPOINT="http://host.docker.internal:4566"
aws --endpoint-url="${ENDPOINT}" lambda create-function \
    --function-name "${LAMBDA_NAME}" \
    --runtime python3.9 \
    --role "${LAMBDA_ROLE}" \
    --handler inference.handler \
    --code "S3Bucket=${BUCKET_NAME},S3Key=lambda/${DEPLOYMENT_PACKAGE}" \
    --timeout 30 \
    --memory-size 512 \
    --environment "Variables={
        MODEL_BUCKET=${BUCKET_NAME},
        MODEL_KEY=models/house_price_random_forest_model.joblib,
        SCALER_KEY=models/scaler.joblib,
        AWS_ENDPOINT_URL=${LAMBDA_ENDPOINT},
        AWS_ENDPOINT_URL_S3=${LAMBDA_ENDPOINT}
    }" \
    --region "${REGION}"

echo ""
echo "   ✅ Lambda function created successfully!"
echo ""

# Step 8: Create or update API Gateway
echo "🌐 Setting up API Gateway..."

# Check if API already exists
API_ID=$(aws --endpoint-url="${ENDPOINT}" apigateway get-rest-apis \
    --query "items[?name=='ML-Inference-API'].id" \
    --output text 2>/dev/null || echo "")

if [ -z "$API_ID" ] || [ "$API_ID" == "None" ]; then
    echo "   Creating new API Gateway..."
    API_ID=$(aws --endpoint-url="${ENDPOINT}" apigateway create-rest-api \
        --name "ML-Inference-API" \
        --description "ML Inference API" \
        --query 'id' \
        --output text)
    echo "   ✅ API created: ${API_ID}"
else
    echo "   ✅ Using existing API: ${API_ID}"
fi

# Get root resource ID
ROOT_ID=$(aws --endpoint-url="${ENDPOINT}" apigateway get-resources \
    --rest-api-id "${API_ID}" \
    --query 'items[?path==`/`].id' \
    --output text)

echo "   Root resource ID: ${ROOT_ID}"

# Create /health resource
HEALTH_RESOURCE_ID=$(aws --endpoint-url="${ENDPOINT}" apigateway get-resources \
    --rest-api-id "${API_ID}" \
    --query "items[?path=='/health'].id" \
    --output text 2>/dev/null || echo "")

if [ -z "$HEALTH_RESOURCE_ID" ] || [ "$HEALTH_RESOURCE_ID" == "None" ]; then
    HEALTH_RESOURCE_ID=$(aws --endpoint-url="${ENDPOINT}" apigateway create-resource \
        --rest-api-id "${API_ID}" \
        --parent-id "${ROOT_ID}" \
        --path-part "health" \
        --query 'id' \
        --output text)
fi

# Create /predict resource
PREDICT_RESOURCE_ID=$(aws --endpoint-url="${ENDPOINT}" apigateway get-resources \
    --rest-api-id "${API_ID}" \
    --query "items[?path=='/predict'].id" \
    --output text 2>/dev/null || echo "")

if [ -z "$PREDICT_RESOURCE_ID" ] || [ "$PREDICT_RESOURCE_ID" == "None" ]; then
    PREDICT_RESOURCE_ID=$(aws --endpoint-url="${ENDPOINT}" apigateway create-resource \
        --rest-api-id "${API_ID}" \
        --parent-id "${ROOT_ID}" \
        --path-part "predict" \
        --query 'id' \
        --output text)
fi

# Add methods (GET /health, POST /predict) with CORS support
for RESOURCE in "${HEALTH_RESOURCE_ID}:GET" "${PREDICT_RESOURCE_ID}:POST"; do
    RESOURCE_ID=$(echo "$RESOURCE" | cut -d: -f1)
    METHOD=$(echo "$RESOURCE" | cut -d: -f2)

    # Add main method
    aws --endpoint-url="${ENDPOINT}" apigateway put-method \
        --rest-api-id "${API_ID}" \
        --resource-id "${RESOURCE_ID}" \
        --http-method "${METHOD}" \
        --authorization-type NONE 2>/dev/null || true

    aws --endpoint-url="${ENDPOINT}" apigateway put-integration \
        --rest-api-id "${API_ID}" \
        --resource-id "${RESOURCE_ID}" \
        --http-method "${METHOD}" \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:000000000000:function:${LAMBDA_NAME}/invocations" 2>/dev/null || true

    # Add OPTIONS method for CORS preflight
    aws --endpoint-url="${ENDPOINT}" apigateway put-method \
        --rest-api-id "${API_ID}" \
        --resource-id "${RESOURCE_ID}" \
        --http-method OPTIONS \
        --authorization-type NONE 2>/dev/null || true

    aws --endpoint-url="${ENDPOINT}" apigateway put-integration \
        --rest-api-id "${API_ID}" \
        --resource-id "${RESOURCE_ID}" \
        --http-method OPTIONS \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:000000000000:function:${LAMBDA_NAME}/invocations" 2>/dev/null || true
done

# Deploy API
aws --endpoint-url="${ENDPOINT}" apigateway create-deployment \
    --rest-api-id "${API_ID}" \
    --stage-name prod 2>/dev/null || true

echo "   ✅ API Gateway configured"
echo ""

# Step 9: Add Lambda permission for API Gateway
echo "🔓 Adding Lambda invoke permission for API Gateway..."
aws --endpoint-url="${ENDPOINT}" lambda add-permission \
    --function-name "${LAMBDA_NAME}" \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:000000000000:${API_ID}/*/*" 2>/dev/null || true
echo "   ✅ Permission added"
echo ""

# Clean up deployment package
rm -f "${DEPLOYMENT_PACKAGE}"

echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "API Gateway URL:"
echo "   ${ENDPOINT}/restapis/${API_ID}/prod/_user_request_"
echo ""
echo "Test endpoints:"
echo "   Health: curl ${ENDPOINT}/restapis/${API_ID}/prod/_user_request_/health"
echo "   Predict: curl -X POST ${ENDPOINT}/restapis/${API_ID}/prod/_user_request_/predict \\"
echo "            -H 'Content-Type: application/json' \\"
echo "            -d '{\"features\": [8.3252, 41.0, 6.984, 1.024, 322.0, 2.555, 37.88, -122.23]}'"
echo ""