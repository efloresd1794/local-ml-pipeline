import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import numpy as np
from loguru import logger
import os

class ModelTrainer:
    def __init__(self, experiment_name="house-price-prediction"):
        self.experiment_name = experiment_name
        mlflow.set_experiment(experiment_name)
        
    def train_model(self, X_train, y_train, X_test, y_test, model_type="random_forest"):
        """Train model with MLflow tracking"""
        
        with mlflow.start_run():
            logger.info(f"Training {model_type} model...")
            
            # Choose model
            if model_type == "random_forest":
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                params = {
                    "model_type": "RandomForestRegressor",
                    "n_estimators": 100,
                    "max_depth": 10,
                    "random_state": 42
                }
            else:
                model = LinearRegression()
                params = {
                    "model_type": "LinearRegression"
                }
            
            # Log parameters
            mlflow.log_params(params)
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # Calculate metrics
            train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            
            # Log metrics
            metrics = {
                "train_rmse": train_rmse,
                "test_rmse": test_rmse,
                "train_r2": train_r2,
                "test_r2": test_r2,
                "test_mae": test_mae
            }
            mlflow.log_metrics(metrics)
            
            # Log model
            mlflow.sklearn.log_model(
                model, 
                "model",
                registered_model_name=f"house-price-{model_type}"
            )
            
            # Save model locally
            os.makedirs('models', exist_ok=True)
            joblib.dump(model, f'models/{model_type}_model.pkl')
            
            logger.info(f"Model training completed. Test RMSE: {test_rmse:.4f}, Test R2: {test_r2:.4f}")
            
            return model, metrics

def main():
    # Load processed data
    data = joblib.load('data/processed/processed_data.pkl')
    X_train, X_test = data['X_train'], data['X_test']
    y_train, y_test = data['y_train'], data['y_test']
    
    # Initialize trainer
    trainer = ModelTrainer()
    
    # Train different models
    models = {}
    for model_type in ['random_forest', 'linear_regression']:
        model, metrics = trainer.train_model(
            X_train, y_train, X_test, y_test, model_type
        )
        models[model_type] = {'model': model, 'metrics': metrics}
    
    logger.info("All models trained successfully!")
    return models

if __name__ == "__main__":
    main()