# ML Pipeline with LocalStack Deployment

This repository contains a complete machine learning pipeline that trains a house price prediction model and deploys it as a serverless API using AWS Lambda, S3, and API Gateway on LocalStack.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ML Training Pipeline                       │
│                                                              │
│  California Housing Dataset                                 │
│         ↓                                                    │
│  Data Processing (data_pipeline.py)                         │
│         ↓                                                    │
│  Model Training (train_s3.py)                               │
│         ↓                                                    │
│  Upload to S3 (LocalStack)                                  │
│    - model.joblib                                           │
│    - scaler.joblib                                          │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              Infrastructure (CDK TypeScript)                 │
│                                                              │
│  ┌────────────┐    ┌────────────┐    ┌──────────────┐      │
│  │   S3       │───→│  Lambda    │←───│ API Gateway  │      │
│  │  Bucket    │    │ (Python)   │    │   REST API   │      │
│  └────────────┘    └────────────┘    └──────────────┘      │
│                           ↓                   ↓             │
│                    Model Inference       HTTP Endpoints     │
│                                           - GET /health      │
│                                           - POST /predict    │
│                                           - POST /predict/   │
│                                             confidence       │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                      LocalStack                              │
│  (Local AWS Cloud Emulator running on localhost:4566)       │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **ML Training**: Trains Random Forest and Linear Regression models on California Housing dataset
- **S3 Storage**: Stores trained models and scalers in S3 (LocalStack)
- **Lambda Inference**: Python Lambda function for real-time predictions
- **API Gateway**: REST API for accessing the ML service
- **CDK Infrastructure**: Infrastructure as Code using TypeScript CDK
- **LocalStack**: Complete local development environment (no AWS account needed!)
- **Mac M4 Optimized**: Configured for Apple Silicon architecture

## Prerequisites

### Required Software

1. **Docker Desktop** (for LocalStack)
   - Download: https://www.docker.com/products/docker-desktop
   - Ensure Docker is running before deployment

2. **Python 3.9+**
   ```bash
   python3 --version  # Should be 3.9 or higher
   ```

3. **Node.js 18+** (for CDK)
   ```bash
   node --version  # Should be 18 or higher
   npm --version
   ```

4. **Git**
   ```bash
   git --version
   ```

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd local-ml-pipeline

# Run the setup script
chmod +x scripts/setup-localstack.sh
./scripts/setup-localstack.sh
```

The setup script will:
- Check all prerequisites
- Create Python virtual environment
- Install Python dependencies
- Install CDK and Node.js dependencies
- Build Lambda layer with ML libraries

### 2. Start LocalStack

```bash
# Start LocalStack container
docker-compose -f docker-compose.localstack.yml up -d

# Check LocalStack status
docker ps | grep localstack

# View LocalStack logs
docker logs -f localstack-ml-pipeline
```

### 3. Train the Model

```bash
# Activate Python virtual environment
source venv/bin/activate

# Process data
python -m src.data.data_pipeline

# Train model and upload to S3 (LocalStack)
python -m src.models.train_s3
```

Expected output:
```
Starting ML model training pipeline with S3 storage
Loading processed data...
Configured S3 client for LocalStack
Created bucket ml-model-artifacts
Uploading scaler to S3...
Training RANDOM_FOREST model...
Model Metrics - RMSE: 0.5234, R2: 0.8123, MAE: 0.3456
Model saved to S3: s3://ml-model-artifacts/models/house_price_random_forest_model.joblib
```

### 4. Deploy Infrastructure

```bash
# Navigate to infrastructure directory
cd infrastructure

# Deploy to LocalStack
npm run deploy:local
```

This will:
- Bootstrap CDK (first time only)
- Create S3 bucket
- Package and deploy Lambda function
- Create Lambda Layer with ML dependencies
- Set up API Gateway
- Display API endpoint URL

### 5. Test the API

```bash
# Return to project root
cd ..

# Run test script
python scripts/test-api.py
```

Or test manually:

```bash
# Get API Gateway ID
aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis

