# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready ML pipeline for house price prediction using the California Housing dataset. The project features **three deployment modes**:

1. **Local Development** - Traditional FastAPI server with MLflow tracking
2. **Docker Deployment** - Multi-service orchestration with Docker Compose
3. **LocalStack AWS Simulation** - Full AWS infrastructure (Lambda, API Gateway, S3) running locally via LocalStack and AWS CDK

## Common Commands

### LocalStack Deployment (Primary Development Mode)

```bash
# Setup and start LocalStack
make setup                    # Install dependencies and configure LocalStack
make start-localstack        # Start LocalStack container
make status                  # Check LocalStack health

# Data pipeline and training
make data                    # Process training data -> data/processed/
make train                   # Train models and upload to S3

# Infrastructure deployment
cd infrastructure && npm install  # First time only
make bootstrap               # Bootstrap CDK for LocalStack (one-time setup)
make build-layer             # Build Lambda layer with ML dependencies
make deploy                  # Deploy CDK stack (Lambda, API Gateway, S3)
                             # Note: build-layer runs automatically before deploy

# Full deployment workflow
make deploy-all              # Runs data + train + deploy in sequence

# Testing and utilities
make test                    # Test API endpoints
make api-url                 # Get API Gateway URL
make health                  # Quick API health check
make s3-list                 # List S3 buckets
make s3-models              # List models in S3
make logs                   # View LocalStack logs

# Web interface
make web                     # Start web GUI at http://localhost:8080

# Cleanup
make stop-localstack        # Stop LocalStack
make clean                  # Remove all containers and data
```

### Local Development (FastAPI)

```bash
# Setup
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# Run pipeline
python src/data/data_pipeline.py    # Process data
python src/models/train.py          # Train with MLflow tracking
python src/api/main.py              # Start FastAPI server (port 8000)

# MLflow UI
mlflow ui --port 5000

# Testing
pytest tests/ -v
pytest tests/ -v --cov=src
```

### Docker Deployment

```bash
# Single container
docker build -f docker/Dockerfile -t house-price-api .
docker run -p 8000:8000 house-price-api

# Multi-service
docker-compose -f docker/docker-compose.yml up
docker-compose exec house-price-api python src/data/data_pipeline.py
docker-compose exec house-price-api python src/models/train.py
docker-compose restart house-price-api
```

### CDK Infrastructure (for LocalStack)

```bash
cd infrastructure

# Install dependencies (first time)
npm install

# Deploy to LocalStack
npm run deploy:local         # Uses cdklocal
npm run synth:local         # Synth stack locally
npm run destroy:local       # Destroy stack

# Deploy to real AWS (if needed)
npm run bootstrap           # One-time AWS setup
npm run deploy             # Deploy to AWS
```

## Architecture

### Dual Architecture Pattern

This project implements **two distinct architectures** that share the same ML models:

#### 1. Local/Docker Architecture (FastAPI)
```
Data Pipeline (src/data/data_pipeline.py)
    ↓
Model Training (src/models/train.py) → MLflow Tracking (mlruns/)
    ↓
Local Models (models/*.pkl)
    ↓
FastAPI Server (src/api/main.py) → Predictor (src/models/predict.py)
```

#### 2. LocalStack/AWS Architecture (Lambda)
```
Data Pipeline (src/data/data_pipeline.py)
    ↓
S3-Aware Training (src/models/train_s3.py) → Models to S3 (ml-model-artifacts bucket)
    ↓
CDK Infrastructure (infrastructure/lib/ml-pipeline-stack.ts)
    ↓
Lambda Function (src/lambda/inference.py) + ML Layer
    ↓
API Gateway → Lambda Integration
```

**Key Differences:**
- **Local**: Uses `src/models/train.py` → saves to `models/*.pkl` → loaded by `src/models/predict.py` (FastAPI)
- **LocalStack**: Uses `src/models/train_s3.py` → uploads to S3 → loaded by `src/lambda/inference.py` (Lambda)
- Both use the same data pipeline (`src/data/data_pipeline.py`) and processing logic

### Data Flow

