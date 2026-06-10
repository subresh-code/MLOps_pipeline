"""
Generate synthetic drifted datasets from the reference training data.

Three scenarios:
  A — feature/data drift: shift numeric feature distributions
  B — concept drift: same features, new fraud patterns (label flip)
  C — covariate shift: identity columns completely absent
"""
import argparse
import logging

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED_DIR, PROCESSED_TRAIN_FILE

logger = logging.getLogger(__name__)

IDENTITY_COLS = [f"id_{str(i).zfill(2)}" for i in range(1, 39)] + [
    "DeviceType",
    "DeviceInfo",
]

SAMPLE_SIZE = 10_000
RANDOM_STATE = 42


def _load_reference(n: int = SAMPLE_SIZE) -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_TRAIN_FILE)
    return df.sample(n=min(n, len(df)), random_state=RANDOM_STATE).reset_index(drop=True)


def scenario_a(df: pd.DataFrame) -> pd.DataFrame:
    """Data drift: shift numeric distributions; labels unchanged."""
    out = df.copy()
    rng = np.random.default_rng(RANDOM_STATE)

    numeric_cols = out.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != "isFraud"]

    # Scale TransactionAmt by 1.5 (higher-value transactions appear)
    if "TransactionAmt" in out.columns:
        out["TransactionAmt"] = out["TransactionAmt"] * 1.5

    # Shift the first 20 numeric features by +2 std
    for col in numeric_cols[:20]:
        std = float(out[col].std())
        if std > 0:
            out[col] = out[col] + 2 * std + rng.normal(0, std * 0.1, size=len(out))

    return out


def scenario_b(df: pd.DataFrame) -> pd.DataFrame:
    """Concept drift: features unchanged, 15% of legitimate txns flipped to fraud."""
    out = df.copy()
    rng = np.random.default_rng(RANDOM_STATE)

    legit_mask = out["isFraud"] == 0
    legit_idx = out.index[legit_mask]
    flip_n = int(len(legit_idx) * 0.15)
    flip_idx = rng.choice(legit_idx, size=flip_n, replace=False)
    out.loc[flip_idx, "isFraud"] = 1

    return out


def scenario_c(df: pd.DataFrame) -> pd.DataFrame:
    """Covariate shift: all identity-table columns are absent (device data lost)."""
    out = df.copy()
    cols_to_drop = [c for c in IDENTITY_COLS if c in out.columns]
    out = out.drop(columns=cols_to_drop)
    return out


def generate_all():
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Loading reference data...")
    ref = _load_reference()
    logger.info(f"Reference: {ref.shape[0]:,} rows, {ref.shape[1]} features")

    scenarios = {
        "a": ("drifted_a.parquet", scenario_a, "Feature/data drift"),
        "b": ("drifted_b.parquet", scenario_b, "Concept drift"),
        "c": ("drifted_c.parquet", scenario_c, "Covariate shift"),
    }

    for key, (fname, fn, desc) in scenarios.items():
        path = DATA_PROCESSED_DIR / fname
        drifted = fn(ref)
        drifted.to_parquet(path, index=False)
        fraud_rate = drifted["isFraud"].mean() if "isFraud" in drifted.columns else "N/A"
        logger.info(
            f"Scenario {key.upper()} ({desc}): {drifted.shape} → {path.name}"
            f"  fraud_rate={fraud_rate:.3f}" if isinstance(fraud_rate, float) else ""
        )

    print("\n" + "=" * 50)
    print("  DRIFT DATA GENERATION COMPLETE")
    print("=" * 50)
    for key, (fname, _, desc) in scenarios.items():
        print(f"  Scenario {key.upper()} ({desc}): data/processed/{fname}")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic drifted datasets")
    parser.add_argument(
        "--scenario",
        choices=["a", "b", "c", "all"],
        default="all",
        help="Which drift scenario to generate (default: all)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

    if args.scenario == "all":
        generate_all()
    else:
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        ref = _load_reference()
        fns = {"a": scenario_a, "b": scenario_b, "c": scenario_c}
        names = {"a": "drifted_a.parquet", "b": "drifted_b.parquet", "c": "drifted_c.parquet"}
        drifted = fns[args.scenario](ref)
        path = DATA_PROCESSED_DIR / names[args.scenario]
        drifted.to_parquet(path, index=False)
        print(f"Saved {path}")
