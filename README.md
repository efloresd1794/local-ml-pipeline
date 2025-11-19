# 🏠 House Price Prediction ML Pipeline

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com/)
[![MLflow](https://img.shields.io/badge/MLflow-2.8%2B-orange)](https://mlflow.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue)](https://www.docker.com/)
[![LocalStack](https://img.shields.io/badge/LocalStack-AWS%20Local-purple)](https://localstack.cloud/)
[![AWS CDK](https://img.shields.io/badge/AWS%20CDK-TypeScript-orange)](https://aws.amazon.com/cdk/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready end-to-end machine learning pipeline for house price prediction, featuring **LocalStack AWS simulation**, MLflow experiment tracking, Docker deployment, FastAPI serving, and a beautiful web interface—all running locally without AWS costs!

## 🎯 **Project Overview**

This project demonstrates enterprise-level ML engineering practices by implementing a complete pipeline from data ingestion to model deployment. Built with California Housing dataset, it showcases modern MLOps workflows including experiment tracking, model versioning, containerized deployment, and **local AWS simulation with LocalStack**—enabling full cloud development without AWS costs!

### **Key Features**

- 🔄 **Automated Data Pipeline** - Preprocessing, feature engineering, and data validation
- 🧪 **MLflow Integration** - Experiment tracking, model registry, and versioning
- 🚀 **FastAPI Service** - High-performance REST API with automatic documentation
- ☁️ **LocalStack AWS Simulation** - Lambda, S3, API Gateway running locally via AWS CDK
- 🎨 **Beautiful Web Interface** - Modern GUI for testing predictions with confidence intervals
- 🐳 **Docker Deployment** - Containerized application with multi-service orchestration
- 🧪 **Comprehensive Testing** - Unit tests, integration tests, and API validation
- ⚙️ **CI/CD Pipeline** - Automated testing and deployment with GitHub Actions
- 📊 **Model Monitoring** - Prediction confidence intervals and model performance tracking
- 🛠️ **Make Commands** - Simple commands for common tasks (make web, make deploy, etc.)

## 🏗️ **Architecture**

This project supports **three deployment modes** that share the same ML models:

### **🔷 Mode 1: LocalStack AWS Simulation (Recommended)**
```
Data Pipeline → S3-Aware Training → S3 (LocalStack)
                                    ↓
                           Lambda Function + ML Layer
                                    ↓
                              API Gateway (REST)
                                    ↓
                          Web GUI (localhost:8080)
```

### **🔷 Mode 2: Local FastAPI Development**
```
Data Pipeline → MLflow Training → Local Models (.pkl)
                                    ↓
                              FastAPI Server
                                    ↓
                          Web GUI (localhost:8080)
```

### **🔷 Mode 3: Docker Compose Orchestration**
```
Data Pipeline → MLflow Training → Models in Container
                                    ↓
                        FastAPI + MLflow + PostgreSQL
                                    ↓
                         Docker Network (localhost:8000)
```

## 📁 **Project Structure**

```
local-ml-pipeline/
├── 📂 src/
│   ├── 📂 data/
│   │   └── 📄 data_pipeline.py        # Data processing and feature engineering
│   ├── 📂 models/
│   │   ├── 📄 train.py                # Model training with MLflow tracking (local)
│   │   ├── 📄 train_s3.py             # Model training with S3 upload (LocalStack)
│   │   └── 📄 predict.py              # Prediction service for FastAPI
│   ├── 📂 lambda/
│   │   └── 📄 inference.py            # Lambda handler for serverless inference
│   └── 📂 api/
│       └── 📄 main.py                 # FastAPI application and endpoints
├── 📂 infrastructure/
│   ├── 📂 bin/
│   │   └── 📄 app.ts                  # CDK app entry point
│   ├── 📂 lib/
│   │   └── 📄 ml-pipeline-stack.ts    # CDK stack definition (Lambda, S3, API Gateway)
│   ├── 📄 package.json                # Node.js dependencies
│   └── 📄 cdk.json                    # CDK configuration
├── 📂 lambda-layers/
│   ├── 📂 ml-dependencies/            # Lambda layer with scikit-learn, pandas, etc.
│   └── 📄 build-layer.sh              # Script to build Lambda layer
├── 📂 web/
│   ├── 📄 index.html                  # Beautiful web GUI for predictions
│   ├── 📄 serve.py                    # Python web server with CORS
│   └── 📄 README.md                   # Web GUI documentation
├── 📂 scripts/
│   ├── 📄 setup-localstack.sh         # Initial setup script
│   ├── 📄 deploy-localstack.sh        # Full deployment script
│   ├── 📄 test-api.py                 # API testing script
│   └── 📄 quick-start.sh              # Quick start workflow
├── 📂 tests/
│   └── 📄 test_api.py                 # API integration tests
├── 📂 docker/
│   ├── 📄 Dockerfile                  # Container configuration
│   └── 📄 docker-compose.yml          # Multi-service orchestration
├── 📂 data/
│   ├── 📂 raw/                        # Raw dataset storage
│   └── 📂 processed/                  # Processed features and scalers
├── 📂 models/                         # Trained model artifacts (local)
├── 📂 mlruns/                         # MLflow experiment tracking
├── 📄 docker-compose.localstack.yml   # LocalStack configuration
├── 📄 Makefile                        # Common commands (make web, make deploy, etc.)
├── 📄 requirements.txt                # Python dependencies
├── 📄 setup.py                        # Package configuration
├── 📄 CLAUDE.md                       # Development guide for Claude Code
├── 📄 README.md                       # This file
└── 📄 README.localstack.md            # Detailed LocalStack documentation
```

## 🚀 **Quick Start**

Choose your preferred deployment mode:

### **⚡ Option 1: Quick Start (Recommended)**

The fastest way to get up and running with LocalStack:

```bash
# One-command setup
make quick-start

# In a new terminal, start the web interface
make web
```

Then open http://localhost:8080 in your browser to interact with the API! 🎉

---

### **☁️ Option 2: LocalStack AWS Simulation**

Full AWS infrastructure running locally:

#### **Prerequisites**
- Python 3.9+
- Docker Desktop (running)
- Node.js 18+
- Git

#### **Setup & Deploy**

```bash
# Step 1: Setup (first time only)
make setup

# Step 2: Start LocalStack
make start-localstack

# Step 3: Process data and train model
make data
make train

# Step 4: Deploy infrastructure (Lambda, API Gateway, S3)
make deploy

# Step 5: Test the API
make test

# Step 6: Start web interface
make web
```

**Available Make Commands:**
```bash
make help              # Show all available commands
make status            # Check LocalStack health
make api-url           # Get API Gateway URL
make health            # Quick API health check
make s3-models         # List models in S3
make logs              # View LocalStack logs
make clean             # Clean up everything
```

---

### **🚀 Option 3: Local FastAPI Development**

Traditional FastAPI server with MLflow tracking:

```bash
# Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# Run pipeline
python src/data/data_pipeline.py
python src/models/train.py
python src/api/main.py

# In another terminal, start web interface
make web
```

**Services:**
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MLflow UI**: `mlflow ui --port 5000` → http://localhost:5000
- **Web GUI**: http://localhost:8080

---

## 🎨 **Web Interface**

A beautiful, modern web GUI for interacting with the ML API!

### **Features**

- 🎯 **User-Friendly Interface** - Clean, intuitive design with gradient backgrounds
- 📊 **Real-time Predictions** - Instant predictions with visual feedback
- 📈 **Confidence Intervals** - 95% confidence interval display for RandomForest models
- 🔄 **Quick Presets** - Pre-filled examples (Luxury SF, Average LA, Budget Valley)
- ✅ **Health Check** - Test API connectivity before making predictions
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

### **Usage**

```bash
# Start the web server
make web

# Or manually
python web/serve.py
```

Then open **http://localhost:8080** in your browser!

### **How It Works**

1. **Configure API**: Enter your API Gateway URL (from `make api-url`) or use `http://localhost:8000` for local FastAPI
2. **Test Connection**: Click "Test Connection" to verify API is responding
3. **Make Predictions**:
   - Use quick presets or enter custom values
   - Click "Predict Price" for simple prediction
   - Click "Predict with Confidence Interval" for detailed results with uncertainty bounds

### **Screenshots**

The interface includes:
- Input fields for all 8 California Housing features with tooltips
- Quick preset buttons for common scenarios
- Real-time prediction results with formatted currency
- Confidence interval visualization (when applicable)
- Error handling and loading states

See [web/README.md](web/README.md) for detailed documentation.

---

## 🐳 **Docker Deployment**

### **Single Container**
```bash
# Build image
docker build -f docker/Dockerfile -t house-price-api .

# Run container
docker run -p 8000:8000 house-price-api
```

### **Multi-Service with Docker Compose**
```bash
# Start all services (API + MLflow Server + PostgreSQL)
docker-compose -f docker/docker-compose.yml up

# Run pipeline inside container
docker-compose exec house-price-api python src/data/data_pipeline.py
docker-compose exec house-price-api python src/models/train.py

# Restart API to load trained models
docker-compose restart house-price-api
```

**Services:**
- **API**: http://localhost:8000
- **MLflow UI**: http://localhost:5000
- **PostgreSQL**: localhost:5432

## 📊 **API Documentation**

Once the API is running, visit http://localhost:8000/docs for interactive API documentation.

### **Endpoints**

| Method | Endpoint | Description | 
|--------|----------|-------------|
| `GET` | `/` | API status and welcome message |
| `GET` | `/health` | Detailed health check |
| `POST` | `/predict` | Single house price prediction |
| `POST` | `/predict/confidence` | Prediction with confidence interval |

### **Request Format**

```json
{
  "MedInc": 8.3252,       // Median income in block group
  "HouseAge": 41.0,       // Median house age in block group
  "AveRooms": 6.984,      // Average number of rooms per household
  "AveBedrms": 1.024,     // Average number of bedrooms per household
  "Population": 322.0,    // Block group population
  "AveOccup": 2.555,      // Average number of household members
  "Latitude": 37.88,      // Block group latitude
  "Longitude": -122.23    // Block group longitude
}
```

## 🧪 **Testing**

### **Run All Tests**
```bash
pytest tests/ -v --cov=src
```

### **Test Categories**
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint validation
- **Model Tests**: Prediction accuracy and consistency

## 📈 **MLflow Tracking**

### **View Experiments**
```bash
# Start MLflow UI
mlflow ui --port 5000
```
Visit: http://localhost:5000


### **Experiment Features**
- Model performance metrics (RMSE, R², MAE)
- Hyperparameter tracking
- Model versioning and registry
- Artifact storage (models, plots, data)

## ☁️ **LocalStack to AWS Migration**

This project **already implements AWS infrastructure locally** using LocalStack! The same CDK code can deploy to real AWS with minimal changes.

### **✅ Currently Implemented (LocalStack)**

- ✅ **Lambda Functions** - Serverless inference with ML dependencies
- ✅ **S3 Storage** - Model artifacts and scalers stored in S3
- ✅ **API Gateway** - REST API with CORS support
- ✅ **AWS CDK** - Infrastructure as Code in TypeScript
- ✅ **Lambda Layers** - Pre-built ML dependencies (scikit-learn, pandas, numpy)

### **🚀 Deploy to Real AWS**

To deploy to production AWS (when ready):

```bash
# Configure AWS credentials
aws configure

# Set environment variable
export USE_LOCALSTACK=false

# Deploy to AWS
cd infrastructure
npm run bootstrap  # First time only
npm run deploy     # Deploy stack
```

### **📈 Future AWS Enhancements**

**SageMaker Integration Path:**
- **SageMaker Processing Jobs**: Scale data preprocessing with parallel instances
- **SageMaker Training Jobs**: Automated hyperparameter tuning
- **SageMaker Model Registry**: Enterprise model governance and A/B testing
- **SageMaker Endpoints**: Auto-scaling real-time inference
- **SageMaker Pipelines**: End-to-end workflow automation with retraining triggers
- **Additional Services**: CloudWatch monitoring, EventBridge orchestration, Step Functions for complex workflows

## 🎯 **Next Steps & Enhancements**

**Deployment:**
- [ ] Deploy to real AWS account (currently local-only with LocalStack)
- [ ] Add CloudWatch alarms and dashboards
- [ ] Implement API authentication (API Keys, Cognito, or IAM)
- [ ] Set up CI/CD pipeline for automated deployments

**ML Enhancements:**
- [ ] Add more model types (XGBoost, LightGBM, Neural Networks)
- [ ] Implement hyperparameter tuning with Optuna or SageMaker HPO
- [ ] Add model explainability (SHAP values, feature importance)
- [ ] Data drift detection and monitoring

**Infrastructure:**
- [ ] Migrate to SageMaker for enterprise-scale operations
- [ ] Add batch prediction endpoints
- [ ] Implement model versioning and A/B testing
- [ ] Set up data lake with S3 + Athena for analytics

---

**Built with ❤️ for the ML Engineering Community**