1. **Data Processing**: `src/data/data_pipeline.py` loads California Housing dataset, performs feature engineering (rooms_per_household, bedrooms_per_room, population_per_household), scales features with StandardScaler, splits into train/test, and saves to `data/processed/processed_data.pkl` and `data/processed/scaler.pkl`

2. **Model Training**:
   - **Local**: `src/models/train.py` trains RandomForest and LinearRegression models, logs to MLflow (mlruns/), saves models to `models/*.pkl`
   - **S3**: `src/models/train_s3.py` trains same models but uploads to S3 bucket (ml-model-artifacts) for Lambda consumption

3. **Inference**:
   - **FastAPI** (`src/api/main.py`): Uses `HousePricePredictor` class from `src/models/predict.py` to load local models
   - **Lambda** (`src/lambda/inference.py`): Downloads models from S3 on cold start, caches in Lambda container

### Feature Engineering

All prediction paths apply the same feature transformations:
```python
rooms_per_household = AveRooms / AveOccup
bedrooms_per_room = AveBedrms / AveRooms
population_per_household = Population / AveOccup
```

These features are computed in:
- `src/data/data_pipeline.py` (training time)
- `src/models/predict.py` (FastAPI predictions)
- Implicitly expected in `src/lambda/inference.py` (Lambda predictions - scaler already includes engineered features)

## Infrastructure (LocalStack/AWS CDK)

**Stack**: `infrastructure/lib/ml-pipeline-stack.ts`

Components:
- **S3 Bucket** (`ml-model-artifacts`): Versioned bucket for model artifacts
- **Lambda Layer** (`MLDependenciesLayer`): ML dependencies (scikit-learn, pandas, numpy, joblib, boto3) built from `lambda-layers/ml-dependencies/`
  - Compatible with Python 3.9, 3.10, 3.11
  - Built using `make build-layer` or `./lambda-layers/build-layer.sh`
- **Lambda Function** (`ml-inference`):
  - Runtime: Python 3.9
  - Handler: `inference.handler`
  - Memory: 512MB
  - Timeout: 30s
  - Uses Lambda Layer for dependencies (no Docker required)
- **API Gateway**: REST API with CORS enabled, routes: `/health`, `/predict`, `/predict/confidence`

**Environment Variables** (Lambda):
- `MODEL_BUCKET`: ml-model-artifacts
- `MODEL_KEY`: models/house_price_random_forest_model.joblib
- `SCALER_KEY`: models/scaler.joblib
- `AWS_ENDPOINT_URL`: http://localhost:4566 (for LocalStack)
- `AWS_ENDPOINT_URL_S3`: http://localhost:4566 (for LocalStack S3 compatibility)

## API Endpoints

All deployment modes expose the same endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check with model status |
| POST | `/predict` | Single prediction |
| POST | `/predict/confidence` | Prediction with 95% confidence interval (RandomForest only) |

**Input Format** (POST requests):
```json
{
  "MedInc": 8.3252,
  "HouseAge": 41.0,
  "AveRooms": 6.984,
  "AveBedrms": 1.024,
  "Population": 322.0,
  "AveOccup": 2.555,
  "Latitude": 37.88,
  "Longitude": -122.23
}
```

**Note**: Lambda expects `{"features": [8.3252, 41.0, 6.984, ...]}` (array format) while FastAPI expects the JSON object format above.

## Testing

- `tests/test_api.py`: FastAPI integration tests using pytest-asyncio
- `scripts/test-api.py`: Standalone script to test Lambda/API Gateway endpoints
- `make test`: Runs test script against deployed LocalStack API

## Web Interface

A beautiful web GUI is available at `web/serve.py`:
- Start: `make web` or `python3 web/serve.py`
- Access: http://localhost:8080
- Features: Test connection, make predictions, view confidence intervals
- Works with both FastAPI and Lambda/API Gateway endpoints

## LocalStack Specifics

**LocalStack URL**: http://localhost:4566

**AWS CLI with LocalStack**:
```bash
# Use awslocal wrapper (installed via awscli-local package)
awslocal s3 ls
awslocal s3 ls s3://ml-model-artifacts/models/

# Or use regular aws with endpoint
aws --endpoint-url=http://localhost:4566 s3 ls
```

