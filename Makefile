PYTHONPATH := .

.PHONY: install train evaluate monitor serve test lint \
        docker-build docker-run docker-up docker-down \
        mlflow-ui clean load-columnstore generate-drift \
        monitor-drift frontend-install frontend-dev

# Install Python dependencies
install:
	pip install -r requirements.txt

# Run data processing and model training
train:
	PYTHONPATH=$(PYTHONPATH) python -m src.data_processing
	PYTHONPATH=$(PYTHONPATH) python -m src.train

# Generate evaluation plots and metrics from trained model
evaluate:
	PYTHONPATH=$(PYTHONPATH) python -m src.evaluate

# Run drift monitoring against default test data
monitor:
	PYTHONPATH=$(PYTHONPATH) python -m src.monitor

# Run drift monitoring against a synthetic scenario (SCENARIO=a|b|c)
monitor-drift:
	@if [ -z "$(SCENARIO)" ]; then \
		echo "Usage: make monitor-drift SCENARIO=a|b|c"; exit 1; \
	fi
	PYTHONPATH=$(PYTHONPATH) python -m src.monitor \
		--current-data data/processed/drifted_$(SCENARIO).parquet \
		--output-json reports/monitoring/drift_summary_$(SCENARIO).json

# Generate synthetic drifted datasets for all three scenarios
generate-drift:
	PYTHONPATH=$(PYTHONPATH) python -m src.generate_drift_data

# Load processed Parquet data into MariaDB ColumnStore
load-columnstore:
	PYTHONPATH=$(PYTHONPATH) python -m src.analytics

# Run the API server locally
serve:
	PYTHONPATH=$(PYTHONPATH) uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	PYTHONPATH=$(PYTHONPATH) pytest tests/ -v --tb=short

# Lint code
lint:
	ruff check src/ tests/

# Build Docker image for the API
docker-build:
	docker build -t fraud-detection-api .

# Run Docker container (API only)
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

# Install frontend dependencies
frontend-install:
	cd frontend && npm install

# Run React dev server (outside Docker)
frontend-dev:
	cd frontend && npm run dev

# Clean artifacts
clean:
	rm -rf data/processed/*
	rm -rf models/*
	rm -rf mlruns/
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
