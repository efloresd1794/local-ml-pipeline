.PHONY: help setup start-localstack stop-localstack status data train deploy test clean web quick-start run-api

# Default target
help:
	@echo "ML Pipeline with LocalStack - Available Commands:"
	@echo ""
	@echo "  make quick-start      - Quick start (recommended for development)"
	@echo "  make run-api          - Run FastAPI server (after quick-start)"
	@echo ""
	@echo "  make setup            - Initial setup (install dependencies)"
	@echo "  make start-localstack - Start LocalStack container"
	@echo "  make stop-localstack  - Stop LocalStack container"
	@echo "  make status          - Check LocalStack status"
	@echo "  make data            - Process training data"
	@echo "  make train           - Train model and upload to S3"
	@echo "  make build-layer     - Build Lambda layer with ML dependencies"
	@echo "  make bootstrap       - Bootstrap CDK for LocalStack (one-time setup)"
	@echo "  make deploy          - Deploy infrastructure to LocalStack (CDK)"
	@echo "  make deploy-direct   - Deploy Lambda directly (bypasses CDK issues) ⭐"
	@echo "  make deploy-all      - Full deployment (data + train + deploy)"
	@echo ""
	@echo "Testing:"
	@echo "  make test                    - Run all tests (unit + integration)"
	@echo "  make test-unit               - Run all unit tests (FastAPI + Lambda)"
	@echo "  make test-fastapi            - Run FastAPI unit tests only"
	@echo "  make test-lambda-unit        - Run Lambda unit tests only"
	@echo "  make test-lambda-integration - Run Lambda integration tests only"
	@echo "  make test-cdk                - Run CDK infrastructure tests"
	@echo ""
	@echo "  make web             - Start web GUI (http://localhost:8080)"
	@echo "  make clean           - Clean up containers and data"
	@echo "  make logs            - View LocalStack logs"
	@echo ""

# Initial setup
setup:
	@echo "Running setup..."
	@chmod +x scripts/setup-localstack.sh
	@./scripts/setup-localstack.sh

# Start LocalStack
start-localstack:
	@echo "Starting LocalStack..."
	@docker-compose -f docker/docker-compose.localstack.yml up -d
	@echo "Waiting for LocalStack to be ready..."
	@sleep 5
	@echo "LocalStack started!"

# Stop LocalStack
stop-localstack:
	@echo "Stopping LocalStack..."
	@docker-compose -f docker/docker-compose.localstack.yml down

# Check status
status:
	@echo "LocalStack Status:"
	@docker ps | grep localstack || echo "LocalStack is not running"
	@echo ""
	@echo "LocalStack Health:"
	@curl -s http://localhost:4566/_localstack/health | python3 -m json.tool || echo "LocalStack is not responding"

# Process data
data:
	@echo "Processing training data..."
	@. venv/bin/activate && python -m src.data.data_pipeline

# Train model
train:
	@echo "Training model and uploading to S3..."
	@. venv/bin/activate && python -m src.models.train_s3

# Deploy infrastructure
deploy: build-layer
	@echo "Deploying CDK stack to LocalStack..."
	@export AWS_ENDPOINT_URL=http://localhost:4566 AWS_ENDPOINT_URL_S3=http://localhost:4566 && cd infrastructure && npm run deploy:local

# Full deployment
deploy-all:
	@echo "Running full deployment pipeline..."
	@chmod +x scripts/deploy-localstack.sh
	@./scripts/deploy-localstack.sh

# Test API
test:
	@echo "Running all tests..."
	@echo ""
	@echo "=== FastAPI Unit Tests ==="
	@. venv/bin/activate && pytest tests/test_fastapi.py -v || true
	@echo ""
	@echo "=== Lambda Unit Tests ==="
	@. venv/bin/activate && pytest tests/test_lambda_unit.py -v || true
	@echo ""
	@echo "=== Lambda Integration Tests ==="
	@. venv/bin/activate && python tests/test_lambda.py

# Run only unit tests (FastAPI + Lambda)
test-unit:
	@echo "Running all unit tests..."
	@echo ""
	@echo "=== FastAPI Unit Tests ==="
	@. venv/bin/activate && pytest tests/test_fastapi.py -v
	@echo ""
	@echo "=== Lambda Unit Tests ==="
	@. venv/bin/activate && pytest tests/test_lambda_unit.py -v