# Set API URL (replace {api-id} with actual ID)
export API_URL="http://localhost:4566/restapis/{api-id}/prod/_user_request_"

# Test health check
curl $API_URL/health

# Test prediction
curl -X POST $API_URL/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "features": [8.3252, 41, 6.984, 1.024, 322, 2.556, 37.88, -122.23]
  }'

# Test prediction with confidence interval
curl -X POST $API_URL/predict/confidence \
  -H 'Content-Type: application/json' \
  -d '{
    "features": [8.3252, 41, 6.984, 1.024, 322, 2.556, 37.88, -122.23]
  }'
```

## API Endpoints

### GET /health

Health check endpoint to verify the service is running and the model is loaded.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "message": "ML Inference service is running"
}
```

### POST /predict

Make a single house price prediction.

**Request:**
```json
{
  "features": [8.3252, 41, 6.984, 1.024, 322, 2.556, 37.88, -122.23]
}
```

**Features (in order):**
1. MedInc: Median income in block group
2. HouseAge: Median house age in block group
3. AveRooms: Average number of rooms per household
4. AveBedrms: Average number of bedrooms per household
5. Population: Block group population
6. AveOccup: Average number of household members
7. Latitude: Block group latitude
8. Longitude: Block group longitude

**Response:**
```json
{
  "prediction": 4.526,
  "prediction_description": "Predicted median house value: $452,600.00",
  "features_received": [8.3252, 41, 6.984, 1.024, 322, 2.556, 37.88, -122.23]
}
```

### POST /predict/confidence

Get prediction with 95% confidence interval (only for ensemble models).

**Request:** Same as `/predict`

**Response:**
```json
{
  "prediction": 4.526,
  "prediction_description": "Predicted median house value: $452,600.00",
  "confidence_interval": {
    "lower_bound": 4.123,
    "upper_bound": 4.929,
    "std_dev": 0.205
  },
  "confidence_interval_description": "95% confidence: $412,300.00 - $492,900.00",
  "features_received": [8.3252, 41, 6.984, 1.024, 322, 2.556, 37.88, -122.23]
}
```

## Project Structure

```
local-ml-pipeline/
├── src/
│   ├── data/
│   │   └── data_pipeline.py       # Data processing
│   ├── models/
│   │   ├── train.py               # Original training (MLflow)
│   │   ├── train_s3.py           # Training with S3 upload
│   │   └── predict.py            # Local prediction
│   ├── lambda/
│   │   └── inference.py          # Lambda handler
│   └── api/
│       └── main.py               # Original FastAPI (for reference)
├── infrastructure/
│   ├── bin/
│   │   └── app.ts                # CDK app entry point
│   ├── lib/
│   │   └── ml-pipeline-stack.ts  # CDK stack definition
│   ├── package.json
│   ├── tsconfig.json
│   └── cdk.json
├── lambda-layers/
│   ├── ml-dependencies/
│   │   ├── requirements.txt      # Lambda layer dependencies
│   │   └── python/               # Built layer (generated)
│   └── build-layer.sh            # Layer build script
├── scripts/
│   ├── setup-localstack.sh       # Initial setup
│   ├── deploy-localstack.sh      # Full deployment
│   └── test-api.py               # API testing
├── docker-compose.localstack.yml  # LocalStack configuration
├── .env.localstack               # LocalStack environment variables
├── requirements.txt              # Python dependencies
└── README.localstack.md          # This file
```

## Development Workflow

### 1. Make Changes to Model

```bash
# Edit training code
vim src/models/train_s3.py

# Retrain and upload
source venv/bin/activate
python -m src.models.train_s3
```

### 2. Update Lambda Function

```bash
# Edit Lambda handler
vim src/lambda/inference.py

# Redeploy
cd infrastructure
npm run deploy:local
cd ..
```

### 3. Update Infrastructure

```bash
# Edit CDK stack
vim infrastructure/lib/ml-pipeline-stack.ts

# Rebuild and redeploy
cd infrastructure
npm run build
npm run deploy:local
cd ..
```

## Troubleshooting

### LocalStack not starting

