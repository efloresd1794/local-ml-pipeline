import joblib
import numpy as np
import pandas as pd
from loguru import logger
import mlflow.sklearn

class HousePricePredictor:
    def __init__(self, model_path=None, model_name=None, model_version=None):
        """
        Initialize predictor with either local model or MLflow model
        """
        self.scaler = joblib.load('data/processed/scaler.pkl')
        
        if model_path:
            self.model = joblib.load(model_path)
            logger.info(f"Loaded local model from {model_path}")
        elif model_name:
            # Load from MLflow registry
            model_uri = f"models:/{model_name}/{model_version or 'latest'}"
            self.model = mlflow.sklearn.load_model(model_uri)
            logger.info(f"Loaded MLflow model: {model_uri}")
        else:
            # Default to latest random forest model
            self.model = joblib.load('models/random_forest_model.pkl')
            logger.info("Loaded default random forest model")
    
    def preprocess_input(self, input_data):
        """Preprocess input data for prediction"""
        # Convert to DataFrame if necessary
        if isinstance(input_data, dict):
            df = pd.DataFrame([input_data])
        else:
            df = pd.DataFrame(input_data)
        
        # Feature engineering (same as training)
        df['rooms_per_household'] = df['AveRooms'] / df['AveOccup'] 
        df['bedrooms_per_room'] = df['AveBedrms'] / df['AveRooms']
        df['population_per_household'] = df['Population'] / df['AveOccup']
        
        # Scale features
        X_scaled = self.scaler.transform(df)
        
        return X_scaled
    
    def predict(self, input_data):
        """Make prediction"""
        try:
            X_processed = self.preprocess_input(input_data)
            prediction = self.model.predict(X_processed)
            
            # Convert to Python float for JSON serialization
            if len(prediction) == 1:
                return float(prediction[0])
            return [float(p) for p in prediction]
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise

    def predict_with_confidence(self, input_data, n_estimators=None):
        """Make prediction with confidence interval (for ensemble models)"""
        if hasattr(self.model, 'estimators_'):
            X_processed = self.preprocess_input(input_data)
            
            # Get predictions from all estimators
            predictions = np.array([
                estimator.predict(X_processed) 
                for estimator in self.model.estimators_
            ])
            
            mean_pred = np.mean(predictions, axis=0)
            std_pred = np.std(predictions, axis=0)
            
            return {
                'prediction': float(mean_pred[0]) if len(mean_pred) == 1 else mean_pred.tolist(),
                'confidence_interval': {
                    'lower': float(mean_pred[0] - 1.96 * std_pred[0]) if len(mean_pred) == 1 else (mean_pred - 1.96 * std_pred).tolist(),
                    'upper': float(mean_pred[0] + 1.96 * std_pred[0]) if len(mean_pred) == 1 else (mean_pred + 1.96 * std_pred).tolist()
                }
            }
        else:
            # For non-ensemble models, return simple prediction
            return {'prediction': self.predict(input_data)}