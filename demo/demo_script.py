"""
Demo script for showcasing the ML pipeline
Run this to demonstrate key features to recruiters
"""
import requests
import json
import time

# Demo scenarios
demo_houses = [
    {"name": "Luxury SF House", "data": {"MedInc": 15.0, "HouseAge": 5, "AveRooms": 8, "AveBedrms": 1.2, "Population": 1000, "AveOccup": 2, "Latitude": 37.77, "Longitude": -122.42}},
    {"name": "Average LA House", "data": {"MedInc": 6.0, "HouseAge": 20, "AveRooms": 5.5, "AveBedrms": 1.1, "Population": 2500, "AveOccup": 3, "Latitude": 34.05, "Longitude": -118.24}},
    {"name": "Budget Central Valley", "data": {"MedInc": 3.0, "HouseAge": 35, "AveRooms": 4, "AveBedrms": 1.3, "Population": 4000, "AveOccup": 4, "Latitude": 36.78, "Longitude": -119.42}}
]

print("🏠 House Price Prediction Demo")
print("=" * 40)

for house in demo_houses:
    print(f"\n📍 {house['name']}")
    
    # Make prediction
    response = requests.post(
        "http://localhost:8000/predict",
        json=house['data']
    )
    
    if response.status_code == 200:
        prediction = response.json()['prediction']
        print(f"   Predicted Price: ${prediction:.2f}00,000")
        print(f"   Median Income: ${house['data']['MedInc']:.1f}0,000")
        print(f"   House Age: {house['data']['HouseAge']} years")
    else:
        print(f"   Error: {response.status_code}")

print("\n🎯 Demo completed! Check MLflow UI for experiment tracking.")