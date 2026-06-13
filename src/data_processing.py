import argparse
import json
import logging

import pandas as pd

from src.config import (
    DATA_PROCESSED_DIR,
    INGESTION_SUMMARY_PATH,
    MODELS_DIR,
    PROCESSED_TEST_FILE,
    PROCESSED_TRAIN_FILE,
    RANDOM_STATE,
    RAW_SPLIT_TEST_FILE,
    RAW_SPLIT_TRAIN_FILE,
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


def ingest_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ingestion stage: load, merge, and temporally split the raw data.

    Writes the un-preprocessed train/test splits to disk so the preprocessing
    stage can run independently. No feature engineering happens here.

    Returns:
        train_raw: Raw training split (earlier 80%)
        test_raw: Raw test split (later 20%)
    """
    df, ingestion_summary = load_raw_data()

    # Temporal split: sort by TransactionDT so train = earlier 80%, test = later 20%.
    # This avoids look-ahead bias — random splitting on time-ordered fraud data
    # leaks future patterns into training and produces over-optimistic metrics.
    df_sorted = df.sort_values("TransactionDT").reset_index(drop=True)
    split_idx = int(len(df_sorted) * (1 - TEST_SIZE))
    train_raw = df_sorted.iloc[:split_idx].copy()
    test_raw = df_sorted.iloc[split_idx:].copy()
    logger.info(
        f"Temporal split — Train: {len(train_raw)} (earlier {int((1-TEST_SIZE)*100)}%), "
        f"Test: {len(test_raw)} (later {int(TEST_SIZE*100)}%)"
    )

    # Add split info to summary
    ingestion_summary.update({
        "train_rows": len(train_raw),
        "test_rows": len(test_raw),
        "fraud_rate_train": round(float(train_raw[TARGET].mean()), 4),
        "fraud_rate_test": round(float(test_raw[TARGET].mean()), 4),
    })

    # Save ingestion summary
    REPORTS_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(INGESTION_SUMMARY_PATH, "w") as f:
        json.dump(ingestion_summary, f, indent=2)
    logger.info(f"Ingestion summary saved to {INGESTION_SUMMARY_PATH}")

    # Persist the raw splits as the handoff to the preprocessing stage
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw.to_parquet(RAW_SPLIT_TRAIN_FILE, index=False)
    test_raw.to_parquet(RAW_SPLIT_TEST_FILE, index=False)
    logger.info(
        f"Raw splits saved to {RAW_SPLIT_TRAIN_FILE} and {RAW_SPLIT_TEST_FILE}"
    )

    return train_raw, test_raw


def preprocess_data() -> tuple[pd.DataFrame, pd.DataFrame, FeaturePreprocessor]:
    """
    Preprocessing stage: feature engineering, encoding, and imputation.

    Reads the raw splits produced by ingest_data(), fits the preprocessor on
    the training split only (to avoid leakage), transforms both splits, and
    saves the processed data, drift-reference sample, and fitted preprocessor.

    Returns:
        train_df: Processed training data
        test_df: Processed test data
        preprocessor: Fitted FeaturePreprocessor for use in inference
    """
    if not RAW_SPLIT_TRAIN_FILE.exists() or not RAW_SPLIT_TEST_FILE.exists():
        logger.info("Raw splits not found — running ingestion stage first.")
        ingest_data()

    train_raw = pd.read_parquet(RAW_SPLIT_TRAIN_FILE)
    test_raw = pd.read_parquet(RAW_SPLIT_TEST_FILE)
    logger.info(
        f"Loaded raw splits — Train: {train_raw.shape}, Test: {test_raw.shape}"
    )

    # Fit preprocessor on training data only, then transform both splits
    preprocessor = FeaturePreprocessor()
    train_df = preprocessor.fit_transform(train_raw)
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


def process_data() -> tuple[pd.DataFrame, pd.DataFrame, FeaturePreprocessor]:
    """Run both stages end-to-end (ingestion then preprocessing).

    Kept for backward compatibility — callers that want the full pipeline in a
    single call (e.g. training when artifacts are missing) still work.
    """
    ingest_data()
    return preprocess_data()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Data ingestion and preprocessing.")
    parser.add_argument(
        "--stage",
        choices=["ingest", "preprocess", "all"],
        default="all",
        help="Which stage to run (default: all).",
    )
    args = parser.parse_args()

    if args.stage == "ingest":
        ingest_data()
    elif args.stage == "preprocess":
        preprocess_data()
    else:
        process_data()