**Lambda Layer Building**:
Lambda layers must be built before deployment (automatically handled by `make deploy`):
```bash
make build-layer
# OR manually:
cd lambda-layers
./build-layer.sh  # Creates python/ package with ML dependencies
```

The layer structure:
```
lambda-layers/ml-dependencies/
├── requirements.txt          # Dependencies: boto3, joblib, numpy, scikit-learn, scipy
└── python/                   # Built packages (created by build-layer.sh)
    ├── sklearn/
    ├── numpy/
    ├── joblib/
    └── ... (other dependencies)
```

**CDK with LocalStack**:
Uses `cdklocal` wrapper (installed via aws-cdk-local npm package) which automatically sets endpoint URLs for LocalStack. The simplified Lambda function (non-Docker) is more compatible with LocalStack than the previous Docker-based approach.

## Important Notes

1. **Virtual Environment**: Always activate venv before running Python commands: `source venv/bin/activate`

2. **Data Pipeline First**: Always run `make data` before training. This generates `data/processed/processed_data.pkl` and `scaler.pkl` required by both training scripts.

3. **LocalStack Deployment Order**:
   - Start LocalStack (`make start-localstack`)
   - Bootstrap CDK (`make bootstrap`) - **one-time setup, creates CDK toolkit stack**
   - Process data (`make data`)
   - Train models (`make train`) - uploads to S3
   - Build Lambda Layer (`make build-layer`) - automatically runs with deploy
   - Deploy infrastructure (`make deploy`) - creates Lambda + Layer + API Gateway
   - Test API (`make test` or `make health`)

4. **Model Path Differences**:
   - Local models: `models/*.pkl` (older pickles) or `models/*.joblib`
   - S3 models: `s3://ml-model-artifacts/models/*.joblib`
   - Lambda expects specific keys: `house_price_random_forest_model.joblib` and `scaler.joblib`

5. **Port Conflicts**: Ensure ports 4566 (LocalStack), 8000 (FastAPI), 5000 (MLflow), 8080 (web GUI) are available.

6. **Docker Socket**: LocalStack requires Docker socket mount (`/var/run/docker.sock`) for Lambda execution.

7. **API Gateway URL**: Use `make api-url` to get the correct LocalStack API Gateway URL. Format: `http://localhost:4566/restapis/{api-id}/prod/_user_request_`

8. **CDK Environment Variables**: Newer versions of `cdklocal` require both `AWS_ENDPOINT_URL` and `AWS_ENDPOINT_URL_S3` to be set. These are automatically configured in `.env.localstack`, the deployment script, and Makefile.

9. **Lambda Architecture**: The project uses a **simple Lambda function with Lambda Layer** approach instead of Docker-based Lambda. This is more compatible with LocalStack and easier to debug. The Lambda Layer contains all ML dependencies (scikit-learn, pandas, numpy, joblib), and the Lambda function code (`src/lambda/inference.py`) is deployed separately. If you encounter deployment issues with LocalStack, use the hybrid approach:
   ```bash
   make start-localstack
   make data && make train    # Uploads models to LocalStack S3
   python src/api/main.py     # Run FastAPI locally (port 8000)
   make web                   # Web GUI (port 8080)
   ```
   For production AWS deployment, the full CDK stack (with Lambda) works perfectly.

## Development Workflow

**For local FastAPI development**:
```bash
source venv/bin/activate
python src/data/data_pipeline.py
python src/models/train.py
python src/api/main.py
# Test: curl http://localhost:8000/health
```

**For LocalStack/Lambda development**:
```bash
make start-localstack
make data
make train
cd infrastructure && npm run deploy:local
make test
```

**For Lambda function changes**:
After modifying `src/lambda/inference.py`, redeploy:
```bash
cd infrastructure && npm run deploy:local
```

**For infrastructure changes**:
After modifying `infrastructure/lib/ml-pipeline-stack.ts`:
```bash
cd infrastructure
npm run build  # Compile TypeScript
npm run deploy:local
```
