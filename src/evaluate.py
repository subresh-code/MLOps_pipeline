import json
import logging
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    PrecisionRecallDisplay,
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
)

from src.config import (
    CLASSIFICATION_REPORT_PATH,
    CONFUSION_MATRIX_PLOT,
    EVAL_METRICS_PATH,
    FEATURE_COLUMNS_PATH,
    FEATURE_IMPORTANCE_PLOT,
    MODEL_PATH,
    PR_CURVE_PLOT,
    PROCESSED_TEST_FILE,
    REPORTS_DIR,
    REPORTS_FIGURES_DIR,
    REPORTS_METRICS_DIR,
    ROC_CURVE_PLOT,
    TARGET,
    TRAINING_METRICS_PATH,
)

logger = logging.getLogger(__name__)


def load_artifacts():
    logger.info("Loading model...")
    model = joblib.load(MODEL_PATH)
    logger.info("Loading test data...")
    test_df = pd.read_parquet(PROCESSED_TEST_FILE)
    feature_columns = joblib.load(FEATURE_COLUMNS_PATH)
    X_test = test_df[feature_columns]
    y_test = test_df[TARGET]
    return model, X_test, y_test


def compute_metrics(y_true, y_pred, y_proba):
    return {
        "auc_roc": float(roc_auc_score(y_true, y_proba)),
        "average_precision": float(average_precision_score(y_true, y_proba)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred)),
        "recall": float(recall_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred)),
        "test_size": int(len(y_true)),
        "fraud_count": int(y_true.sum()),
        "fraud_rate": float(y_true.mean()),
    }


def save_metrics(metrics):
    REPORTS_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVAL_METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {EVAL_METRICS_PATH}")


def save_classification_report(y_true, y_pred):
    REPORTS_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    report = classification_report(y_true, y_pred, digits=4)
    with open(CLASSIFICATION_REPORT_PATH, "w") as f:
        f.write(report)
    logger.info(f"Classification report saved to {CLASSIFICATION_REPORT_PATH}")


def plot_confusion_matrix(y_true, y_pred):
    REPORTS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Legit", "Fraud"])
    disp.plot(cmap="Blues", values_format="d")
    plt.title("Confusion Matrix - XGBoost Fraud Detection")
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PLOT, dpi=150)
    plt.close()
    logger.info(f"Confusion matrix saved to {CONFUSION_MATRIX_PLOT}")


def plot_roc_curve(y_true, y_proba):
    REPORTS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc = roc_auc_score(y_true, y_proba)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, label=f"XGBoost (AUC = {auc:.4f})", linewidth=2)
    ax.plot([0, 1], [0, 1], "k--", label="Random Classifier", linewidth=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve - XGBoost Fraud Detection")
    ax.legend(loc="lower right")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    plt.tight_layout()
    plt.savefig(ROC_CURVE_PLOT, dpi=150)
    plt.close()
    logger.info(f"ROC curve saved to {ROC_CURVE_PLOT}")


def plot_pr_curve(y_true, y_proba):
    REPORTS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    precision, recall, _ = precision_recall_curve(y_true, y_proba)
    ap = average_precision_score(y_true, y_proba)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(recall, precision, label=f"XGBoost (AP = {ap:.4f})", linewidth=2)
    baseline = y_true.mean()
    ax.axhline(y=baseline, color="gray", linestyle="--", label=f"Baseline ({baseline:.4f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curve - XGBoost Fraud Detection")
    ax.legend(loc="upper right")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    plt.tight_layout()
    plt.savefig(PR_CURVE_PLOT, dpi=150)
    plt.close()
    logger.info(f"PR curve saved to {PR_CURVE_PLOT}")


def plot_feature_importance(model, feature_columns, top_n=20):
    REPORTS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    importance = model.feature_importances_
    indices = np.argsort(importance)[::-1][:top_n]
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(range(top_n), importance[indices][::-1], color="steelblue")
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([feature_columns[i] for i in indices[::-1]])
    ax.set_xlabel("Importance")
    ax.set_title(f"Top {top_n} Feature Importance - XGBoost Fraud Detection")
    plt.tight_layout()
    plt.savefig(FEATURE_IMPORTANCE_PLOT, dpi=150)
    plt.close()
    logger.info(f"Feature importance plot saved to {FEATURE_IMPORTANCE_PLOT}")


def run_evaluation():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_METRICS_DIR.mkdir(parents=True, exist_ok=True)

    model, X_test, y_test = load_artifacts()
    logger.info(f"Test set: {X_test.shape[0]} samples, {X_test.shape[1]} features")

    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    metrics = compute_metrics(y_test, y_pred, y_proba)
    save_metrics(metrics)

    save_classification_report(y_test, y_pred)

    plot_confusion_matrix(y_test, y_pred)
    plot_roc_curve(y_test, y_proba)
    plot_pr_curve(y_test, y_proba)
    plot_feature_importance(model, list(X_test.columns))

    print("\n" + "=" * 55)
    print("  EVALUATION COMPLETE - XGBoost Fraud Detection")
    print("=" * 55)
    for k, v in metrics.items():
        print(f"  {k:20s} = {v:.6f}" if isinstance(v, float) else f"  {k:20s} = {v}")
    print("=" * 55)
    print(f"\nOutputs:")
    print(f"  Metrics:           {EVAL_METRICS_PATH}")
    print(f"  Classification rpt:{CLASSIFICATION_REPORT_PATH}")
    print(f"  Confusion matrix:  {CONFUSION_MATRIX_PLOT}")
    print(f"  ROC curve:         {ROC_CURVE_PLOT}")
    print(f"  PR curve:          {PR_CURVE_PLOT}")
    print(f"  Feature importance:{FEATURE_IMPORTANCE_PLOT}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    run_evaluation()
