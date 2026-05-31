import json
import logging

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import (
    DATA_PROCESSED_DIR,
    INGESTION_SUMMARY_PATH,
    MODELS_DIR,
    PROCESSED_TEST_FILE,
    PROCESSED_TRAIN_FILE,
    RANDOM_STATE,
    REFERENCE_DATA_FILE,
    REFERENCE_SAMPLE_SIZE,
    REPORTS_METRICS_DIR,
    TARGET,
    TEST_SIZE,
    TRAIN_IDENTITY_FILE,
    TRAIN_TRANSACTION_FILE,
)
from src.preprocessing import FeaturePreprocessor

logger = logging.getLogger(__name__)


def validate_raw_data():
    """Check that required files and columns exist before loading."""
    if not TRAIN_TRANSACTION_FILE.exists():
        raise FileNotFoundError(
            f"Transaction file not found at {TRAIN_TRANSACTION_FILE}. "
            "Download the IEEE-CIS dataset and place it in data/raw/."
        )

    # Validate required columns in transaction file
    required = {"TransactionID", TARGET, "TransactionDT", "TransactionAmt"}
    sample = pd.read_csv(TRAIN_TRANSACTION_FILE, nrows=0)
    actual = set(sample.columns)
    missing = required - actual
    if missing:
        raise ValueError(
            f"Transaction file is missing required columns: {missing}. "
            f"Found columns: {sorted(actual)}"
        )

    # Validate identity file if present
    if TRAIN_IDENTITY_FILE.exists():
        id_sample = pd.read_csv(TRAIN_IDENTITY_FILE, nrows=0)
        if "TransactionID" not in id_sample.columns:
            raise ValueError(
                "Identity file is missing required column 'TransactionID'. "
                f"Found columns: {sorted(id_sample.columns)}"
            )

    logger.info("Schema validation passed for all input files.")


def load_raw_data() -> pd.DataFrame:
    validate_raw_data()

    logger.info(f"Loading transaction data from {TRAIN_TRANSACTION_FILE}")
    transactions = pd.read_csv(TRAIN_TRANSACTION_FILE)
    n_trans = len(transactions)
    c_trans = len(transactions.columns)
    logger.info(f"Transaction rows: {n_trans}, columns: {c_trans}")

    identity_used = False
    n_ident = 0
    c_ident = 0

    if TRAIN_IDENTITY_FILE.exists():
        identity_used = True
        logger.info(f"Loading identity data from {TRAIN_IDENTITY_FILE}")
        identity = pd.read_csv(TRAIN_IDENTITY_FILE)
        n_ident = len(identity)
        c_ident = len(identity.columns)
        logger.info(f"Identity rows: {n_ident}, columns: {c_ident}")

        df = transactions.merge(identity, on="TransactionID", how="left")

        # LEFT JOIN must preserve all transaction rows
        n_merged = len(df)
        if n_merged != n_trans:
            raise RuntimeError(
                f"Row count mismatch after LEFT JOIN: expected {n_trans} (transaction rows), "
                f"got {n_merged}. The join may have introduced duplicates or dropped rows."
            )
        logger.info(f"Merged data: {n_merged} rows, {len(df.columns)} columns")
    else:
        df = transactions
        logger.info("No identity file found — using transaction data only.")

    summary = {
        "transaction_rows": n_trans,
        "transaction_columns": c_trans,
        "identity_rows": n_ident,
        "identity_columns": c_ident,
        "identity_file_used": identity_used,
        "merged_rows": len(df),
        "merged_columns": len(df.columns),
        "join_key": "TransactionID",
        "join_type": "left",
        "row_count_preserved": len(df) == n_trans,
    }

    return df, summary


def process_data() -> tuple[pd.DataFrame, pd.DataFrame, FeaturePreprocessor]:
    """
    Process raw data and return train/test splits with fitted preprocessor.

    The preprocessor is fitted on the training split only (after splitting)
    to avoid data leakage. The test set is then transformed using the
    fitted preprocessor.

    Returns:
        train_df: Processed training data
        test_df: Processed test data
        preprocessor: Fitted FeaturePreprocessor for use in inference
    """
    df, ingestion_summary = load_raw_data()

    # Split BEFORE preprocessing to avoid data leakage
    train_raw, test_raw = train_test_split(
        df, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=df[TARGET]
    )
    logger.info(f"Split data - Train: {len(train_raw)}, Test: {len(test_raw)}")

    # Add split info to summary
    fraud_rate_train = float(train_raw[TARGET].mean())
    fraud_rate_test = float(test_raw[TARGET].mean())
    ingestion_summary.update({
        "train_rows": len(train_raw),
        "test_rows": len(test_raw),
        "fraud_rate_train": round(fraud_rate_train, 4),
        "fraud_rate_test": round(fraud_rate_test, 4),
    })

    # Save ingestion summary
    REPORTS_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(INGESTION_SUMMARY_PATH, "w") as f:
        json.dump(ingestion_summary, f, indent=2)
    logger.info(f"Ingestion summary saved to {INGESTION_SUMMARY_PATH}")

    # Fit preprocessor on training data only
    preprocessor = FeaturePreprocessor()
    train_df = preprocessor.fit_transform(train_raw)

    # Transform test data using fitted preprocessor
    test_df = preprocessor.transform(test_raw)

    logger.info(f"Train shape: {train_df.shape}, Test shape: {test_df.shape}")
    logger.info(
        f"Fraud rate - Train: {train_df[TARGET].mean():.4f}, "
        f"Test: {test_df[TARGET].mean():.4f}"
    )

    # Save processed data
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    train_df.to_parquet(PROCESSED_TRAIN_FILE, index=False)
    test_df.to_parquet(PROCESSED_TEST_FILE, index=False)

    # Save reference data for drift monitoring
    reference_sample = train_df.drop(columns=[TARGET]).sample(
        n=min(REFERENCE_SAMPLE_SIZE, len(train_df)), random_state=RANDOM_STATE
    )
    reference_sample.to_parquet(REFERENCE_DATA_FILE, index=False)

    # Save preprocessing artifacts
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    preprocessor.save()

    logger.info(f"Processed data saved to {DATA_PROCESSED_DIR}")
    return train_df, test_df, preprocessor


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_df, test_df, preprocessor = process_data()
