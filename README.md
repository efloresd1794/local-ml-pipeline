# 🏠 House Price Prediction ML Pipeline

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com/)
[![MLflow](https://img.shields.io/badge/MLflow-2.8%2B-orange)](https://mlflow.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready end-to-end machine learning pipeline for house price prediction, featuring MLflow experiment tracking, Docker deployment, and FastAPI serving with comprehensive CI/CD automation.

## 🎯 **Project Overview**

This project demonstrates enterprise-level ML engineering practices by implementing a complete pipeline from data ingestion to model deployment. Built with California Housing dataset, it showcases modern MLOps workflows including experiment tracking, model versioning, containerized deployment, and automated testing.

### **Key Features**

- 🔄 **Automated Data Pipeline** - Preprocessing, feature engineering, and data validation
- 🧪 **MLflow Integration** - Experiment tracking, model registry, and versioning
- 🚀 **FastAPI Service** - High-performance REST API with automatic documentation
- 🐳 **Docker Deployment** - Containerized application with multi-service orchestration
- 🧪 **Comprehensive Testing** - Unit tests, integration tests, and API validation
- ⚙️ **CI/CD Pipeline** - Automated testing and deployment with GitHub Actions
- 📊 **Model Monitoring** - Prediction confidence intervals and model performance tracking

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Source   │───▶│  Data Pipeline   │───▶│  Feature Store  │
│ (California     │    │  (Preprocessing) │    │   (Processed)   │
│  Housing Data)  │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Prediction    │◀───│   FastAPI App    │◀───│  Model Training │
│    Service      │    │   (REST API)     │    │  (MLflow Track) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 **Project Structure**

```
house-price-ml-pipeline/
├── 📂 src/
│   ├── 📂 data/
│   │   └── 📄 data_pipeline.py      # Data processing and feature engineering
│   ├── 📂 models/
│   │   ├── 📄 train.py              # Model training with MLflow tracking
│   │   └── 📄 predict.py            # Prediction service and model loading
│   └── 📂 api/
│       └── 📄 main.py               # FastAPI application and endpoints
├── 📂 tests/
│   └── 📄 test_api.py               # API integration tests
├── 📂 docker/
│   ├── 📄 Dockerfile                # Container configuration
│   └── 📄 docker-compose.yml        # Multi-service orchestration
├── 📂 .github/workflows/
│   └── 📄 ci-cd.yml                 # CI/CD pipeline automation
├── 📂 data/
│   ├── 📂 raw/                      # Raw dataset storage
│   └── 📂 processed/                # Processed features and scalers
├── 📂 models/                       # Trained model artifacts
├── 📂 mlruns/                       # MLflow experiment tracking
├── 📄 requirements.txt              # Python dependencies
├── 📄 setup.py                      # Package configuration
└── 📄 README.md                     # Project documentation
```

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8+
- Docker (optional, for containerized deployment)
- Git

### **1. Installation**

```bash
# Clone the repository
git clone https://github.com/yourusername/house-price-ml-pipeline.git
cd house-price-ml-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### **2. Run the Pipeline**

```bash
# Step 1: Process data
python src/data/data_pipeline.py

# Step 2: Train models
python src/models/train.py

# Step 3: Start API server
python src/api/main.py
```

### **3. Test the API**

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Make prediction
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "MedInc": 8.3252,
       "HouseAge": 41.0,
       "AveRooms": 6.984,
       "AveBedrms": 1.024,
       "Population": 322.0,
       "AveOccup": 2.555,
       "Latitude": 37.88,
       "Longitude": -122.23
     }'
```

**Expected Response:**
```json
{
  "prediction": 4.526,
  "status": "success"
}
```

### **4. Run Tests**

```bash
pytest tests/ -v
```

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

## ☁️ **AWS Cloud Enhancement**

This pipeline is designed for seamless migration to **AWS SageMaker** for enterprise-scale ML operations. The current local implementation serves as a foundation that can be enhanced with AWS services:

**🔄 SageMaker Integration Path:**
- **SageMaker Processing Jobs**: Replace local data pipeline with scalable preprocessing using SageMaker Processing, enabling parallel feature engineering across multiple instances
- **SageMaker Training Jobs**: Migrate MLflow experiments to SageMaker Experiments with automatic hyperparameter tuning using SageMaker Automatic Model Tuning
- **SageMaker Model Registry**: Replace local MLflow registry with SageMaker Model Registry for enterprise model governance and automated A/B testing
- **SageMaker Endpoints**: Deploy FastAPI as SageMaker real-time endpoints with auto-scaling and multi-model hosting capabilities
- **SageMaker Pipelines**: Convert the entire workflow into a SageMaker Pipeline with automated retraining triggers based on data drift detection
- **Additional AWS Services**: Integrate S3 for data lake storage, CloudWatch for monitoring, Lambda for serverless processing, and EventBridge for workflow orchestration

This architecture enables **production-scale ML operations** with enterprise features like automated model deployment, A/B testing, data drift detection, and cost optimization through managed infrastructure.

## 🎯 **Next Steps & Enhancements**

- [ ] **SageMaker Migration**: Convert pipeline to SageMaker Processing, Training, and Endpoints
- [ ] **Model Monitoring**: Add SageMaker Model Monitor for prediction drift detection
- [ ] **A/B Testing**: Implement SageMaker multi-variant endpoints for model comparison
- [ ] **Batch Predictions**: Add SageMaker Batch Transform for bulk predictions
- [ ] **Model Explainability**: Integrate SageMaker Clarify for feature importance and bias detection
- [ ] **Real-time Streaming**: Add Kinesis Data Streams for live predictions with SageMaker

---

**Built with ❤️ for the ML Engineering Community**