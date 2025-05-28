import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.datasets import fetch_california_housing
import os
import joblib
from loguru import logger

class DataPipeline:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def load_data(self):
        """Load California housing dataset"""
        logger.info("Loading California housing dataset...")
        
        # Load dataset
        housing = fetch_california_housing()
        df = pd.DataFrame(housing.data, columns=housing.feature_names)
        df['target'] = housing.target
        
        # Save raw data
        os.makedirs('data/raw', exist_ok=True)
        df.to_csv('data/raw/housing_data.csv', index=False)
        
        logger.info(f"Dataset loaded with shape: {df.shape}")
        return df
    
    def preprocess_data(self, df, is_training=True):
        """Preprocess the data"""
        logger.info("Preprocessing data...")
        
        # Handle missing values (if any)
        df = df.dropna()
        
        # Feature engineering
        df['rooms_per_household'] = df['AveRooms'] / df['AveOccup'] 
        df['bedrooms_per_room'] = df['AveBedrms'] / df['AveRooms']
        df['population_per_household'] = df['Population'] / df['AveOccup']
        
        # Separate features and target
        X = df.drop('target', axis=1)
        y = df['target']
        
        # Scale features
        if is_training:
            X_scaled = self.scaler.fit_transform(X)
            # Save scaler
            os.makedirs('data/processed', exist_ok=True)
            joblib.dump(self.scaler, 'data/processed/scaler.pkl')
        else:
            X_scaled = self.scaler.transform(X)
            
        return X_scaled, y, X.columns.tolist()
    
    def split_data(self, X, y, test_size=0.2, random_state=42):
        """Split data into train/test sets"""
        logger.info("Splitting data...")
        return train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    def run_pipeline(self):
        """Run complete data pipeline"""
        logger.info("Starting data pipeline...")
        
        # Load data
        df = self.load_data()
        
        # Preprocess
        X, y, feature_names = self.preprocess_data(df, is_training=True)
        
        # Split data
        X_train, X_test, y_train, y_test = self.split_data(X, y)
        
        # Save processed data
        processed_data = {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'feature_names': feature_names
        }
        
        joblib.dump(processed_data, 'data/processed/processed_data.pkl')
        
        logger.info("Data pipeline completed successfully!")
        return processed_data

if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.run_pipeline()