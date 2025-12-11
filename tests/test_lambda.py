#!/usr/bin/env python3
"""
Test script for ML Inference API on LocalStack
Tests health check and prediction endpoints
"""

import requests
import json
import os
import sys


def get_api_url():
    """Get API Gateway URL from environment or LocalStack"""
    # Try to get from environment
    api_url = os.environ.get('API_GATEWAY_URL')

    if not api_url:
        # Try to get from LocalStack
        import subprocess
        try:
            # Set AWS credentials for LocalStack
            env = os.environ.copy()
            env['AWS_ACCESS_KEY_ID'] = 'test'
            env['AWS_SECRET_ACCESS_KEY'] = 'test'
            env['AWS_DEFAULT_REGION'] = 'us-east-1'

            result = subprocess.run(
                ['aws', '--endpoint-url=http://localhost:4566', 'apigateway',
                 'get-rest-apis', '--query', "items[?name=='ML-Inference-API'].id",
                 '--output', 'text'],
                capture_output=True,
                text=True,
                env=env
            )
            api_id = result.stdout.strip()

            if api_id and api_id != 'None':
                api_url = f"http://localhost:4566/restapis/{api_id}/prod/_user_request_"
            else:
                print("Could not find API Gateway in LocalStack")
                print("Please ensure the stack is deployed")
                sys.exit(1)
        except Exception as e:
            print(f"Error getting API URL: {e}")
            sys.exit(1)

    return api_url


def test_health(base_url):
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("Testing Health Check Endpoint")
    print("="*60)

    url = f"{base_url}/health"
    print(f"GET {url}")

    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_prediction(base_url):
    """Test prediction endpoint"""
    print("\n" + "="*60)
    print("Testing Prediction Endpoint")
    print("="*60)

    # Sample California housing data
    # Features: [MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude]
    test_cases = [
        {
            "name": "Luxury San Francisco House",
            "features": [8.3252, 41, 6.984, 1.024, 322, 2.556, 37.88, -122.23]
        },
        {
            "name": "Average Los Angeles House",
            "features": [3.8, 25, 5.5, 1.2, 1200, 3.0, 34.05, -118.24]
        },
        {
            "name": "Budget Central Valley House",
            "features": [2.5, 15, 4.8, 1.0, 800, 2.5, 36.74, -119.78]
        }
    ]

    url = f"{base_url}/predict"

    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"Features: {test_case['features']}")

        payload = {"features": test_case['features']}

        try:
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"Prediction: ${result['prediction'] * 100000:,.2f}")
                print(f"Description: {result.get('prediction_description', 'N/A')}")
            else:
                print(f"Error Response: {response.text}")

        except Exception as e:
            print(f"Error: {e}")


def test_confidence(base_url):
    """Test prediction with confidence interval endpoint"""
    print("\n" + "="*60)
    print("Testing Confidence Interval Endpoint")
    print("="*60)

    # Sample data
    features = [8.3252, 41, 6.984, 1.024, 322, 2.556, 37.88, -122.23]

    url = f"{base_url}/predict/confidence"
    payload = {"features": features}

    print(f"POST {url}")
    print(f"Features: {features}")

    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\nPrediction: ${result['prediction'] * 100000:,.2f}")

            if 'confidence_interval' in result:
                ci = result['confidence_interval']
                print(f"Confidence Interval (95%):")
                print(f"  Lower: ${ci['lower_bound'] * 100000:,.2f}")
                print(f"  Upper: ${ci['upper_bound'] * 100000:,.2f}")
                print(f"  Std Dev: {ci['std_dev']:.4f}")
            else:
                print(f"Warning: {result.get('warning', 'No confidence interval available')}")
        else:
            print(f"Error Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main test function"""
    print("="*60)
    print("ML Inference API Test Suite")
    print("="*60)

    # Get API URL
    try:
        base_url = get_api_url()
        print(f"\nAPI Base URL: {base_url}")
    except Exception as e:
        print(f"Failed to get API URL: {e}")
        sys.exit(1)

    # Run tests
    health_ok = test_health(base_url)

    if health_ok:
        test_prediction(base_url)
        test_confidence(base_url)
    else:
        print("\n⚠️  Health check failed. Skipping other tests.")
        sys.exit(1)

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
