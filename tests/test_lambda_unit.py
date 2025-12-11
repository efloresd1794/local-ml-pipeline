"""
Unit tests for Lambda inference function
Tests all functions with mocked dependencies
"""

import pytest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import using importlib to handle 'lambda' reserved keyword
import importlib.util
spec = importlib.util.spec_from_file_location(
    "inference",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "lambda", "inference.py")
)
inference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inference)

# Import functions
initialize_s3_client = inference.initialize_s3_client
load_model_from_s3 = inference.load_model_from_s3
preprocess_features = inference.preprocess_features
create_response = inference.create_response
handler = inference.handler


class TestInitializeS3Client:
    """Test S3 client initialization"""

    def test_initialize_s3_client_localstack(self):
        """Test S3 client initialization for LocalStack"""
        # Set up environment for LocalStack
        with patch.dict(os.environ, {
            'AWS_ENDPOINT_URL': 'http://localhost:4566',
            'AWS_ACCESS_KEY_ID': 'test',
            'AWS_SECRET_ACCESS_KEY': 'test',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            # Reset the global s3_client
            inference.s3_client = None

            with patch.object(inference, 'boto3') as mock_boto3:
                client = initialize_s3_client()

                # Verify boto3.client was called with LocalStack config
                mock_boto3.client.assert_called_once()
                call_args = mock_boto3.client.call_args
                assert call_args[0][0] == 's3'
                assert call_args[1]['endpoint_url'] == 'http://localhost:4566'

    def test_initialize_s3_client_aws(self):
        """Test S3 client initialization for AWS"""
        # Clear endpoint URL
        with patch.dict(os.environ, {}, clear=True):
            # Reset the global s3_client
            inference.s3_client = None

            with patch.object(inference, 'boto3') as mock_boto3:
                client = initialize_s3_client()

                # Verify boto3.client was called without endpoint
                mock_boto3.client.assert_called_once_with('s3')


class TestLoadModelFromS3:
    """Test model loading from S3"""

    def test_load_model_from_s3_success(self):
        """Test successful model loading"""
        # Reset global variables
        inference.model = None
        inference.scaler = None

        # Mock S3 client
        mock_s3 = Mock()

        # Mock temp files
        mock_temp_model = Mock()
        mock_temp_model.name = '/tmp/model.joblib'
        mock_temp_scaler = Mock()
        mock_temp_scaler.name = '/tmp/scaler.joblib'

        # Mock joblib loading
        mock_model = Mock()
        mock_scaler_obj = Mock()

        with patch.object(inference, 'initialize_s3_client', return_value=mock_s3), \
             patch.object(inference, 'joblib') as mock_joblib, \
             patch.object(inference, 'tempfile') as mock_tempfile, \
             patch.object(inference, 'os') as mock_os:

            mock_tempfile.NamedTemporaryFile.side_effect = [
                MagicMock(__enter__=lambda self: mock_temp_model, __exit__=lambda *args: None),
                MagicMock(__enter__=lambda self: mock_temp_scaler, __exit__=lambda *args: None)
            ]
            mock_joblib.load.side_effect = [mock_model, mock_scaler_obj]

            model, scaler = load_model_from_s3()

            # Verify S3 downloads were called
            assert mock_s3.download_file.call_count == 2
            assert model == mock_model
            assert scaler == mock_scaler_obj

    def test_load_model_from_cache(self):
        """Test model loading from cache"""
        # Set cached model
        mock_model = Mock()
        mock_scaler = Mock()
        inference.model = mock_model
        inference.scaler = mock_scaler

        model, scaler = load_model_from_s3()

        # Should return cached values
        assert model == mock_model
        assert scaler == mock_scaler


class TestPreprocessFeatures:
    """Test feature preprocessing"""

    def test_preprocess_features_valid_input(self):
        """Test preprocessing with valid features"""
        # Sample features
        features = [8.3252, 41.0, 6.984, 1.024, 322.0, 2.555, 37.88, -122.23]

        # Mock scaler
        mock_scaler = Mock()
        mock_scaler.transform.return_value = np.array([[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]])

        result = preprocess_features(features, mock_scaler)

        # Verify transform was called
        mock_scaler.transform.assert_called_once()

        # Check that engineered features were added
        call_args = mock_scaler.transform.call_args[0][0]
        assert call_args.shape == (1, 11)  # 8 original + 3 engineered

    def test_preprocess_features_engineering(self):
        """Test feature engineering calculations"""
        features = [8.3252, 41.0, 6.984, 1.024, 322.0, 2.555, 37.88, -122.23]

        mock_scaler = Mock()
        mock_scaler.transform.return_value = np.array([[0] * 11])

        preprocess_features(features, mock_scaler)

        # Get the features passed to scaler
        call_args = mock_scaler.transform.call_args[0][0]
        engineered = call_args[0]

        # Verify engineered features
        # rooms_per_household = AveRooms / AveOccup = 6.984 / 2.555
        # bedrooms_per_room = AveBedrms / AveRooms = 1.024 / 6.984
        # population_per_household = Population / AveOccup = 322.0 / 2.555

        assert len(engineered) == 11
        assert np.isclose(engineered[8], 6.984 / 2.555)  # rooms_per_household
        assert np.isclose(engineered[9], 1.024 / 6.984)  # bedrooms_per_room
        assert np.isclose(engineered[10], 322.0 / 2.555)  # population_per_household

    def test_preprocess_features_zero_division(self):
        """Test handling of zero division in feature engineering"""
        # Features with zero AveOccup and AveRooms
        features = [8.3252, 41.0, 0.0, 1.024, 322.0, 0.0, 37.88, -122.23]

        mock_scaler = Mock()
        mock_scaler.transform.return_value = np.array([[0] * 11])

        # Should not raise exception
        result = preprocess_features(features, mock_scaler)

        # Verify engineered features are 0 when division by zero
        call_args = mock_scaler.transform.call_args[0][0]
        engineered = call_args[0]

        assert engineered[8] == 0  # rooms_per_household (AveRooms=0 / AveOccup=0)
        assert engineered[9] == 0  # bedrooms_per_room (AveBedrms / AveRooms=0)
        assert engineered[10] == 0  # population_per_household (Population / AveOccup=0)


class TestCreateResponse:
    """Test API Gateway response creation"""

    def test_create_response_success(self):
        """Test successful response creation"""
        body = {'message': 'Success', 'data': 123}
        response = create_response(200, body)

        assert response['statusCode'] == 200
        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert json.loads(response['body']) == body

    def test_create_response_error(self):
        """Test error response creation"""
        body = {'error': 'Something went wrong'}
        response = create_response(500, body)

        assert response['statusCode'] == 500
        assert json.loads(response['body']) == body


class TestHandler:
    """Test Lambda handler function"""

    def test_handler_options_request(self):
        """Test CORS preflight OPTIONS request"""
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/predict'
        }

        response = handler(event, None)

        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']

    def test_handler_health_check_success(self):
        """Test health check endpoint - success"""
        event = {
            'httpMethod': 'GET',
            'path': '/health'
        }

        mock_model = Mock()
        mock_scaler = Mock()

        with patch.object(inference, 'load_model_from_s3', return_value=(mock_model, mock_scaler)):
            response = handler(event, None)

            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['status'] == 'healthy'
            assert body['model_loaded'] == True

    def test_handler_health_check_failure(self):
        """Test health check endpoint - failure"""
        event = {
            'httpMethod': 'GET',
            'path': '/health'
        }

        with patch.object(inference, 'load_model_from_s3', side_effect=Exception('S3 connection failed')):
            response = handler(event, None)

            assert response['statusCode'] == 503
            body = json.loads(response['body'])
            assert body['status'] == 'unhealthy'
            assert body['model_loaded'] == False

    def test_handler_predict_success(self):
        """Test prediction endpoint - success"""
        event = {
            'httpMethod': 'POST',
            'path': '/predict',
            'body': json.dumps({
                'features': [8.3252, 41.0, 6.984, 1.024, 322.0, 2.555, 37.88, -122.23]
            })
        }

        # Mock model
        mock_model = Mock()
        mock_model.predict.return_value = np.array([4.526])
        mock_scaler = Mock()

        with patch.object(inference, 'load_model_from_s3', return_value=(mock_model, mock_scaler)), \
             patch.object(inference, 'preprocess_features', return_value=np.array([[0.1, 0.2, 0.3]])):

            response = handler(event, None)

            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'prediction' in body
            assert body['prediction'] == 4.526

    def test_handler_predict_missing_body(self):
        """Test prediction endpoint - missing body"""
        event = {
            'httpMethod': 'POST',
            'path': '/predict'
        }

        response = handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    def test_handler_predict_missing_features(self):
        """Test prediction endpoint - missing features"""
        event = {
            'httpMethod': 'POST',
            'path': '/predict',
            'body': json.dumps({'data': 'invalid'})
        }

        response = handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing features' in body['error']

    def test_handler_predict_invalid_features_count(self):
        """Test prediction endpoint - invalid feature count"""
        event = {
            'httpMethod': 'POST',
            'path': '/predict',
            'body': json.dumps({
                'features': [1.0, 2.0, 3.0]  # Only 3 features instead of 8
            })
        }

        response = handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Features must be a list of 8 numbers' in body['error']

    def test_handler_confidence_with_ensemble(self):
        """Test confidence interval endpoint with ensemble model"""
        event = {
            'httpMethod': 'POST',
            'path': '/predict/confidence',
            'body': json.dumps({
                'features': [8.3252, 41.0, 6.984, 1.024, 322.0, 2.555, 37.88, -122.23]
            })
        }

        # Mock ensemble model (RandomForest)
        mock_estimator1 = Mock()
        mock_estimator1.predict.return_value = np.array([4.5])
        mock_estimator2 = Mock()
        mock_estimator2.predict.return_value = np.array([4.7])

        mock_model = Mock()
        mock_model.predict.return_value = np.array([4.6])
        mock_model.estimators_ = [mock_estimator1, mock_estimator2]

        mock_scaler = Mock()

        with patch.object(inference, 'load_model_from_s3', return_value=(mock_model, mock_scaler)), \
             patch.object(inference, 'preprocess_features', return_value=np.array([[0.1, 0.2, 0.3]])):

            response = handler(event, None)

            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'confidence_interval' in body
            assert 'lower_bound' in body['confidence_interval']
            assert 'upper_bound' in body['confidence_interval']
            assert 'std_dev' in body['confidence_interval']

    def test_handler_confidence_without_ensemble(self):
        """Test confidence interval endpoint with non-ensemble model"""
        event = {
            'httpMethod': 'POST',
            'path': '/predict/confidence',
            'body': json.dumps({
                'features': [8.3252, 41.0, 6.984, 1.024, 322.0, 2.555, 37.88, -122.23]
            })
        }

        # Mock non-ensemble model (LinearRegression)
        mock_model = Mock(spec=['predict'])  # Only has predict method, no estimators_
        mock_model.predict.return_value = np.array([4.6])

        mock_scaler = Mock()

        with patch.object(inference, 'load_model_from_s3', return_value=(mock_model, mock_scaler)), \
             patch.object(inference, 'preprocess_features', return_value=np.array([[0.1, 0.2, 0.3]])):

            response = handler(event, None)

            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'warning' in body
            assert 'not available for non-ensemble models' in body['warning']

    def test_handler_invalid_json(self):
        """Test prediction endpoint - invalid JSON"""
        event = {
            'httpMethod': 'POST',
            'path': '/predict',
            'body': 'invalid json {'
        }

        response = handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid JSON' in body['error']

    def test_handler_unknown_endpoint(self):
        """Test unknown endpoint"""
        event = {
            'httpMethod': 'GET',
            'path': '/unknown'
        }

        response = handler(event, None)

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'Not found' in body['error']
        assert 'available_endpoints' in body
