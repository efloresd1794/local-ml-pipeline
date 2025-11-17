"""
AWS Lambda Handler for ML Model Inference
Loads model from S3 and performs predictions
"""

import json
import os
import boto3
from botocore.client import Config
import joblib
import numpy as np
import tempfile
from typing import Dict, Any, List


# Global variables for model caching
model = None
scaler = None
s3_client = None


def initialize_s3_client():
    """Initialize S3 client for LocalStack or AWS"""
    global s3_client

    if s3_client is None:
        # Check if running in LocalStack
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')

        if endpoint_url:
            # LocalStack configuration
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'test'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'test'),
                region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                config=Config(signature_version='s3v4')
            )
            print("Configured S3 client for LocalStack")
        else:
            # AWS configuration
            s3_client = boto3.client('s3')
            print("Configured S3 client for AWS")

    return s3_client


def load_model_from_s3():
    """Load model and scaler from S3 bucket"""
    global model, scaler

    if model is not None and scaler is not None:
        print("Model and scaler already loaded (using cache)")
        return model, scaler

    # Get S3 configuration from environment
    bucket_name = os.environ.get('MODEL_BUCKET', 'ml-model-artifacts')
    model_key = os.environ.get('MODEL_KEY', 'models/house_price_random_forest_model.joblib')
    scaler_key = os.environ.get('SCALER_KEY', 'models/scaler.joblib')

    print(f"Loading model from s3://{bucket_name}/{model_key}")
    print(f"Loading scaler from s3://{bucket_name}/{scaler_key}")

    # Initialize S3 client
    s3 = initialize_s3_client()

    try:
        # Download model
        with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as tmp_model:
            s3.download_file(bucket_name, model_key, tmp_model.name)
            model = joblib.load(tmp_model.name)
            os.remove(tmp_model.name)
            print("Model loaded successfully")

        # Download scaler
        with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as tmp_scaler:
            s3.download_file(bucket_name, scaler_key, tmp_scaler.name)
            scaler = joblib.load(tmp_scaler.name)
            os.remove(tmp_scaler.name)
            print("Scaler loaded successfully")

        return model, scaler

    except Exception as e:
        print(f"Error loading model from S3: {e}")
        raise


def preprocess_features(features: List[float], scaler) -> np.ndarray:
    """
    Preprocess input features

    Expected features (8):
    - MedInc: Median income in block group
    - HouseAge: Median house age in block group
    - AveRooms: Average number of rooms per household
    - AveBedrms: Average number of bedrooms per household
    - Population: Block group population
    - AveOccup: Average number of household members
    - Latitude: Block group latitude
    - Longitude: Block group longitude
    """
    # Convert to numpy array
    features_array = np.array(features).reshape(1, -1)

    # Scale features
    features_scaled = scaler.transform(features_array)

    return features_scaled


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body)
    }


def handler(event, context):
    """
    Lambda handler for ML inference

    Supports the following routes:
    - GET /health: Health check
    - POST /predict: Single prediction
    - POST /predict/confidence: Prediction with confidence interval
    """
    print(f"Event: {json.dumps(event)}")

    # Extract HTTP method and path
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')

    # Handle CORS preflight
    if http_method == 'OPTIONS':
        return create_response(200, {'message': 'OK'})

    # Health check endpoint
    if path == '/health' and http_method == 'GET':
        try:
            # Try to load model to verify health
            load_model_from_s3()
            return create_response(200, {
                'status': 'healthy',
                'model_loaded': True,
                'message': 'ML Inference service is running'
            })
        except Exception as e:
            return create_response(503, {
                'status': 'unhealthy',
                'model_loaded': False,
                'error': str(e)
            })

    # Prediction endpoints
    if path in ['/predict', '/predict/confidence'] and http_method == 'POST':
        try:
            # Parse request body
            if 'body' not in event:
                return create_response(400, {'error': 'Missing request body'})

            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']

            # Extract features
            if 'features' not in body:
                return create_response(400, {
                    'error': 'Missing features in request body',
                    'expected_format': {
                        'features': [
                            'MedInc', 'HouseAge', 'AveRooms', 'AveBedrms',
                            'Population', 'AveOccup', 'Latitude', 'Longitude'
                        ]
                    }
                })

            features = body['features']

            # Validate features
            if not isinstance(features, list) or len(features) != 8:
                return create_response(400, {
                    'error': 'Features must be a list of 8 numbers',
                    'received': len(features) if isinstance(features, list) else 'not a list'
                })

            # Load model and scaler
            model, scaler = load_model_from_s3()

            # Preprocess features
            features_scaled = preprocess_features(features, scaler)

            # Make prediction
            prediction = model.predict(features_scaled)[0]

            # Base response
            response_data = {
                'prediction': float(prediction),
                'prediction_description': f'Predicted median house value: ${prediction * 100000:.2f}',
                'features_received': features
            }

            # Add confidence interval for ensemble models (if requested)
            if path == '/predict/confidence':
                if hasattr(model, 'estimators_'):
                    # Get predictions from all estimators
                    estimator_predictions = np.array([
                        estimator.predict(features_scaled)[0]
                        for estimator in model.estimators_
                    ])

                    # Calculate confidence interval (95%)
                    std_dev = np.std(estimator_predictions)
                    confidence_interval = 1.96 * std_dev

                    response_data.update({
                        'confidence_interval': {
                            'lower_bound': float(prediction - confidence_interval),
                            'upper_bound': float(prediction + confidence_interval),
                            'std_dev': float(std_dev)
                        },
                        'confidence_interval_description':
                            f'95% confidence: ${(prediction - confidence_interval) * 100000:.2f} - '
                            f'${(prediction + confidence_interval) * 100000:.2f}'
                    })
                else:
                    response_data['warning'] = 'Confidence interval not available for non-ensemble models'

            return create_response(200, response_data)

        except json.JSONDecodeError:
            return create_response(400, {'error': 'Invalid JSON in request body'})
        except Exception as e:
            print(f"Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return create_response(500, {
                'error': 'Internal server error during prediction',
                'details': str(e)
            })

    # Unknown endpoint
    return create_response(404, {
        'error': 'Not found',
        'path': path,
        'method': http_method,
        'available_endpoints': {
            'GET /health': 'Health check',
            'POST /predict': 'Single prediction',
            'POST /predict/confidence': 'Prediction with confidence interval'
        }
    })
