# CMP6230 MLOps Pipeline — IEEE-CIS Fraud Detection

A full MLOps pipeline for credit card fraud detection using the IEEE-CIS Fraud Detection dataset. Implements five standard MLOps stages — Data Ingestion, Preprocessing, Model Training, Deployment, and Monitoring — with XGBoost, FastAPI, MLflow, MariaDB ColumnStore, Redis, Evidently, Docker Compose, and a React dashboard.

## Dataset

**Source**: [IEEE-CIS Fraud Detection](https://www.kaggle.com/c/ieee-fraud-detection/data) (Kaggle)

Place the following raw CSV files in `data/raw/` before running the pipeline:

| File | Rows | Columns |
|------|------|---------|
| `train_transaction.csv` | 590,540 | 394 |
| `train_identity.csv` | 144,233 | 41 |

The dataset contains 590,540 anonymised transactions with a **3.5% fraud rate** (≈27:1 class imbalance). The two files are joined on `TransactionID` (LEFT JOIN) to produce a single 435-feature table.

> Raw CSVs are not included in the repo (~1 GB combined). Download from Kaggle and place in `data/raw/`.

## Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Orchestration | Apache Airflow DAG | End-to-end pipeline scheduling |
| Experiment tracking | MLflow | Metrics, parameters, artefact versioning |
| Serving | FastAPI + Docker | REST prediction API with Redis caching |
| Analytical store | MariaDB ColumnStore | Columnar SQL queries on processed data |
| Caching | Redis | Prediction result caching (TTL 3600s) |
| Monitoring | Evidently | Feature distribution drift detection |
| Frontend | React 18 + Vite + Tailwind | Dashboard for predictions, EDA, metrics, drift |

## Pipeline Stages

| Stage | Module | Description |
|-------|--------|-------------|
| Data Ingestion | `src.data_processing` | Load CSVs, validate schema, LEFT JOIN on `TransactionID`, save Parquet |
| Preprocessing | `src.preprocessing` | Median imputation, label encoding, leakage-safe fit-on-train-only |
| Model Training | `src.train` | XGBoost with `scale_pos_weight=20`, logged to MLflow |
| Evaluation | `src.evaluate` | AUC-ROC, F1, precision, recall; confusion matrix, ROC, PR curve, feature importance |
| Deployment | `src.api` | FastAPI with Redis-cached `/predict`; static EDA and report figure serving |
| Monitoring | `src.monitor` | Evidently `DataDriftPreset` against reference data; supports custom current-data path |
| Drift Simulation | `src.generate_drift_data` | Three synthetic drift scenarios (A/B/C) for monitoring demonstration |
| Analytical Queries | `src.analytics` | Load processed data into MariaDB ColumnStore; run fraud-rate SQL queries |

## Quick Start

### Automated (recommended) — two commands

After cloning, the entire pipeline runs hands-off in Docker via Airflow. You only
need Docker and a Kaggle API token (the raw data is ~1.3 GB and not committed).

```bash
# 1. Provide a Kaggle token (https://www.kaggle.com/settings -> API -> Create New Token)
export KAGGLE_API_TOKEN=KGAT_xxxxxxxxxxxxxxxx     # or save it to ~/.kaggle/access_token

# 2. Download the raw dataset into data/raw/
./download_data.sh

# 3. Build Airflow, trigger the DAG, and run all stages end-to-end:
#    ingest -> preprocess -> train -> evaluate -> generate_drift -> monitor
./run_pipeline.sh
```

`run_pipeline.sh` options: `--no-wait` (trigger and return), `--full-stack` (also
start the API, frontend, Redis, MariaDB, and MLflow). The Airflow UI is at
http://localhost:8080 (admin/admin).

### Manual (step by step)

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Download the dataset

Download `train_transaction.csv` and `train_identity.csv` from [Kaggle](https://www.kaggle.com/c/ieee-fraud-detection/data) and place them in `data/raw/`.

### 4. Run the full pipeline

```bash
make train        # ingest → preprocess → train (logs to MLflow)
make evaluate     # evaluation metrics + figures
make monitor      # drift report against reference data
```

### 5. Start all services

```bash
docker compose up --build
```

Services:

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | FastAPI prediction service |
| Frontend | http://localhost:3000 | React dashboard |
| MLflow | http://localhost:5001 | Experiment tracking UI |
| MariaDB ColumnStore | localhost:3307 | Columnar analytical DB |
| Redis | localhost:6380 | Prediction cache |

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make train` | Full pipeline: ingest → preprocess → train |
| `make evaluate` | Model evaluation + figures |
| `make monitor` | Drift monitoring (train vs test) |
| `make serve` | Start FastAPI locally on port 8000 |
| `make docker-up` | Build and start all Docker Compose services |
| `make docker-down` | Stop all services |
| `make load-columnstore` | Load processed Parquet data into MariaDB ColumnStore |
| `make generate-drift` | Generate all three drift scenario Parquet files |
| `make monitor-drift SCENARIO=a` | Run drift monitor against scenario a, b, or c |
| `make frontend-install` | `npm install` inside `frontend/` |
| `make frontend-dev` | Start Vite dev server locally on port 5173 |
| `make mlflow-ui` | Start standalone MLflow UI on port 5000 |
| `make test` | Run pytest |
| `make lint` | Lint with ruff |
| `make clean` | Remove processed data, model artefacts, and MLflow runs |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | API status, model loaded flag, Redis connected flag |
| `/model-info` | GET | Model type, feature count, metrics |
| `/predict` | POST | Fraud prediction; returns `fraud_probability`, `is_fraud`, `confidence`, `cached` |
| `/eda-summary` | GET | EDA summary stats from `notebooks/eda_summary.json` |
| `/metrics` | GET | Training and evaluation metrics |
| `/drift-summary` | GET | Drift summary JSON; `?scenario=a\|b\|c` for synthetic scenarios |
| `/analytics/queries` | GET | Run ColumnStore SQL queries and return results |
| `/eda-figures` | GET | List available EDA figure filenames |
| `/report-figures` | GET | List available report figure filenames |
| `/static/eda/<file>` | GET | Serve EDA figures from `notebooks/figures/` |
| `/static/reports/<file>` | GET | Serve report figures from `reports/figures/` |
| `/docs` | GET | Swagger UI |

Example prediction request:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"TransactionAmt": 500.0, "ProductCD": "W", "card4": "visa", "P_emaildomain": "gmail.com"}'
```

Example response:

```json
{"fraud_probability": 0.526, "is_fraud": true, "confidence": 0.526, "cached": false}
```

A second identical request returns `"cached": true` (Redis hit).

## Drift Simulation

Three synthetic drift scenarios are generated from the training reference data:

| Scenario | Type | Description |
|----------|------|-------------|
| A | Feature / data drift | `TransactionAmt × 1.5`; top 20 numeric features shifted by +2σ |
| B | Concept drift | 15% of legitimate transactions randomly relabelled as fraud |
| C | Covariate shift | All identity columns (`id_01`–`id_38`, `DeviceType`, `DeviceInfo`) dropped |

```bash
make generate-drift             # generates drifted_a/b/c.parquet in data/processed/
make monitor-drift SCENARIO=a   # run Evidently against scenario A
```

Drift scenario reports are saved to `reports/monitoring/drift_summary_<scenario>.json` and are also accessible via `/drift-summary?scenario=a`.

## MariaDB ColumnStore

Processed data can be loaded into MariaDB ColumnStore for columnar SQL analytics:

```bash
make load-columnstore
```

This runs `src/analytics.py` which:
1. Reads `data/processed/train.parquet` and `test.parquet`
2. Infers the DDL from Parquet column dtypes (float64 → DOUBLE, int64 → BIGINT)
3. Creates `fraud_transactions` with `ENGINE=ColumnStore`
4. Loads data in chunks of 5,000 rows
5. Runs five pre-built analytical queries (fraud rate by product, amount by fraud status, fraud by card type, C-feature comparison, summary stats)

The `/analytics/queries` API endpoint runs these queries on demand.

## Frontend

The React dashboard (React 18, Vite 5, Tailwind CSS, Axios, React Router v6) has five pages:

| Page | Path | Description |
|------|------|-------------|
| Predict | `/` | Transaction form with fraud probability bar and Redis cache indicator |
| EDA | `/eda` | Summary stats and EDA figures |
| Metrics | `/metrics` | Model performance metrics and evaluation plots |
| Monitor | `/monitor` | Drift summary table with p-values; scenario selector (A/B/C) |
| Analytics | `/analytics` | ColumnStore SQL query results |

Run locally (without Docker):

```bash
make frontend-install
make frontend-dev       # http://localhost:5173
```

## Generated Artefacts

| Path | Description |
|------|-------------|
| `data/processed/train.parquet` | Preprocessed training set (472,432 rows, 119 columns) |
| `data/processed/test.parquet` | Preprocessed test set (118,108 rows) |
| `data/processed/reference_data.parquet` | Reference sample for drift monitoring |
| `data/processed/drifted_a.parquet` | Synthetic drift scenario A |
| `data/processed/drifted_b.parquet` | Synthetic drift scenario B |
| `data/processed/drifted_c.parquet` | Synthetic drift scenario C |
| `models/model.joblib` | Trained XGBoost classifier |
| `models/preprocessing_artifacts.joblib` | Fitted encoders, medians, column order |
| `models/metrics.json` | Evaluation metrics |
| `reports/figures/` | Confusion matrix, ROC curve, PR curve, feature importance |
| `reports/metrics/evaluation_metrics.json` | Full evaluation metrics |
| `reports/metrics/classification_report.txt` | Scikit-learn classification report |
| `reports/metrics/ingestion_summary.json` | Ingestion validation summary |
| `reports/monitoring/drift_report.html` | Evidently HTML drift report |
| `reports/monitoring/drift_summary.json` | Drift summary JSON |
| `reports/monitoring/drift_summary_<a\|b\|c>.json` | Per-scenario drift summaries |

## Testing

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

## Optional Airflow Orchestration

A DAG at `dags/fraud_pipeline_dag.py` orchestrates the four core pipeline stages sequentially:

```
ingest_data → train_model → evaluate_model → monitor_drift
```

Install Airflow in a separate environment to avoid dependency conflicts:

```bash
pip install "apache-airflow>=2.10.0"
export AIRFLOW_HOME=/path/to/mlops_pipeline
airflow standalone
airflow dags trigger fraud_detection_mlops_pipeline
```

## Project Structure

```
├── data/
│   ├── raw/                        # train_transaction.csv, train_identity.csv (download separately)
│   ├── processed/                  # Parquet outputs (train, test, reference, drifted_a/b/c)
│   └── sql/
│       └── init_columnstore.sql    # MariaDB ColumnStore DB and user initialisation
├── frontend/                       # React 18 + Vite + Tailwind dashboard
│   ├── src/
│   │   ├── pages/                  # Predict, EDA, Metrics, Monitor, Analytics
│   │   ├── components/             # Navbar, StatCard
│   │   └── api/index.js            # Axios API client
│   ├── Dockerfile
│   └── vite.config.js
├── models/                         # Serialised model and preprocessing artefacts
├── notebooks/
│   └── 01_eda_fraud_detection.ipynb
├── reports/
│   ├── figures/                    # Evaluation plots
│   ├── metrics/                    # Metrics JSON and classification report
│   └── monitoring/                 # Evidently HTML + JSON drift reports
├── src/
│   ├── config.py                   # Paths, hyperparameters, Redis/ColumnStore config
│   ├── data_processing.py          # CSV loading, validation, LEFT JOIN, Parquet output
│   ├── preprocessing.py            # Imputation, label encoding (fit-on-train-only)
│   ├── train.py                    # XGBoost training with MLflow logging
│   ├── evaluate.py                 # Metrics, plots
│   ├── predict.py                  # Inference with preprocessing pipeline
│   ├── api.py                      # FastAPI: /predict (Redis-cached), all endpoints
│   ├── monitor.py                  # Evidently drift monitoring
│   ├── analytics.py                # MariaDB ColumnStore loader and SQL queries
│   └── generate_drift_data.py      # Synthetic drift scenario generator
├── tests/
│   ├── test_data_processing.py
│   ├── test_predict.py
│   └── test_api.py
├── dags/
│   └── fraud_pipeline_dag.py       # Optional Airflow DAG
├── Dockerfile                      # API image
├── docker-compose.yml              # API, MLflow, Redis, MariaDB ColumnStore, Frontend
├── Makefile
├── requirements.txt
└── .github/workflows/ci.yml        # CI: lint → test → Docker build
```

## Limitations

- Monitoring is **data-drift only** — performance monitoring (precision/recall over time) requires ground-truth labels not available in a static dataset context.
- No automated retraining — drift can be detected but retraining must be triggered manually.
- Schema validation is lightweight — column existence and row-count checks only.
- MariaDB ColumnStore requires `privileged: true` in Docker Compose on Linux.
- Raw Kaggle CSVs must be downloaded separately (~1 GB).
