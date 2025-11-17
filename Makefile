.PHONY: help setup start-localstack stop-localstack status data train deploy test clean

# Default target
help:
	@echo "ML Pipeline with LocalStack - Available Commands:"
	@echo ""
	@echo "  make setup            - Initial setup (install dependencies)"
	@echo "  make start-localstack - Start LocalStack container"
	@echo "  make stop-localstack  - Stop LocalStack container"
	@echo "  make status          - Check LocalStack status"
	@echo "  make data            - Process training data"
	@echo "  make train           - Train model and upload to S3"
	@echo "  make deploy          - Deploy infrastructure to LocalStack"
	@echo "  make deploy-all      - Full deployment (data + train + deploy)"
	@echo "  make test            - Test the API"
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
	@docker-compose -f docker-compose.localstack.yml up -d
	@echo "Waiting for LocalStack to be ready..."
	@sleep 5
	@echo "LocalStack started!"

# Stop LocalStack
stop-localstack:
	@echo "Stopping LocalStack..."
	@docker-compose -f docker-compose.localstack.yml down

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
deploy:
	@echo "Deploying CDK stack to LocalStack..."
	@cd infrastructure && npm run deploy:local

# Full deployment
deploy-all:
	@echo "Running full deployment pipeline..."
	@chmod +x scripts/deploy-localstack.sh
	@./scripts/deploy-localstack.sh

# Test API
test:
	@echo "Testing API..."
	@. venv/bin/activate && python scripts/test-api.py

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

# Check S3 buckets
s3-list:
	@echo "S3 Buckets in LocalStack:"
	@aws --endpoint-url=http://localhost:4566 s3 ls

# List models in S3
s3-models:
	@echo "Models in S3:"
	@aws --endpoint-url=http://localhost:4566 s3 ls s3://ml-model-artifacts/models/ || echo "No models found"

# Get API URL
api-url:
	@echo "Fetching API Gateway URL..."
	@API_ID=$$(aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis --query 'items[0].id' --output text 2>/dev/null); \
	if [ -n "$$API_ID" ] && [ "$$API_ID" != "None" ]; then \
		echo "API URL: http://localhost:4566/restapis/$$API_ID/prod/_user_request_"; \
	else \
		echo "API Gateway not found. Please deploy first."; \
	fi

# Quick health check
health:
	@echo "Checking API health..."
	@API_ID=$$(aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis --query 'items[0].id' --output text 2>/dev/null); \
	if [ -n "$$API_ID" ] && [ "$$API_ID" != "None" ]; then \
		curl -s http://localhost:4566/restapis/$$API_ID/prod/_user_request_/health | python3 -m json.tool; \
	else \
		echo "API Gateway not found. Please deploy first."; \
	fi
