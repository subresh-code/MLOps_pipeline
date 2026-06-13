# MLOps & Data Analytics Pipeline: Assessment Report

**Module Code:** CMP6230
**Module Title:** Data Management & Machine Learning Operations
**Lecturer:** Rupak Koirala
**Student Name:** Subresh Thakulla
**Student Number:** 23189651
**Date:** June 2026

---

## Abstract

This report documents the planning, design, implementation and evaluation of an end-to-end Machine Learning Operations (MLOps) pipeline for financial fraud detection using the IEEE-CIS Fraud Detection dataset (Vesta Corporation, 2019). Three candidate datasets were evaluated before selecting the IEEE-CIS data, which comprises 590,540 anonymised e-commerce transactions with a 3.5% fraud rate and presents authentic data-management challenges including severe class imbalance (27:1), multi-table schema design, and the risk of concept drift in production.

The pipeline implements five logical stages — data ingestion, pre-processing, model development, deployment, and monitoring — supported by a four-tier storage architecture of raw CSV, Snappy-compressed Parquet, MariaDB ColumnStore, and a Redis prediction cache. An XGBoost classifier trained with cost-sensitive weighting (`scale_pos_weight=20`) achieved an AUC-ROC of 0.943 on a temporally-ordered held-out test set (the later 20% of transactions by `TransactionDT`), reflecting a methodologically rigorous time-based evaluation. The batch pipeline is orchestrated by Apache Airflow, while the serving stack (FastAPI, Redis, MariaDB ColumnStore, MLflow, React) is containerised with Docker Compose. Feature drift is monitored with Evidently AI across three synthetic scenarios. A central theme of this report is the **reflective comparison between the original Summative Draft Plan and the delivered implementation** — every significant deviation (LightGBM → XGBoost, SMOTE → cost-sensitive weighting, Streamlit → React, Parquet-only → multi-tier storage) is documented and justified. Ethical and legal dimensions are evaluated under the UK GDPR and the Data Protection Act 2018.

**Keywords:** MLOps, Fraud Detection, XGBoost, MariaDB ColumnStore, Redis, Evidently, FastAPI, Docker, MLflow, GDPR

---

## 1. Introduction

Financial fraud represents one of the most consequential and technically challenging problems in applied machine learning. In the United Kingdom alone, fraud accounted for over £1.2 billion in losses in 2023, with e-commerce card fraud forming a significant proportion (UK Finance, 2023). Yet detecting fraud is not simply a modelling problem — as Sculley et al. (2015) observed, the code required to build a model is minuscule compared to the infrastructure required to verify, ingest, and manage the data surrounding it. This distinction between a model and a production-grade *system* is the central concern of Machine Learning Operations (MLOps).

This report documents the end-to-end planning, design, implementation and evaluation of an MLOps pipeline applied to the IEEE-CIS Fraud Detection dataset (Vesta Corporation, 2019). The work covers four areas aligned to the module learning outcomes: (1) the planning and design of a data storage and pipeline architecture, (2) the implementation of that pipeline including ingestion, preprocessing, model training, serving, and monitoring, (3) exploratory data analysis and drift detection, and (4) an evaluation of the ethical and legal dimensions of operating a fraud detection system.

Crucially, this is a *log report*: it tracks the iterative journey from an initial plan to a working system. The pipeline as built deviates from the original Summative Draft Plan in several deliberate ways, and a recurring objective of this document is to **justify what was planned against what was implemented**, explaining each deviation as an engineering decision rather than an oversight.

---

## 2. Identification of Candidate Source Data

Selecting an appropriate dataset is a foundational decision in any MLOps pipeline. According to Breck et al. (2017), data quality and structural complexity directly determine the difficulty of building reliable production systems. Three candidate datasets were evaluated across five criteria: the presence of a defined ML target, structural complexity, data quality challenges, MLOps relevance, and manageable scale.

### 2.1 Candidate 1: IEEE-CIS Fraud Detection

Provided by Vesta Corporation and hosted on Kaggle (2019), this dataset contains 590,540 anonymised e-commerce transactions labelled with a binary fraud indicator (`isFraud`). A separate identity table records device and network attributes for a subset of transactions, linked by `TransactionID`. The join strategy between these two tables is a concrete data-management decision with real downstream consequences: an inner join silently discards all transactions lacking identity records, potentially introducing selection bias (Sculley et al., 2015).

**Table 1 — IEEE-CIS Fraud Detection Dataset Characteristics**

| Attribute | Description |
|---|---|
| Transaction records | 590,540 labelled e-commerce transactions |
| Identity records | 144,233 optional device/network records |
| Fraud rate | ≈3.5% (27:1 class imbalance) |
| Total features | 434 after transaction–identity LEFT JOIN |
| Source format | Flat CSV files (two separate tables) |
| ML task | Binary classification (`isFraud`) |
| Key challenge | Class imbalance, missingness, concept drift |

*[Figure: `erd_ieee_cis.png` — Entity–Relationship Diagram for the IEEE-CIS Fraud Detection Dataset]*

### 2.2 Candidate 2: Rossmann Store Sales