```bash
# Check Docker is running
docker ps

# Restart LocalStack
docker-compose -f docker-compose.localstack.yml down
docker-compose -f docker-compose.localstack.yml up -d

# Check logs
docker logs localstack-ml-pipeline
```

### Lambda deployment fails

```bash
# Rebuild Lambda layer
cd lambda-layers
./build-layer.sh
cd ..

# Clear CDK cache
cd infrastructure
rm -rf cdk.out
npm run deploy:local
cd ..
```

### S3 bucket not found

```bash
# List S3 buckets in LocalStack
aws --endpoint-url=http://localhost:4566 s3 ls

# Create bucket manually
aws --endpoint-url=http://localhost:4566 s3 mb s3://ml-model-artifacts

# Re-upload model
source venv/bin/activate
python -m src.models.train_s3
```

### API Gateway returns 404

```bash
# Get API Gateway ID
aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis

# Check deployment
aws --endpoint-url=http://localhost:4566 apigateway get-deployments --rest-api-id {api-id}

# Redeploy CDK stack
cd infrastructure
npm run deploy:local
cd ..
```

## Environment Variables

### LocalStack Configuration (.env.localstack)

```bash
# AWS Endpoint
AWS_ENDPOINT_URL=http://localhost:4566
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# LocalStack Flag
USE_LOCALSTACK=true

# S3 Configuration
MODEL_BUCKET=ml-model-artifacts
MODEL_KEY=models/house_price_random_forest_model.joblib
SCALER_KEY=models/scaler.joblib
```

## Migration to AWS

To deploy to actual AWS (when ready):

1. **Update Environment Variables**
   ```bash
   export USE_LOCALSTACK=false
   export AWS_DEFAULT_REGION=us-east-1
   # Configure AWS credentials
   aws configure
   ```

2. **Deploy with CDK**
   ```bash
   cd infrastructure
   npm run bootstrap  # Bootstrap CDK in your AWS account
   npm run deploy     # Deploy to AWS
   cd ..
   ```

3. **Upload Model to AWS S3**
   ```bash
   source venv/bin/activate
   USE_LOCALSTACK=false python -m src.models.train_s3
   ```

## Performance Considerations

### Lambda Cold Start

First invocation may take 2-5 seconds due to:
- Loading scikit-learn libraries
- Downloading model from S3

Subsequent invocations use cached model (~100-300ms).

### Model Size

- RandomForest model: ~10-50 MB
- Lambda layer (ML libs): ~150-250 MB
- Total Lambda package: ~200-300 MB

### Optimization Tips

1. **Use Provisioned Concurrency** (for AWS) to avoid cold starts
2. **Smaller Model**: Use Linear Regression for faster load times
3. **Model Compression**: Use joblib compression
4. **Lambda Memory**: Increase to 1024 MB for faster execution

## Testing

### Unit Tests

```bash
source venv/bin/activate
pytest tests/
```

### Integration Tests

```bash
# Start LocalStack
docker-compose -f docker-compose.localstack.yml up -d

# Deploy
./scripts/deploy-localstack.sh

# Run tests
python scripts/test-api.py
```

## Monitoring and Logs

### View Lambda Logs

```bash
# LocalStack logs
docker logs -f localstack-ml-pipeline

# Lambda-specific logs (AWS)
aws logs tail /aws/lambda/ml-inference --follow
```

### CloudWatch Metrics (AWS only)

- Invocations
- Duration
- Error count
- Throttles

## Cost Estimation (AWS)

For AWS deployment (not applicable to LocalStack):

- **Lambda**: ~$0.20 per 1M requests + compute time
- **API Gateway**: ~$3.50 per 1M requests
- **S3**: ~$0.023 per GB/month
- **Total**: ~$5-20/month for moderate usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test with LocalStack
5. Submit pull request

## License

MIT License - see LICENSE file

## Support

For issues and questions:
- GitHub Issues: [Your repo URL]
- Documentation: This README
- LocalStack Docs: https://docs.localstack.cloud/

## Acknowledgments

- California Housing Dataset from scikit-learn
- LocalStack for local AWS emulation
- AWS CDK for infrastructure as code
