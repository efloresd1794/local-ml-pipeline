# Quick Start Guide - ML Pipeline on LocalStack

Get your ML pipeline running locally in under 10 minutes!

## Prerequisites ✅

- Docker Desktop (running)
- Python 3.9+
- Node.js 18+
- 5 GB free disk space

## Installation (5 minutes)

```bash
# 1. Setup environment
chmod +x scripts/setup-localstack.sh
./scripts/setup-localstack.sh

# 2. Start LocalStack
make start-localstack
```

Wait for: `LocalStack started!`

## Deploy Pipeline (3 minutes)

```bash
# Run full deployment
make deploy-all
```
or
from root folder:
cd infrastruture
cdklocal bootstrap aws://000000000000/us-east-1
cdklocal deploy --verbose   


This will:
1. ✅ Process California Housing data
2. ✅ Train Random Forest model
3. ✅ Upload model to S3 (LocalStack)
4. ✅ Deploy Lambda + API Gateway

## Test API (1 minute)

### Option 1: Web GUI (Recommended) 🌐

```bash
# Start the web interface
make web
```

Then open http://localhost:8080 in your browser!

Features:
- 🎨 Beautiful, user-friendly interface
- 📊 Real-time predictions
- 📈 Confidence intervals
- 🔄 Quick preset examples

### Option 2: Command Line Testing

```bash
# Run automated tests
make test
```

Expected output:
```
Testing Health Check Endpoint
Status Code: 200
✅ Model loaded successfully

Testing Prediction Endpoint
Luxury San Francisco House:
Prediction: $452,600.00
✅ Prediction successful
```

## Manual API Testing

```bash
# Get API URL
make api-url

# Test health
make health

# Or use curl
export API_URL="http://localhost:4566/restapis/{api-id}/prod/_user_request_"

curl -X POST $API_URL/predict \
  -H 'Content-Type: application/json' \
  -d '{"features": [8.3, 41, 7, 1, 322, 2.5, 37.88, -122.23]}'
```

## Common Commands

```bash
make help              # Show all commands
make web               # Start web GUI (http://localhost:8080)
make status           # Check LocalStack status
make logs             # View LocalStack logs
make s3-models        # List models in S3
make clean            # Clean up everything
```

## Troubleshooting

### LocalStack won't start
```bash
# Restart Docker Desktop
# Then:
make clean
make start-localstack
```

### Deployment fails
```bash
# Clean and retry
make clean
make setup
make deploy-all
```

### API returns 404
```bash
# Check API URL
make api-url

# Redeploy
cd infrastructure
npm run deploy:local
cd ..
```

## Next Steps

- Read [README.localstack.md](README.localstack.md) for detailed docs
- Modify model in `src/models/train_s3.py`
- Update Lambda in `src/lambda/inference.py`
- Change infrastructure in `infrastructure/lib/ml-pipeline-stack.ts`

## Architecture at a Glance

```
Data → Train → S3 (LocalStack) → Lambda → API Gateway → You!
```

Happy coding! 🚀