The Rossmann Store Sales dataset (Kaggle, 2015) contains daily sales figures for 1,115 German pharmacy stores. The task is univariate regression — predicting future store sales from historical promotions, holidays, and store-type features. Although well-structured, it presents limited MLOps challenges: the target is continuous and stable, there is no meaningful concept drift, and data arrives as a simple two-table join on a composite key of (Store, Date).

**Table 2 — Rossmann Store Sales Dataset Characteristics**

| Attribute | Description |
|---|---|
| Records | ≈1,017,209 daily store entries |
| Stores | 1,115 pharmacy outlets across Germany |
| ML task | Regression (predict daily sales) |
| Source format | Two CSV files joined on (Store, Date) |
| Key challenge | Seasonal patterns, minor missingness |
| MLOps relevance | Low — stable seasonal target, no drift risk |

*[Figure: `erd_rossmann.png` — Schema Diagram: Rossmann Store Sales Dataset]*

### 2.3 Candidate 3: NYC TLC Trip Record Data

The NYC Taxi and Limousine Commission Trip Record dataset (NYC TLC, 2024) contains taxi and ride-hailing journey records partitioned into monthly Parquet files. At billions of rows per year, the scale is extreme for a prototype system. Critically, the dataset has no predefined ML target variable — a meaningful supervised learning problem would require substantial additional engineering before any modelling could begin.

**Table 3 — NYC TLC Trip Record Dataset Characteristics**

| Attribute | Description |
|---|---|
| Records | Billions of rows per year |
| File format | Monthly Parquet files, flat structure |
| ML task | None predefined — requires formulation |
| Key challenge | Extreme scale, no ground-truth ML label |
| MLOps relevance | Low — no natural monitoring target |

*[Figure: `flat_file_nyctlc.png` — Flat-File Structure: NYC TLC Trip Record Dataset]*

---

## 3. Selection of Source Data

### 3.1 Comparative Decision Matrix

**Table 4 — Dataset Selection Decision Matrix**

| Criterion | IEEE-CIS | Rossmann | NYC TLC |
|---|---|---|---|
| Defined ML target | **High** — binary fraud label with ground truth | Medium — regression label | **Low** — no predefined target |
| Multi-entity structure | **High** — two related tables, real JOIN decision | Medium — simple two-table join | **Low** — flat file only |
| Data quality challenges | **High** — imbalance, missingness, anonymisation | Medium — minor missingness | Medium — scale only |
| MLOps / drift relevance | **High** — fraud patterns evolve | **Low** — stable seasonal patterns | **Low** — no monitoring target |
| Manageable scale | **High** — 590k rows, fits in memory | **High** — ≈1M rows | **Low** — billions of rows/year |
| **Overall** | **Selected** | Not selected | Not selected |

### 3.2 Justification of Selection

The IEEE-CIS Fraud Detection dataset was selected for three reasons. First, it provides a clearly defined binary classification target with reliable ground truth, unlike the NYC TLC data which requires the practitioner to invent a supervised learning objective. Second, the optional join between the transaction and identity tables introduces a concrete, consequential data-management decision: using an inner join silently discards the 446,307 transactions with no identity record, introducing selection bias that would be undetectable once the pipeline runs (Sculley et al., 2015). A LEFT JOIN preserves all 590,540 transactions, treating missing identity columns as a legitimate signal. Third, the 27:1 class imbalance and the tendency for fraud patterns to evolve over time mean the dataset naturally surfaces the two most important MLOps challenges — handling skewed distributions and detecting model degradation through drift monitoring (Klaise et al., 2020).

### 3.3 Leveraging the Dataset for Machine Learning

**Table 5 — Mapping Dataset Properties to Pipeline Requirements**

| Dataset Property | Pipeline Implication |
|---|---|
| Binary `isFraud` label | Direct binary classification; precision–recall trade-off critical |
| 27:1 class imbalance | Cost-sensitive training (`scale_pos_weight=20`); AUC-ROC and Average Precision as primary metrics |
| Two-table CSV format | ETL ingestion with LEFT JOIN; schema validation on merge |
| High missingness in identity cols | Median imputation for numerics; sentinel encoding for categoricals |
| 434 raw features | Feature selection; label encoding for tree-based models |
| Evolving fraud patterns | Feature drift monitoring with Evidently; synthetic drift scenarios |

---

## 4. Data Storage Planning and Design

### 4.1 Source Data Characteristics

The IEEE-CIS dataset is delivered as two flat CSV files. Although CSV is universally portable, it is poorly suited to analytical workloads: a query scanning 434 columns must read every byte of every row, generating unnecessary I/O.

**Table 6 — Physical Composition of Source Data**

| File | Rows | Columns | Size (approx.) |
|---|---|---|---|
| `train_transaction.csv` | 590,540 | 394 | 543 MB |
| `train_identity.csv` | 144,233 | 41 | 33 MB |
| **Merged (LEFT JOIN)** | **590,540** | **434** | **≈576 MB** |
| After preprocessing | 590,540 | 119 | — |

### 4.2 Proposed Multi-Tier Storage Architecture

A single storage format cannot serve all consumers equally. Raw data must be preserved for reproducibility; the ML pipeline needs fast columnar reads; the serving layer requires sub-millisecond response times. A four-tier architecture addresses each concern.

