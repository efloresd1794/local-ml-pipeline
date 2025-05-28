from fastapi import FastAPI, HTTPException
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

@app.post("/predict", response_model=PredictionResponse)
async def predict_price(features: HouseFeatures):
    """Predict house price"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        # Convert to dict
        input_data = features.dict()
        
        # Make prediction
        prediction = predictor.predict(input_data)
        
        return PredictionResponse(prediction=prediction)
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict/confidence", response_model=ConfidencePredictionResponse)
async def predict_price_with_confidence(features: HouseFeatures):
    """Predict house price with confidence interval"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        # Convert to dict
        input_data = features.dict()
        
        # Make prediction with confidence
        result = predictor.predict_with_confidence(input_data)
        
        return ConfidencePredictionResponse(**result)
        
    except Exception as e:
        logger.error(f"Prediction with confidence failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)