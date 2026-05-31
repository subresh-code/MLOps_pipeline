# CMP6230 MLOps Pipeline for IEEE-CIS Fraud Detection

A data management and machine learning operations pipeline for credit card fraud detection using the IEEE-CIS Fraud Detection dataset. The pipeline implements five standard MLOps stages — Data Ingestion, Data Preprocessing, Model Development, Model Deployment, and Model Monitoring — using XGBoost, FastAPI, MLflow, Docker, and Evidently.

## Dataset

**Source**: [IEEE-CIS Fraud Detection](https://www.kaggle.com/c/ieee-fraud-detection/data) on Kaggle.

The pipeline expects the following raw CSV files inside `data/raw/`:

| File | Description |
|------|-------------|
| `train_transaction.csv` | Transaction-level features (590,540 rows, 394 columns) |
| `train_identity.csv` | Identity/vendor features (144,233 rows, 41 columns) |

These files are **not included** in the submission ZIP due to their size (the dataset is approximately 1 GB combined). They must be downloaded from Kaggle and placed in `data/raw/` before running the training pipeline.

The dataset contains 590,540 anonymised transactions with a 3.5 % fraud rate (approximately 27:1 class imbalance).

## Pipeline Stages

| Stage | Module | Description |
|-------|--------|-------------|
| Data Ingestion | `src.data_processing` | Loads CSV files, validates schema, performs LEFT JOIN on `TransactionID`, saves ingestion summary |
| Data Preprocessing | `src.preprocessing` | Fits label encoders, median imputation, and column alignment on the training split only |
| Model Development | `src.train` | Trains an XGBoost classifier with `scale_pos_weight=20`, logs metrics and artefacts to MLflow |
| Model Deployment | `src.api` | Serves predictions via FastAPI, containerised with Docker and Docker Compose |
| Model Monitoring | `src.monitor` | Compares reference and current data distributions using Evidently's `DataDriftPreset` |

## Installation

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate            # Windows
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Download the dataset

1. Download the IEEE-CIS Fraud Detection dataset from [Kaggle](https://www.kaggle.com/c/ieee-fraud-detection/data)
2. Place `train_transaction.csv` and `train_identity.csv` inside `data/raw/`
3. The directory should look like:

```
data/raw/
├── train_transaction.csv
└── train_identity.csv
```

## Main Commands

All common operations are available as `make` targets:

| Command | Description |
|---------|-------------|
| `make train` | Run data processing, model training, and log results to MLflow |
| `make evaluate` | Generate evaluation metrics, classification report, and figures |
| `make monitor` | Run Evidently data-drift monitoring and generate an HTML report |
| `PYTHONPATH=. python -m src.evaluate` | Equivalent to `make evaluate` |
| `PYTHONPATH=. python -m src.monitor` | Equivalent to `make monitor` |
| `make serve` | Start the FastAPI locally at `http://localhost:8000` |
| `make test` | Run tests with pytest |
| `make lint` | Lint source and test files with ruff |
| `make docker-up` | Build and start API + MLflow UI with Docker Compose |
| `make docker-down` | Stop Docker Compose services |
| `make mlflow-ui` | Start a standalone MLflow tracking UI on port 5000 |
| `make clean` | Remove processed data, model artefacts, and MLflow runs |

### Running ad hoc

```bash
# Full pipeline (ingestion → preprocessing → training)
make train

# Evaluate the trained model
PYTHONPATH=. python -m src.evaluate

# Run drift monitoring
PYTHONPATH=. python -m src.monitor

# Serve the API locally
PYTHONPATH=. uvicorn src.api:app --reload
```

## Generated Outputs

After running the pipeline, the following artefacts are produced:

| Path | Description |
|------|-------------|
| `data/processed/train.parquet` | Preprocessed training set (472,432 rows) |
| `data/processed/test.parquet` | Preprocessed test set (118,108 rows) |
| `data/processed/reference_data.parquet` | Reference sample for drift monitoring |
| `models/model.joblib` | Trained XGBoost classifier |
| `models/preprocessing_artifacts.joblib` | Fitted encoders, medians, and column order |
| `models/metrics.json` | Evaluation metrics (AUC, F1, precision, recall) |
| `models/label_encoders.joblib` | Per-column label encoders |
| `reports/figures/confusion_matrix.png` | Confusion matrix plot |
| `reports/figures/roc_curve.png` | ROC curve plot |
| `reports/figures/pr_curve.png` | Precision-recall curve plot |
| `reports/figures/feature_importance.png` | XGBoost feature importance plot |
| `reports/metrics/evaluation_metrics.json` | Full evaluation metrics summary |
| `reports/metrics/classification_report.txt` | Scikit-learn classification report |
| `reports/metrics/ingestion_summary.json` | Ingestion validation summary |
| `reports/monitoring/drift_report.html` | Evidently data-drift HTML report |
| `reports/monitoring/drift_summary.json` | Drift summary in JSON format |

## API Endpoints

The FastAPI application exposes the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Returns API status and whether the model is loaded |
| `/model-info` | GET | Returns model type, expected features, and performance metrics |
| `/predict` | POST | Accepts a JSON transaction payload and returns `fraud_probability`, `is_fraud`, and `confidence` |
| `/docs` | GET | Interactive Swagger UI documentation |

Example prediction request:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "TransactionAmt": 500.0,
    "ProductCD": "W",
    "card4": "visa",
    "P_emaildomain": "gmail.com"
  }'
```

Example response:

```json
{"fraud_probability": 0.526, "is_fraud": true, "confidence": 0.526}
```

## Testing

Tests are written using pytest and cover the three main components:

```bash
make test
# or
pytest tests/ -v --tb=short
```

| Test file | Scope |
|-----------|-------|
| `tests/test_data_processing.py` | Data loading, schema validation, train/test split, ingestion summary |
| `tests/test_predict.py` | Preprocessing pipeline, feature engineering, prediction output |
| `tests/test_api.py` | API endpoints, health check, prediction route, error handling |

## Deployment

### Local (Docker Compose)

```bash
make docker-up
```

Starts two containers:
- **API** (`fraud-detection-api`) on port 8000
- **MLflow** (`mlflow-server`) on port 5000

### FastAPI (standalone)

```bash
make serve
# or
PYTHONPATH=. uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### GCP Cloud Run

The API can be deployed to Google Cloud Run. A `.gcloudignore` file is included for artefact filtering.

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/fraud-detection-api
gcloud run deploy fraud-detection-api \
  --image gcr.io/YOUR_PROJECT_ID/fraud-detection-api \
  --platform managed --region us-central1 --port 8000 --memory 1Gi --allow-unauthenticated
```

### CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on push to `main`: lint (ruff) → test (pytest) → Docker build verification.

## Experiment Tracking

MLflow tracks each training run. To view experiment history:

```bash
make mlflow-ui
# then open http://localhost:5000
```

Or alongside the API via Docker Compose (`make docker-up`).

## Optional Airflow Orchestration

A lightweight Apache Airflow DAG is included at `dags/fraud_pipeline_dag.py` as coursework evidence of pipeline orchestration. It runs the four core stages sequentially:

```
ingest_data → train_model → evaluate_model → monitor_drift
```

**Important:** Airflow has many pinned dependencies and may conflict with this project's environment. Install it in an isolated virtual environment or use Airflow's standalone mode.

```bash
# Install Airflow in a separate environment (recommended)
pip install "apache-airflow>=2.10.0"

# Set the AIRFLOW_HOME to the project root for the DAG to be discoverable
export AIRFLOW_HOME=/path/to/MLOps_pipeline

# Start Airflow in standalone mode (scheduler + webserver on port 8080)
airflow standalone

# Trigger the DAG manually
airflow dags trigger fraud_detection_mlops_pipeline
```

Alternatively, from the Airflow web UI (http://localhost:8080):
1. Find the DAG named `fraud_detection_mlops_pipeline`
2. Toggle the switch to unpause it
3. Click the play button (▶ Trigger DAG)

The primary reproducible pipeline remains the Makefile targets.

## Limitations

- **Monitoring is data-drift only**: The monitor uses Evidently's `DataDriftPreset` to compare feature distributions. Performance monitoring (tracking precision, recall, and accuracy over time) requires labelled production data, which is not available in a static dataset context.
- **Production performance monitoring**: Without a live stream of ground-truth labels, the pipeline cannot demonstrate automated performance degradation detection.
- **Schema validation is lightweight**: Column existence and row-count checks are performed at ingestion, but full data-type and range validation is not implemented.
- **No automated retraining**: While drift can be detected, retraining must be triggered manually.
- **Raw Kaggle data must be downloaded separately**: The raw CSVs exceed typical submission size limits and are not included in the ZIP.

## Project Structure

```
├── data/
│   ├── raw/                    # Place train_transaction.csv and train_identity.csv here
│   └── processed/              # Output parquet files (train, test, reference)
├── models/                     # Serialised model and preprocessing artefacts
├── reports/
│   ├── figures/                # Evaluation plots
│   ├── metrics/                # Metrics JSON and ingestion summary
│   └── monitoring/             # Drift reports
├── src/
│   ├── __init__.py
│   ├── config.py               # Paths, hyperparameters, feature lists
│   ├── data_processing.py      # Data loading, validation, train/test split
│   ├── preprocessing.py        # Feature engineering, encoders, imputation
│   ├── train.py                # XGBoost training with MLflow logging
│   ├── evaluate.py             # Model evaluation and figure generation
│   ├── predict.py              # Prediction service (preprocessing + inference)
│   ├── monitor.py              # Evidently data-drift monitoring
│   └── api.py                  # FastAPI application
├── tests/
│   ├── __init__.py
│   ├── test_data_processing.py
│   ├── test_predict.py
│   └── test_api.py
├── dags/
│   └── fraud_pipeline_dag.py     # Optional Airflow orchestration DAG
├── notebooks/
│   └── 01_eda_fraud_detection.ipynb
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── .github/workflows/ci.yml
```