*[Figure: `storage_tiers.png` — Four-Tier Storage Architecture: Raw CSV → Parquet → MariaDB ColumnStore → Redis]*

**Table 7 — Storage Tier Summary**

| Tier | Technology | Purpose | Consumer |
|---|---|---|---|
| Raw | CSV (flat file) | Source of truth; reproducibility | Data engineers |
| Processed | Parquet (Snappy) | Columnar ML training and evaluation | Data scientists |
| Analytical | MariaDB ColumnStore | SQL-based fraud-rate analytics | Analysts, BI |
| Cache | Redis (TTL 3600s) | Sub-millisecond prediction serving | API, end users |

> **Plan vs implementation note:** The Summative Draft Plan proposed a Parquet-only storage strategy. During implementation this was expanded to four tiers by adding MariaDB ColumnStore (a true columnar analytical engine) and Redis (a key-value cache). This directly satisfies the Exercise 2 requirement to use "Column-oriented datastores and Key-Value data stores," and provides a SQL-accessible analytical path for the Data Science / Analyst consumer that Parquet alone could not.

### 4.3 Logical Storage Structure: OBT over Normalised Schemas

**Table 8 — Evaluation of Logical Storage Structures**

| Structure | Benefits | Drawbacks | Verdict |
|---|---|---|---|
| OBT — Denormalised *(chosen)* | ML-ready; no joins at query time; fast columnar scans | Some redundancy; harder to update | **Best for ML** |
| Star Schema | BI-friendly; clean dimension tables | Joins required for ML features | Better for BI |
| Snowflake Schema | Reduced redundancy | Deep joins; ML-unfriendly | Not suitable |
| Normalised 3NF | High integrity; OLTP-focused | Join-heavy; not suited to analytics | Not suitable |

### 4.4 Ingestion Strategy: ETL over ELT

An ETL strategy was selected over ELT. Because the IEEE-CIS data requires a LEFT JOIN, schema validation, type casting, and missing-value treatment *before* it can be safely stored, delaying transformations to the load stage would push all complexity into the ML pipeline and make the stored data inconsistent. ETL ensures only a clean, validated, denormalised Parquet file is persisted.

**Table 9 — ETL vs ELT Evaluation**

| Strategy | Advantages | Disadvantages | Verdict |
|---|---|---|---|
| **ETL** *(chosen)* | Clean data stored; schema validated early; leakage prevented | Less flexible if raw re-use needed | **Selected** |
| ELT | Raw data preserved; suited to cloud warehouses | Transformations deferred; inconsistency risk for ML | Not selected |

---

## 5. MLOps Pipeline Design

The pipeline is structured into five logical stages following the MLOps lifecycle described by Sculley et al. (2015): data ingestion, pre-processing, model development, deployment, and monitoring. Apache Airflow (2023) orchestrates the **batch** stages as a Directed Acyclic Graph (DAG), while the **deployment** stage is realised as a containerised serving stack under Docker Compose.

> **Design vs implementation note:** The logical design describes five stages. The implemented Airflow DAG (`fraud_detection_mlops_pipeline`) contains four tasks — `ingest_data → train_model → evaluate_model → monitor_drift` — because pre-processing is executed within the training task, and deployment is handled outside Airflow by Docker Compose. This is an intentional separation of concerns: Airflow governs the repeatable batch lifecycle, while Docker governs the always-on serving runtime.

*[Figure: `pipeline_stages.png` — MLOps Pipeline Architecture with Apache Airflow Orchestration, Multi-Tier Storage, and Containerised Serving]*

### 5.1 Stage 1 — Data Ingestion

**What:** Raw CSV files are extracted, validated against an expected schema, LEFT JOINed on `TransactionID`, and stored as Snappy-compressed Parquet. An ingestion summary JSON records row counts, fraud rate, and schema version.

**Why:** Schema validation prevents silent failures downstream. The LEFT JOIN preserves all 590,540 transactions, avoiding the selection bias an inner join would introduce by discarding 446,307 transactions with no identity record (Sculley et al., 2015).

**How:** Implemented in `src/data_processing.py` using pandas; summary written to `reports/metrics/ingestion_summary.json`.

### 5.2 Stage 2 — Data Pre-processing

**What:** Median imputation for numeric columns, label encoding for categorical columns, and feature selection reducing 434 raw features to 119 model-ready features.

**Why:** Tree-based models require no missing values in numeric inputs. Fitting encoders and imputers on training data only — and applying them to test data — prevents data leakage (Breck et al., 2017).

**How:** Implemented in `src/preprocessing.py`; fitted transformers serialised to `models/preprocessing_artifacts.joblib`.

### 5.3 Stage 3 — Model Development

**What:** An XGBoost binary classifier is trained on the preprocessed feature matrix. Hyperparameters, metrics, and the serialised artefact are logged to MLflow (2023).

**Why:** Grinsztajn et al. (2022) demonstrate that tree-based models consistently outperform deep learning on tabular data. `scale_pos_weight=20` encodes the 27:1 imbalance directly into the loss function, making oversampling unnecessary.

**How:** Implemented in `src/train.py`; model saved to `models/model.joblib`; evaluation in `src/evaluate.py`.

### 5.4 Stage 4 — Model Deployment

