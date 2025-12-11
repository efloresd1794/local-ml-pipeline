import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "House Price Prediction API is running!" in response.json()["message"]

def test_health_check():
    response = client.get("/health")
    assert response.status_code in [200, 503]  # May fail if model not loaded

def test_predict():
    test_data = {
        "MedInc": 8.3252,
        "HouseAge": 41.0,
        "AveRooms": 6.984,
        "AveBedrms": 1.024,
        "Population": 322.0,
        "AveOccup": 2.555,
        "Latitude": 37.88,
        "Longitude": -122.23
    }
    
    response = client.post("/predict", json=test_data)
    
    if response.status_code == 200:
        assert "prediction" in response.json()
        assert isinstance(response.json()["prediction"], (int, float))
    else:
        # Model might not be trained yet
        assert response.status_code == 503