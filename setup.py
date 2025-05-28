from setuptools import setup, find_packages

setup(
    name="house-price-ml-pipeline",
    version="1.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "mlflow>=2.8.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
    ],
    author="Edson Flores",
    description="End-to-end ML pipeline for house price prediction by efd",
    python_requires=">=3.8",
)