**What:** The trained model is served via a FastAPI REST API, containerised with Docker Compose. A Redis cache stores prediction results by SHA-256 hash of the input (TTL = 3600s).

**Why:** Containerisation ensures reproducible deployment (Breck et al., 2017). The Redis cache reduces latency for repeated identical requests — realistic in payment screening where the same card may be queried repeatedly within seconds.

**How:** Implemented in `src/api.py`; full stack defined in `docker-compose.yml`.

### 5.5 Stage 5 — Model Monitoring

**What:** Evidently AI's `DataDriftPreset` (2023) compares incoming feature distributions against a 5,000-row reference sample from training data. Three synthetic drift scenarios demonstrate monitoring behaviour.

**Why:** Fraud patterns evolve as fraudsters adapt (Klaise et al., 2020). Silent model degradation without monitoring can render a once-accurate model ineffective with no visible error.

**How:** Implemented in `src/monitor.py`; reports saved as HTML and JSON to `reports/monitoring/`.

### 5.6 Pipeline Orchestration

Apache Airflow orchestrates the four batch tasks as a DAG (`dags/fraud_pipeline_dag.py`): `ingest_data → train_model → evaluate_model → monitor_drift`. Each task is a `BashOperator` invoking the corresponding `src/` module. Task dependencies ensure downstream stages never run on stale data, and the monitoring stage can trigger a retraining run if the drift share exceeds the configured threshold of 0.05.

---

## 6. Pipeline Implementation

### 6.1 System Environment and Tools

**Table 10 — System Environment and Software Stack**

| Category | Tool / Version | Purpose |
|---|---|---|
| Language | Python 3.11 | Core pipeline implementation |
| ML framework | XGBoost 2.x | Fraud classifier |
| Data | pandas, PyArrow | Ingestion, transformation, Parquet I/O |
| Experiment tracking | MLflow 2.x | Parameter, metric, artefact logging |
| Serving | FastAPI, Uvicorn | REST prediction API |
| Caching | Redis 7 | Prediction result cache |
| Analytical DB | MariaDB ColumnStore | Columnar SQL on processed data |
| Monitoring | Evidently AI | Feature drift detection |
| Orchestration | Apache Airflow 2.x | DAG-based pipeline scheduling |
| Containerisation | Docker Compose | Multi-service deployment |
| Frontend | React 18 + Vite 5 + Tailwind | Prediction and monitoring dashboard |

### 6.2 Data Ingestion Implementation

The ingestion stage loads both CSVs, validates column presence, merges with a LEFT JOIN, and writes Parquet. A **temporal 80/20 split** is then applied before any fitting: the full merged dataset is sorted ascending by `TransactionDT` (a seconds-since-reference timestamp), and the earlier 80% of transactions form the training set while the later 20% form the held-out test set. This is methodologically critical — random splitting on time-ordered fraud data allows future transaction patterns to appear in training, producing optimistic evaluation metrics that do not reflect real deployment conditions (Klaise et al., 2020). Temporal ordering is the standard evaluation protocol in the IEEE-CIS competition itself.

```python
trans = pd.read_csv("data/raw/train_transaction.csv")
ident = pd.read_csv("data/raw/train_identity.csv")

# LEFT JOIN preserves all 590,540 transactions
merged = trans.merge(ident, on="TransactionID", how="left")

# Temporal split: train on earlier 80%, evaluate on later 20%
df_sorted  = merged.sort_values("TransactionDT").reset_index(drop=True)
split_idx  = int(len(df_sorted) * 0.8)
train      = df_sorted.iloc[:split_idx]
test       = df_sorted.iloc[split_idx:]

train.to_parquet("data/processed/train.parquet", compression="snappy")
test.to_parquet("data/processed/test.parquet",  compression="snappy")
```

**Table 11 — Data Ingestion Validation Checks**

| Check | Condition | Result |
|---|---|---|
| Row count preserved | merged rows = transaction rows (LEFT JOIN) | Pass |
| Split method | Sort ascending by `TransactionDT` → earlier 80% / later 20% | Temporal (no look-ahead) |
| Fraud rate train | Early-period transactions (≥3.0%) | ≈3.5% |
| Fraud rate test | Late-period transactions (may differ from train) | ≈3.5% |
| Key column present | `isFraud`, `TransactionID`, `TransactionDT` | Pass |

### 6.3 Pre-processing Implementation

All transformers are fitted on training data only and persisted, ensuring the serving pipeline applies identical encoding.

```python
medians = X_train.median()
X_train = X_train.fillna(medians)
X_test  = X_test.fillna(medians)   # apply TRAIN medians to test

for col in cat_cols:
    le = LabelEncoder()
    X_train[col] = le.fit_transform(X_train[col].astype(str))
    X_test[col]  = X_test[col].map(
        lambda x: le.transform([x])[0] if x in le.classes_ else -1)
```

### 6.4 Model Training and Evaluation

```python
import mlflow, xgboost as xgb

with mlflow.start_run():
    model = xgb.XGBClassifier(
        scale_pos_weight=20, n_estimators=300, max_depth=7,
        learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        min_child_weight=5, eval_metric="auc", n_jobs=-1)
    model.fit(X_train, y_train)
    mlflow.log_params(model.get_params())
    mlflow.log_metrics({"auc_roc": roc_auc_score(y_test, y_prob)})
    mlflow.sklearn.log_model(model, "model")
```

