from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.predict import HousePricePredictor
from loguru import logger

# Initialize FastAPI app
app = FastAPI(
    title="House Price Prediction API",
    description="An API for predicting house prices using machine learning",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize predictor
try:
    predictor = HousePricePredictor()
    logger.info("Predictor initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize predictor: {str(e)}")
    predictor = None

# Pydantic models for request/response
class HouseFeatures(BaseModel):
    MedInc: float  # Median income
    HouseAge: float  # House age
    AveRooms: float  # Average rooms
    AveBedrms: float  # Average bedrooms
    Population: float  # Population
    AveOccup: float  # Average occupancy
    Latitude: float  # Latitude
    Longitude: float  # Longitude

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "MedInc": 8.3252,
                "HouseAge": 41.0,
                "AveRooms": 6.984,
                "AveBedrms": 1.024,
                "Population": 322.0,
                "AveOccup": 2.555,
                "Latitude": 37.88,
                "Longitude": -122.23
            }
        }
    }

# Array format (for web interface compatibility)
class HouseFeaturesArray(BaseModel):
    features: list[float]  # [MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude]

    def to_dict(self):
        """Convert array to named dict"""
        if len(self.features) != 8:
            raise ValueError("Features array must contain exactly 8 values")
        return {
            "MedInc": self.features[0],
            "HouseAge": self.features[1],
            "AveRooms": self.features[2],
            "AveBedrms": self.features[3],
            "Population": self.features[4],
            "AveOccup": self.features[5],
            "Latitude": self.features[6],
            "Longitude": self.features[7]
        }

class PredictionResponse(BaseModel):
    prediction: float
    status: str = "success"

class ConfidencePredictionResponse(BaseModel):
    prediction: float
    confidence_interval: dict
    status: str = "success"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "House Price Prediction API is running!"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    return {
        "status": "healthy",
        "model_loaded": predictor is not None,
        "api_version": "1.0.0"
    }

@app.post("/predict")
async def predict_price(request: HouseFeaturesArray | HouseFeatures):
    """Predict house price (accepts both array and object format)"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    try:
        # Convert to dict based on input type
        if isinstance(request, HouseFeaturesArray):
            input_data = request.to_dict()
            features_array = request.features
        else:
            input_data = request.model_dump()
            # Convert dict to array for features_received
            features_array = [
                input_data["MedInc"], input_data["HouseAge"], input_data["AveRooms"],
                input_data["AveBedrms"], input_data["Population"], input_data["AveOccup"],
                input_data["Latitude"], input_data["Longitude"]
            ]

        # Make prediction
        prediction = predictor.predict(input_data)

        return {
            "prediction": prediction,
            "status": "success",
            "features_received": features_array
        }

    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict/confidence")
async def predict_price_with_confidence(request: HouseFeaturesArray | HouseFeatures):
    """Predict house price with confidence interval (accepts both array and object format)"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    try:
        # Convert to dict based on input type
        if isinstance(request, HouseFeaturesArray):
            input_data = request.to_dict()
            features_array = request.features
        else:
            input_data = request.model_dump()
            # Convert dict to array for features_received
            features_array = [
                input_data["MedInc"], input_data["HouseAge"], input_data["AveRooms"],
                input_data["AveBedrms"], input_data["Population"], input_data["AveOccup"],
                input_data["Latitude"], input_data["Longitude"]
            ]

        # Make prediction with confidence
        result = predictor.predict_with_confidence(input_data)

        # Add features_received and status
        result["features_received"] = features_array
        result["status"] = "success"

        return result

    except Exception as e:
        logger.error(f"Prediction with confidence failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)