# Run only FastAPI unit tests
test-fastapi:
	@echo "Running FastAPI unit tests..."
	@. venv/bin/activate && pytest tests/test_fastapi.py -v

# Run only Lambda unit tests
test-lambda-unit:
	@echo "Running Lambda unit tests..."
	@. venv/bin/activate && pytest tests/test_lambda_unit.py -v

# Run only Lambda integration tests
test-lambda-integration:
	@echo "Running Lambda integration tests..."
	@. venv/bin/activate && python tests/test_lambda.py

# Run CDK infrastructure tests
test-cdk:
	@echo "Running CDK infrastructure tests..."
	@cd infrastructure && npm test

# View logs
logs:
	@docker logs -f localstack-ml-pipeline

# Clean up
clean:
	@echo "Cleaning up..."
	@docker-compose -f docker-compose.localstack.yml down -v
	@rm -rf localstack-data/
	@rm -rf infrastructure/cdk.out/
	@rm -rf lambda-layers/ml-dependencies/python/
	@rm -rf models/*.joblib
	@rm -rf data/processed/*.pkl
	@echo "Cleanup complete!"

# Build Lambda layer
build-layer:
	@echo "Building Lambda layer..."
	@cd lambda-layers && ./build-layer.sh

# Bootstrap CDK for LocalStack (one-time setup)
bootstrap:
	@echo "Bootstrapping CDK for LocalStack..."
	@export AWS_ENDPOINT_URL=http://localhost:4566 AWS_ENDPOINT_URL_S3=http://localhost:4566 && cd infrastructure && npx cdklocal bootstrap aws://000000000000/us-east-1

# Deploy Lambda directly (bypasses CDK asset publishing issues)
deploy-direct:
	@echo "Deploying Lambda directly to LocalStack..."
	@chmod +x scripts/deploy-lambda-direct.sh
	@./scripts/deploy-lambda-direct.sh

# Check S3 buckets
s3-list:
	@echo "S3 Buckets in LocalStack:"
	@AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 ls

# List models in S3
s3-models:
	@echo "Models in S3:"
	@AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 ls s3://ml-model-artifacts/models/ || echo "No models found"

# Get API URL
api-url:
	@echo "Fetching API Gateway URL..."
	@API_ID=$$(AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis --query "items[?name=='ML-Inference-API'].id" --output text 2>/dev/null); \
	if [ -n "$$API_ID" ] && [ "$$API_ID" != "None" ]; then \
		echo "API URL: http://localhost:4566/restapis/$$API_ID/prod/_user_request_"; \
	else \
		echo "API Gateway not found. Please deploy first."; \
	fi

# Quick health check
health:
	@echo "Checking API health..."
	@API_ID=$$(AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis --query "items[?name=='ML-Inference-API'].id" --output text 2>/dev/null); \
	if [ -n "$$API_ID" ] && [ "$$API_ID" != "None" ]; then \
		curl -s http://localhost:4566/restapis/$$API_ID/prod/_user_request_/health | python3 -m json.tool; \
	else \
		echo "API Gateway not found. Please deploy first."; \
	fi

# Start web GUI
web:
	@echo "Starting web GUI..."
	@echo "Open http://localhost:8080 in your browser"
	@echo ""
	@echo "API should be running at http://localhost:8000"
	@echo ""
	@python3 web/serve.py

# Quick Start - Recommended workflow for development
quick-start:
	@echo "Running quick start..."
	@chmod +x scripts/quick-start.sh
	@./scripts/quick-start.sh

# Run FastAPI server
run-api:
	@echo "Starting FastAPI server..."
	@echo "API will be available at http://localhost:8000"
	@echo ""
	@echo "Endpoints:"
	@echo "  GET  http://localhost:8000/health"
	@echo "  POST http://localhost:8000/predict"
	@echo "  POST http://localhost:8000/predict/confidence"
	@echo ""
	@echo "Press Ctrl+C to stop"
	@echo ""
	@source venv/bin/activate && python src/api/main.py