**Table 12 — Model Evaluation Metrics (Temporal Test Set — later 20% by TransactionDT, ≈118,108 transactions)**

| Metric | Value |
|---|---|
| AUC-ROC | 0.943 |
| Average Precision | 0.661 |
| F1 | 0.458 |
| Precision | 0.323 |
| Recall | 0.790 |

*[Figure: `model_metrics_summary.png` — Model Evaluation Metrics Summary]*
*[Figure: `roc_curve.png` — ROC Curve (AUC = 0.943)]*
*[Figure: `pr_curve.png` — Precision–Recall Curve (AP = 0.661)]*
*[Figure: `confusion_matrix.png` — Confusion Matrix]*
*[Figure: `feature_importance.png` — Top-20 Feature Importances]*

### 6.5 Deployment: FastAPI and Redis Caching

```python
import hashlib, json

def get_cache_key(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

@app.post("/predict")
def predict(payload: PredictRequest):
    key = get_cache_key(payload.dict())
    if (cached := redis_client.get(key)):
        return {**json.loads(cached), "cached": True}
    result = run_inference(payload)
    redis_client.setex(key, 3600, json.dumps(result))
    return {**result, "cached": False}
```

### 6.6 MariaDB ColumnStore Analytical Layer

Processed Parquet is loaded into MariaDB ColumnStore via `src/analytics.py`, enabling SQL aggregation over 590,540 rows. The `ENGINE=ColumnStore` declaration routes storage through the columnar backend (MariaDB, 2023).

```sql
CREATE TABLE IF NOT EXISTS fraud_transactions (
    TransactionID  BIGINT,
    isFraud        TINYINT,
    TransactionAmt DOUBLE,
    ProductCD      VARCHAR(64),
    card4          VARCHAR(64)
    -- ... further columns inferred from Parquet dtypes
) ENGINE=ColumnStore DEFAULT CHARSET=utf8;
```

The `/analytics/queries` endpoint runs five pre-built analytical queries (fraud rate by product, amount by fraud status, fraud by card type, C-feature comparison, summary statistics) on demand.

### 6.7 Reflection: Plan versus Implementation

This subsection directly addresses the Exercise 2 requirement for a reflective discussion comparing the current pipeline to the initial and final plans.

**Table 13 — Plan vs Implementation: Discrepancies and Justifications**

| Component | Original Plan (Draft) | Implemented | Justification for Change |
|---|---|---|---|
| Classifier | LightGBM | **XGBoost** | More direct, interpretable control of class imbalance via `scale_pos_weight`; cleaner `joblib` serialisation integrating with FastAPI. Final AUC-ROC 0.943 validates the choice. |
| Evaluation split | Stratified random 80/20 | **Temporal 80/20 (sort by `TransactionDT`)** | Random splitting on time-ordered fraud data introduces look-ahead bias — future patterns leak into training. Temporal ordering produces an evaluation that reflects real deployment conditions and matches the IEEE-CIS competition's own evaluation protocol (Klaise et al., 2020). |
| Imbalance handling | SMOTE oversampling | **`scale_pos_weight=20`** | At 590k rows, SMOTE adds heavy compute and risks leakage if applied before the split. Cost-sensitive weighting achieves the same effect by reweighting the loss directly. |
| Frontend | Streamlit dashboard | **React 18 + Vite + Tailwind** | Production-grade decoupled frontend with routing, reusable components, and clean separation from the API layer. |
| Storage | Parquet only | **Parquet + MariaDB ColumnStore + Redis** | Adds a SQL-accessible columnar analytics tier and a low-latency key-value serving cache, directly satisfying Exercise 2's datastore requirements. |
| Orchestration scope | "Airflow orchestrates all five stages" | **Airflow orchestrates 4 batch tasks; Docker Compose runs serving** | Separation of concerns: Airflow governs the repeatable batch lifecycle; Docker governs the always-on serving runtime. |
| Explainability | SHAP values | Feature importances logged to MLflow | XGBoost native importances were sufficient for the analyst audience and avoided SHAP's runtime cost on 119 features. |

**How would the pipeline be improved in future?** The most impactful next step is closing the loop with **automated retraining** triggered by drift alerts, and adding **performance monitoring** via a delayed ground-truth label feedback mechanism (since feature-distribution monitoring alone cannot detect concept drift — see Section 8).

### 6.8 Limitations and Design Trade-offs

Critical evaluation of a system's known weaknesses is as important as documenting its capabilities (Breck et al., 2017). The table below catalogues the principal limitations of the implemented pipeline, the domain risk each carries for a live fraud detection system, and its mitigation status.

**Table 13a — Pipeline Limitations and Design Trade-offs**

