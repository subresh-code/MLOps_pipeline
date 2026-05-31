PYTHONPATH := .

.PHONY: install train evaluate monitor serve test lint docker-build docker-run clean

# Install dependencies
install:
	pip install -r requirements.txt

# Run data processing and model training
train:
	PYTHONPATH=$(PYTHONPATH) python -m src.data_processing
	PYTHONPATH=$(PYTHONPATH) python -m src.train

# Generate evaluation plots and metrics from trained model
evaluate:
	PYTHONPATH=$(PYTHONPATH) python -m src.evaluate

# Run drift monitoring to generate HTML report and JSON summary
monitor:
	PYTHONPATH=$(PYTHONPATH) python -m src.monitor

# Run the API server locally
serve:
	PYTHONPATH=$(PYTHONPATH) uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	PYTHONPATH=$(PYTHONPATH) pytest tests/ -v --tb=short

# Lint code
lint:
	ruff check src/ tests/

# Build Docker image
docker-build:
	docker build -t fraud-detection-api .

# Run Docker container
docker-run:
	docker run -p 8000:8000 -v ./models:/app/models fraud-detection-api

# Run full stack with docker-compose
docker-up:
	docker compose up --build

# Stop docker-compose
docker-down:
	docker compose down

# Start MLflow UI
mlflow-ui:
	mlflow server --host 0.0.0.0 --port 5001 --backend-store-uri sqlite:///mlruns/mlflow.db

# Clean artifacts
clean:
	rm -rf data/processed/*
	rm -rf models/*
	rm -rf mlruns/
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
