# Reflection: Task 1 Plan vs Task 2 Implementation

## Overview

This document reflects on the implementation of the CMP6230 Task 2 MLOps pipeline in relation to the pipeline design proposed in Task 1. The project addresses credit card fraud detection using the IEEE-CIS Fraud Detection dataset, implementing a five-stage MLOps pipeline: Data Ingestion, Data Pre-processing, Model Development, Model Deployment, and Model Monitoring. Overall, the implemented pipeline closely follows the original plan, with several practical adjustments made during development.

## What Matched the Task 1 Plan

Several core design decisions from the Task 1 proposal were carried through to the final implementation:

- **Dataset**: The IEEE-CIS Fraud Detection dataset was used, matching the planned choice.
- **Data join**: The planned LEFT JOIN on `TransactionID` between `train_transaction.csv` and `train_identity.csv` was implemented as specified.
- **Storage format**: The denormalised analytical table was stored as Parquet, as planned.
- **Pipeline stages**: All five planned stages (Data Ingestion, Data Pre-processing, Model Development, Model Deployment, Model Monitoring) were implemented.
- **Tree-based model**: The plan specified LightGBM or a tree-based classifier; the final implementation uses XGBoost, which falls within this category.
- **Containerisation and API**: The deployment stage includes FastAPI with Docker support, matching the planned deployment approach.
- **Drift monitoring**: Monitoring was included using Evidently, consistent with the plan's intent.

## What Changed During Implementation

Several differences emerged between the planned design and the actual implementation:

- **Train/test split positioning**: The plan implicitly assumed that preprocessing would occur before the train/test split. Implementation revealed that this would cause data leakage, as the preprocessing statistics (medians, label encodings) would incorporate information from the test set. The split was moved to occur **before** preprocessing, so the preprocessor is fitted exclusively on training data and only transformed on test and production data.
- **Model selection**: LightGBM was the planned model, but XGBoost was selected during implementation. XGBoost integrates well with the existing Python stack, provides built-in handling of missing values, and offers a straightforward `scale_pos_weight` parameter for class imbalance. The `compare_models.py` script confirmed that XGBoost produced competitive results against Logistic Regression and Random Forest baselines.
- **Schema validation**: The plan anticipated formal schema validation using Great Expectations. The current implementation uses lightweight file-existence and column-presence checks rather than a full validation framework. This was a pragmatic decision to keep the pipeline scope manageable while still providing meaningful ingestion guarantees.
- **Monitoring scope**: The plan described both drift and performance monitoring. The implementation focuses on data drift using Evidently's `DataDriftPreset`. Full performance monitoring (tracking precision, recall, and accuracy over time against ground-truth labels) was not implemented because production labels are not immediately available in the fraud-detection setting, and the coursework uses a static dataset rather than a live production stream.
- **Output evidence generation**: Evaluation plots (confusion matrix, ROC curve, PR curve, feature importance) were added during implementation as report evidence but were not detailed in the original plan.

## Why the Changes Were Justified

- **Data leakage prevention**: Moving the split before preprocessing is a standard best practice in machine learning and corrects a significant flaw in the original plan. Allowing test-set information to influence preprocessing would have inflated reported performance metrics and produced an unrealistically optimistic evaluation.
- **XGBoost over LightGBM**: Both are gradient-boosted tree frameworks with similar performance characteristics. XGBoost's mature Python packaging, direct support for handling missing values, and built-in `scale_pos_weight` for class imbalance made it the more practical choice without sacrificing model quality.
- **Lightweight validation**: For a coursework project with a single known data source, a full Great Expectations suite adds configuration overhead without proportional benefit. The implemented checks (file existence, required column presence, row-count preservation after join) cover the most critical failure modes.
- **Limited monitoring scope**: Since the project operates on historical competition data rather than a live system, production performance monitoring cannot be demonstrated meaningfully. The data-drift comparison between the training reference sample and the held-out test set demonstrates the monitoring infrastructure is operational and ready for deployment.

## Current Limitations

- **Schema validation is minimal**: Column presence is checked, but data types, value ranges, and referential integrity are not validated. A malformed CSV could pass the initial checks and fail later in the pipeline.
- **No model explainability**: The pipeline does not include SHAP or LIME explanations, which limits interpretability for stakeholders.
- **Monitoring lacks prediction drift**: Population Stability Index (PSI) and prediction distribution tracking are not implemented, reducing visibility into model behaviour changes between training and production.
- **No automated retraining**: While the drift monitor flags distribution changes, there is no automated mechanism to trigger retraining or model rollback.
- **API security**: The FastAPI endpoints have no authentication, which is acceptable for coursework but would need addressing in a production deployment.

## Future Improvements

- **Formal data validation**: Integrate Great Expectations or Pandera schemas to validate data types, value ranges, and null-percentage thresholds at ingestion time.
- **Model explainability**: Add SHAP summary plots and force plots to the evaluation pipeline for both global feature importance and individual prediction explanations.
- **PSI and prediction drift**: Extend the monitor to track PSI for numerical features and prediction-distribution shifts for model outputs, using saved predictions from the test set as a baseline.
- **Scheduled monitoring**: Deploy the drift monitor as a scheduled job (e.g., cron, Airflow, or Cloud Scheduler) to produce periodic drift reports without manual invocation.
- **Automated retraining**: Implement a retraining pipeline triggered when the drift share exceeds a configurable threshold over multiple consecutive checks.
- **API security**: Add API key or OAuth2 authentication to the FastAPI endpoints for production use.
- **Cloud object storage**: Store model artefacts and processed data in cloud storage (GCS or S3) rather than local disk to support multi-instance deployments.