| Limitation | Domain Risk for Fraud Detection | Mitigation Status |
|---|---|---|
| **Decision threshold fixed at 0.5** | At this threshold, precision is 32.3% — two in three alerts are false positives. Production fraud systems tune the threshold to a target alert-budget or target precision. | Unmitigated. Threshold tuning is the highest-priority single improvement. |
| **Feature-only drift monitoring** | Scenario B demonstrated that concept drift (fraud pattern changes with no feature-distribution shift) goes undetected by `DataDriftPreset` alone. This is the most operationally dangerous failure mode in fraud. | Partially mitigated by the three-scenario design which proves the gap. Fully requires a delayed ground-truth feedback loop to compute live F1/AUC on labelled data. |
| **Static 5,000-row reference dataset** | The reference sample is fixed at training time. As genuine distributional shift accumulates in production, the reference diverges from the true baseline and drift thresholds become miscalibrated. | Unmitigated. A production system should use a rolling reference window updated on a defined schedule. |
| **MariaDB ColumnStore and Redis at this scale** | At 590,540 rows, a DuckDB in-process query engine and a simple in-memory cache would achieve the same analytical and latency goals with lower operational complexity. ColumnStore and Redis are included to satisfy the columnar-DB and key-value store requirements of the brief and to demonstrate the architecture at scale. | Acceptable and deliberate for coursework purposes. Both tools are appropriate at production scale (>10M rows or multi-user concurrent queries). |
| **No automated retraining trigger** | Drift is detected and summarised but does not trigger pipeline re-execution. The system requires manual intervention after a drift alert, introducing a delay before model refresh. | Unmitigated. Automated retraining would require an Airflow sensor reading `drift_summary.json` and conditionally triggering the `train_model → evaluate_model` sub-DAG. |
| **Feature engineering is minimal** | High-scoring IEEE-CIS solutions use UID-based client aggregations and frequency encoding of email domains and device fingerprints — features that capture user-level behaviour invisible to per-transaction encoding alone. | Partially mitigated by the 119-feature label-encoded baseline. Full mitigation would require a stateful feature store or time-windowed aggregation in preprocessing. |

These limitations are not oversights; each represents a deliberate trade-off between prototype scope and production completeness. Identifying and articulating them is itself a component of responsible MLOps practice (Sculley et al., 2015).

---

## 7. Data Analysis and Exploratory Data Analysis

### 7.1 Levels of Measurement

Understanding the level of measurement of each variable determines which statistical tests and visualisations are valid (Stevens, 1946).

**Table 14 — Variable Types, Levels of Measurement, and Analysis Strategies**

| Feature(s) | Level | Description | Valid Analysis |
|---|---|---|---|
| `TransactionAmt`, D-features | Ratio | Continuous, true zero | Mean, std, IQR, histogram, box plot |
| `TransactionDT` | Interval | Time delta in seconds | Time series, trend analysis |
| `ProductCD`, `card4/6`, email domains | Nominal | Unordered categories | Frequency counts, fraud rate per group |
| `addr1`, `addr2` | Ordinal | Region/postal codes | Rank-based comparisons |
| `isFraud` | Nominal (binary) | Target label | Class distribution, confusion matrix |

### 7.2 Research Questions

- **RQ1:** Does transaction amount distribution differ significantly between fraudulent and legitimate transactions?
- **RQ2:** At what time of day does fraud rate peak, and does this vary across product categories?
- **RQ3:** Are device/network identity features independently associated with higher fraud rates?

### 7.3 Class Distribution

The severe 27:1 imbalance (3.5% fraud) motivates `scale_pos_weight=20` and the use of AUC-ROC and Average Precision over accuracy (a trivial all-legitimate model scores 96.5% accuracy).

*[Figure: `01_fraud_distribution.png` — Class Distribution]*

### 7.4 RQ1 — Transaction Amount Analysis

Fraudulent transactions concentrate at lower amounts with a secondary spike at round-number values, consistent with account-testing behaviour.

*[Figure: `02_transaction_amount.png` — Transaction Amount Distribution]*
*[Figure: `03_fraud_rate_by_amount.png` — Fraud Rate by Amount Bin]*

### 7.5 RQ2 — Temporal Patterns

Fraud activity peaks during off-peak hours, consistent with cross-time-zone operation or reduced monitoring during low-activity periods.

*[Figure: `04_temporal_patterns.png` — Temporal Fraud Patterns]*

### 7.6 Categorical Feature Analysis

Product code `C` shows the highest fraud rate; debit cards show a marginally higher rate than credit cards.

*[Figure: `05_product_code_analysis.png` — Fraud Rate by Product Code]*
*[Figure: `06_card_analysis.png` — Fraud Rate by Card Type]*

### 7.7 Missing Values and Outliers

Identity columns have the highest missingness (75.6% of transactions lack an identity record — a direct consequence of the LEFT JOIN). IQR-based outlier analysis shows outliers in `TransactionAmt` and C-features carry a substantially higher fraud rate, confirming extreme values are signal, not noise.

*[Figure: `08_missing_values.png` — Missing Value Profile]*
*[Figure: `08b_outlier_analysis.png` — Outlier Analysis]*

---

## 8. Model Monitoring and Drift Detection

### 8.1 Monitoring Approach

Evidently AI's `DataDriftPreset` (2023) compares feature distributions between a 5,000-row reference sample and incoming data using Wasserstein distance (numeric) and PSI (categorical). The monitor accepts any Parquet file as current data, enabling both live monitoring and retrospective scenario testing.

```bash
make generate-drift                # creates drifted_a/b/c.parquet
make monitor-drift SCENARIO=a      # runs Evidently against scenario A
```

