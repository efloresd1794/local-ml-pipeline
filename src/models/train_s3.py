"""
ML Model Training Script with S3 Upload (LocalStack compatible)
Trains models and uploads artifacts to S3 bucket
"""

import os
import boto3
from botocore.client import Config
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from loguru import logger
import tempfile


class S3ModelTrainer:
    def __init__(self, bucket_name="ml-model-artifacts", use_localstack=True):
        """
        Initialize S3 Model Trainer

        Args:
            bucket_name: S3 bucket name for model artifacts
            use_localstack: If True, configure for LocalStack endpoint
        """
        self.bucket_name = bucket_name
        self.use_localstack = use_localstack

        # Configure S3 client for LocalStack or AWS
        if use_localstack:
            # LocalStack configuration
            self.s3_client = boto3.client(
                's3',
                endpoint_url=os.environ.get('AWS_ENDPOINT_URL', 'http://localhost:4566'),
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'test'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'test'),
                region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                config=Config(signature_version='s3v4')
            )
            logger.info("Configured S3 client for LocalStack")
        else:
            # AWS configuration
            self.s3_client = boto3.client('s3')
            logger.info("Configured S3 client for AWS")

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
        except:
            try:
                if self.use_localstack:
                    # For LocalStack, use simpler create_bucket
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    # For AWS, handle region-specific bucket creation
                    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
                    if region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': region}
                        )
                logger.info(f"Created bucket {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to create bucket: {e}")
                raise

    def upload_artifact(self, local_file, s3_key):
        """Upload file to S3"""
        try:
            self.s3_client.upload_file(local_file, self.bucket_name, s3_key)
            logger.info(f"Uploaded {local_file} to s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {local_file}: {e}")
            return False

    def save_model_to_s3(self, model, model_name):
        """Save model as joblib file and upload to S3"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.joblib') as tmp_file:
            # Save model to temporary file
            joblib.dump(model, tmp_file.name)
            tmp_path = tmp_file.name

        try:
            # Upload to S3
            s3_key = f"models/{model_name}.joblib"
            success = self.upload_artifact(tmp_path, s3_key)

            if success:
                logger.info(f"Model saved to S3: s3://{self.bucket_name}/{s3_key}")

            return success
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def train_model(self, X_train, y_train, X_test, y_test, model_type="random_forest"):
        """Train model and upload to S3"""
        logger.info(f"Training {model_type} model...")

        # Choose model
        if model_type == "random_forest":
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
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

        # Train model
        model.fit(X_train, y_train)
        logger.info(f"Model training completed")

        # Make predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Calculate metrics
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        test_mae = mean_absolute_error(y_test, y_pred_test)

        metrics = {
            "train_rmse": train_rmse,
            "test_rmse": test_rmse,
            "train_r2": train_r2,
            "test_r2": test_r2,
            "test_mae": test_mae
        }

        logger.info(f"Model Metrics - RMSE: {test_rmse:.4f}, R2: {test_r2:.4f}, MAE: {test_mae:.4f}")

        # Save model to S3
        model_name = f"house_price_{model_type}_model"
        self.save_model_to_s3(model, model_name)

        # Also save locally for backup
        os.makedirs('models', exist_ok=True)
        local_path = f'models/{model_type}_model.joblib'
        joblib.dump(model, local_path)
        logger.info(f"Model also saved locally: {local_path}")

        return model, metrics


def main():
    """Main training pipeline"""
    logger.info("Starting ML model training pipeline with S3 storage")

    # Load processed data and scaler
    logger.info("Loading processed data...")
    data = joblib.load('data/processed/processed_data.pkl')
    scaler = joblib.load('data/processed/scaler.pkl')

    X_train, X_test = data['X_train'], data['X_test']
    y_train, y_test = data['y_train'], data['y_test']

    logger.info(f"Training data shape: {X_train.shape}")
    logger.info(f"Test data shape: {X_test.shape}")

    # Initialize S3 trainer
    use_localstack = os.environ.get('USE_LOCALSTACK', 'true').lower() == 'true'
    bucket_name = os.environ.get('MODEL_BUCKET', 'ml-model-artifacts')

    trainer = S3ModelTrainer(bucket_name=bucket_name, use_localstack=use_localstack)

    # Upload scaler to S3 first
    logger.info("Uploading scaler to S3...")
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.joblib') as tmp_file:
        joblib.dump(scaler, tmp_file.name)
        trainer.upload_artifact(tmp_file.name, 'models/scaler.joblib')
        os.remove(tmp_file.name)

    # Train models
    models = {}
    for model_type in ['random_forest', 'linear_regression']:
        logger.info(f"\n{'='*60}")
        logger.info(f"Training {model_type.upper()} model")
        logger.info(f"{'='*60}")

        model, metrics = trainer.train_model(
            X_train, y_train, X_test, y_test, model_type
        )
        models[model_type] = {'model': model, 'metrics': metrics}

    # Display summary
    logger.info(f"\n{'='*60}")
    logger.info("TRAINING SUMMARY")
    logger.info(f"{'='*60}")
    for model_type, data in models.items():
        metrics = data['metrics']
        logger.info(f"\n{model_type.upper()}:")
        logger.info(f"  Test RMSE: {metrics['test_rmse']:.4f}")
        logger.info(f"  Test R2:   {metrics['test_r2']:.4f}")
        logger.info(f"  Test MAE:  {metrics['test_mae']:.4f}")

    logger.info(f"\n{'='*60}")
    logger.info("All models trained and uploaded to S3 successfully!")
    logger.info(f"S3 Bucket: {bucket_name}")
    logger.info(f"{'='*60}")

    return models


if __name__ == "__main__":
    main()