### 8.2 Synthetic Drift Scenarios and Results

**Table 15 — Synthetic Drift Scenario Definitions and Results**

| Scenario | Type | Modification | Drifted | Detected |
|---|---|---|---|---|
| A | Feature drift | `TransactionAmt ×1.5`; top 20 numeric features +2σ | 20/118 (17.0%) | **Yes** |
| B | Concept drift | 15% of legitimate labels flipped to fraud; features unchanged | 0/118 (0.0%) | **No** |
| C | Covariate shift | All identity columns dropped | 0/118 (0.0%) | **No** |

*[Figure: `drift_scenarios.png` — Drift Detection Results Across Three Scenarios]*

### 8.3 Analysis of Results

**Scenario A** confirms deliberate feature perturbations are reliably detected (20/118 features exceed threshold), triggering a retraining alert.

**Scenario B** exposes a critical limitation: concept drift — where the feature→label relationship changes but distributions remain identical — produces 0% drift and is undetected. A fraud ring mimicking legitimate patterns would degrade the model silently. Detecting this requires ground-truth labels on incoming data, rarely available in real time.

**Scenario C** demonstrates covariate shift via column removal: the monitor warns about missing identity columns but reports 0% drift on the remaining 118 unchanged features, distinguishing covariate shift from feature drift.

**Table 16 — Drift Monitoring Limitations and Mitigations**

| Limitation | Impact | Mitigation |
|---|---|---|
| Concept drift undetected | Silent degradation when patterns change without distribution shift | Delayed label feedback loop; periodic held-out evaluation |
| Covariate shift (missing cols) | Column absence warns but does not alert | Schema validation at ingestion |
| No performance monitoring | Precision/recall trends invisible without labels | Sample-and-review; human-in-the-loop labelling |
| Static reference dataset | Reference becomes stale as legitimate patterns evolve | Rolling reference window per retraining run |

---

## 9. Data Handling and Protection

### 9.1 Definitions

**Data Security** — technical/organisational measures protecting data from unauthorised access or loss. **Data Privacy** — individuals' rights over how their personal data is used. **Data Ethics** — broader societal impact including fairness, transparency, and accountability (Barocas et al., 2019).

### 9.2 Legal Framework

**Table 17 — Applicable Legal Framework and Pipeline Compliance**

| Regulation | Key Requirement | Pipeline Compliance |
|---|---|---|
| UK GDPR Art. 5 | Lawfulness, data minimisation, storage limitation | Anonymised features; no PII retained; raw CSVs excluded from version control |
| UK GDPR Art. 22 | Right not to be subject to solely automated decisions | Model returns a probability score; human review required before action |
| Data Protection Act 2018 | Special category data protection | Financial data treated as sensitive; access restricted to authorised users |
| ICO Guidance on AI | Explainability of automated decisions | Feature importances logged via MLflow; top-20 features interpretable |

### 9.3 Ethical Considerations

**Algorithmic bias:** transactions pattern-matching to fraud indicators (unusual times, foreign domains) may disproportionately flag certain groups; fairness must be designed in, not assumed (Barocas et al., 2019). **False-positive harm:** the pipeline prioritises recall (0.790) over precision (0.323) to minimise missed fraud, deliberately accepting more false positives — a trade-off that must be communicated transparently. **Transparency:** under UK GDPR Art. 22, disputed flags require a meaningful explanation, supported by MLflow-logged feature importances.

### 9.4 Technical Mitigations Implemented

**Table 18 — Ethical and Privacy Mitigations**

| Risk | Mitigation | Where |
|---|---|---|
| PII exposure | Raw CSVs excluded via `.gitignore`; only anonymised Parquet committed | `.gitignore`, `data/raw/` |
| Automated decision harm | Probability score only; no automatic account action | `src/api.py` `/predict` |
| Lack of explainability | Feature importances logged each training run | `src/train.py`, MLflow |
| Model degradation | Evidently drift monitoring triggers retraining alerts | `src/monitor.py` |
| Unauthorised access | Authenticated ColumnStore/Redis; credentials via env vars | `docker-compose.yml`, `config.py` |
| Data retention | No transaction data persisted beyond Redis TTL of 3600s | `src/api.py` |

### 9.5 Privacy-Preserving Considerations for Future Work

Future iterations could add **differential privacy** during training (guarding against membership inference), **federated learning** (training across institutions without centralising raw data), and **k-anonymity/ℓ-diversity** anonymisation before data enters the storage layer.

---

## 10. Conclusion and Reflection

### 10.1 Summary of Achievements

**Table 19 — Learning Outcomes and Evidence**

| LO | Learning Outcome | Evidence |
|---|---|---|
| LO1 | Model and communicate data management requirements | Three candidates evaluated; OBT vs Star/Snowflake; ETL justification; multi-tier storage (Sec. 2–5) |
| LO2 | Implement storage, retrieval, analytical processing | Parquet ingestion; ColumnStore SQL; Redis cache; FastAPI; Docker Compose (Sec. 6) |
| LO3 | Generate insight using appropriate tools | EDA; XGBoost AUC-ROC 0.943; three drift scenarios with Evidently (Sec. 7–8) |
| LO4 | Evaluate ethical and legal issues | UK GDPR Art. 5/22; bias discussion; six technical mitigations (Sec. 9) |

### 10.2 Reflection on Plan vs Implementation

The development process was iterative, not linear. The significant deviations from the Summative Draft Plan — LightGBM → XGBoost, SMOTE → cost-sensitive weighting, Streamlit → React, Parquet-only → four-tier storage (Table 13) — were each driven by concrete engineering trade-offs encountered during implementation, not by abandoning the plan. This mirrors real-world MLOps practice, where designs are refined as understanding of the problem deepens.

### 10.3 Concluding Remarks

The system demonstrates that a production-grade MLOps pipeline for fraud detection is achievable within a resource-constrained prototype. The central lesson confirms Sculley et al. (2015): the model itself — a few hundred lines of XGBoost configuration — is the smallest component. The surrounding infrastructure (ingestion validation, leakage-safe preprocessing, containerised serving, columnar analytics, prediction caching, drift monitoring, ethical governance) constitutes the majority of the engineering effort and determines whether the model can be trusted, maintained, and improved in production.

---

## References

Apache Software Foundation (2023) *Apache Airflow Documentation*. Available at: https://airflow.apache.org (Accessed: December 2024).

Barocas, S., Hardt, M. and Narayanan, A. (2019) *Fairness and Machine Learning: Limitations and Opportunities*. fairmlbook.org. Available at: https://fairmlbook.org (Accessed: January 2025).

Breck, E., Cai, S., Nielsen, E., Salib, M. and Sculley, D. (2017) 'The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction', *IEEE International Conference on Big Data*, pp. 1123–1132.

Chawla, N.V., Bowyer, K.W., Hall, L.O. and Kegelmeyer, W.P. (2002) 'SMOTE: Synthetic Minority Over-sampling Technique', *Journal of Artificial Intelligence Research*, 16, pp. 321–357.

Chen, T. and Guestrin, C. (2016) 'XGBoost: A Scalable Tree Boosting System', *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, pp. 785–794.

Evidently AI (2023) *Evidently: Open-Source ML Monitoring*. Available at: https://github.com/evidentlyai/evidently (Accessed: December 2024).

Grinsztajn, L., Oyallon, E. and Varoquaux, G. (2022) 'Why tree-based models still outperform deep learning on tabular data', *Advances in Neural Information Processing Systems*, 35, pp. 507–520.

Kaggle (2015) *Rossmann Store Sales*. Available at: https://www.kaggle.com/c/rossmann-store-sales (Accessed: October 2024).

Klaise, J., Van Looveren, A., Cox, C., Vacanti, G. and Coca, A. (2020) 'Monitoring and explainability of models in production', *ICML Workshop on Challenges in Deploying and Monitoring ML Systems*.

MariaDB Foundation (2023) *MariaDB ColumnStore Documentation*. Available at: https://mariadb.com/kb/en/mariadb-columnstore/ (Accessed: December 2024).

MLflow / Databricks (2023) *MLflow: An Open Source Platform for the ML Lifecycle*. Available at: https://mlflow.org (Accessed: December 2024).

New York City Taxi and Limousine Commission (2024) *TLC Trip Record Data*. Available at: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page (Accessed: October 2024).

Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J.-F. and Dennison, D. (2015) 'Hidden technical debt in machine learning systems', *Advances in Neural Information Processing Systems*, 28.

Stevens, S.S. (1946) 'On the Theory of Scales of Measurement', *Science*, 103(2684), pp. 677–680.

UK Finance (2023) *Annual Fraud Report 2023*. Available at: https://www.ukfinance.org.uk (Accessed: January 2025).

UK Parliament (2018) *Data Protection Act 2018*. Available at: https://www.legislation.gov.uk/ukpga/2018/12/contents (Accessed: January 2025).

Vesta Corporation (2019) *IEEE-CIS Fraud Detection*. Kaggle Competition. Available at: https://www.kaggle.com/c/ieee-fraud-detection (Accessed: October 2024).

---

## Appendix A — Project Repository Structure

```
mlops_pipeline/
├── data/{raw,processed,sql}/
├── src/        # data_processing, preprocessing, train, evaluate,
│               # api, monitor, analytics, generate_drift_data, predict, config
├── models/     # model.joblib, preprocessing_artifacts.joblib, feature_columns.joblib
├── notebooks/  # 01_eda_fraud_detection.ipynb
├── reports/    # figures/, metrics/, monitoring/
├── frontend/   # React 18 + Vite + Tailwind dashboard
├── dags/       # fraud_pipeline_dag.py (Airflow)
├── docker-compose.yml, Makefile, requirements.txt
```

## Appendix B — FastAPI Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | API status, model loaded, Redis connected |
| `/predict` | POST | Fraud probability; returns `cached: true/false` |
| `/model-info` | GET | Model type, feature count, metrics |
| `/metrics` | GET | Training and evaluation metrics |
| `/drift-summary` | GET | Drift JSON; `?scenario=a\|b\|c` |
| `/analytics/queries` | GET | ColumnStore SQL query results |
| `/eda-summary` | GET | EDA summary statistics |
| `/eda-figures`, `/report-figures` | GET | List available figures |
| `/docs` | GET | Swagger UI |
