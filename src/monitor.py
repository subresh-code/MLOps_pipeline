import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")


def _fallback_drift(ref: pd.DataFrame, cur: pd.DataFrame) -> dict:
    """Simple statistical drift check when Evidently is unavailable."""
    numeric_ref = ref.select_dtypes(include=[np.number])
    numeric_cur = cur.select_dtypes(include=[np.number])
    common = list(set(numeric_ref.columns) & set(numeric_cur.columns))

    drifted = []
    for col in common:
        ref_mean = float(numeric_ref[col].mean()) if not numeric_ref[col].isna().all() else 0.0
        cur_mean = float(numeric_cur[col].mean()) if not numeric_cur[col].isna().all() else 0.0
        ref_std = float(numeric_ref[col].std()) if not numeric_ref[col].isna().all() else 1.0
        denom = max(ref_std, 1e-8)
        change_pct = abs(cur_mean - ref_mean) / denom
        if change_pct > 0.2:
            drifted.append({
                "feature": col,
                "ref_mean": round(ref_mean, 4),
                "cur_mean": round(cur_mean, 4),
                "change_std": round(change_pct, 4),
            })

    return {
        "method": "fallback_statistical",
        "number_of_features": len(common),
        "number_of_drifted_features": len(drifted),
        "drift_share": round(len(drifted) / max(len(common), 1), 4),
        "drift_detected": len(drifted) / max(len(common), 1) > 0.05,
        "drifted_features": drifted,
        "evidently_available": False,
    }


def run_drift_monitor(current_data_path: str | None = None, output_json_path: str | None = None):
    from src.config import (
        DRIFT_REPORT_HTML,
        DRIFT_SUMMARY_JSON,
        DRIFT_THRESHOLD,
        PROCESSED_TEST_FILE,
        REFERENCE_DATA_FILE,
        REPORTS_MONITORING_DIR,
        TARGET,
    )

    REPORTS_MONITORING_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Loading reference data...")
    if not REFERENCE_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Reference data not found at {REFERENCE_DATA_FILE}. Run training first."
        )
    ref = pd.read_parquet(REFERENCE_DATA_FILE)
    logger.info(f"Reference: {ref.shape[0]} rows, {ref.shape[1]} features")

    logger.info("Loading current data...")
    cur_path = Path(current_data_path) if current_data_path else PROCESSED_TEST_FILE
    if not cur_path.exists():
        raise FileNotFoundError(
            f"Current data not found at {cur_path}. Run training (or generate-drift) first."
        )
    cur = pd.read_parquet(cur_path)
    if TARGET in cur.columns:
        cur = cur.drop(columns=[TARGET])
        logger.info("Dropped target column from current data")
    logger.info(f"Current: {cur.shape[0]} rows, {cur.shape[1]} features")

    # Align columns
    common_cols = list(set(ref.columns) & set(cur.columns))
    missing = set(ref.columns) - set(cur.columns)
    if missing:
        logger.warning(f"Missing columns in current data: {missing}")
    logger.info(f"Comparing {len(common_cols)} common features")

    ref_aligned = ref[common_cols]
    cur_aligned = cur[common_cols]

    # Try Evidently 0.7.x API
    evidently_ok = False
    drift_result = {}

    try:
        from evidently.core.report import Report
        from evidently.presets import DataDriftPreset

        report = Report(metrics=[DataDriftPreset()])
        snapshot = report.run(reference_data=ref_aligned, current_data=cur_aligned)

        snapshot.save_html(str(DRIFT_REPORT_HTML))
        logger.info(f"Drift HTML report saved to {DRIFT_REPORT_HTML}")

        raw = json.loads(snapshot.json())
        metrics = raw.get("metrics", [])

        drift_result = {
            "method": "evidently_datadriftpreset",
            "number_of_features": len(common_cols),
            "number_of_drifted_features": 0,
            "drift_share": 0.0,
            "drift_detected": False,
            "threshold_used": DRIFT_THRESHOLD,
            "reference_rows": len(ref_aligned),
            "current_rows": len(cur_aligned),
            "evidently_available": True,
            "drifted_features": [],
            "all_metrics": [],
        }

        drifted_count = 0
        for m in metrics:
            name = m.get("metric_name", "")
            val = m.get("value")
            cfg = m.get("config", {})
            if "ValueDrift" in name and isinstance(val, (int, float)):
                col = cfg.get("column", name)
                p_value = float(val)
                threshold = cfg.get("threshold", 0.05)
                is_drifted = p_value < threshold
                entry = {
                    "feature": col,
                    "p_value": round(p_value, 6),
                    "threshold": threshold,
                    "stattest": cfg.get("method", ""),
                    "drift_detected": is_drifted,
                }
                drift_result["all_metrics"].append(entry)
                if is_drifted:
                    drifted_count += 1
                    drift_result["drifted_features"].append(entry)
        drift_result["number_of_drifted_features"] = drifted_count
        drift_result["drift_share"] = round(drifted_count / max(len(metrics) - 1, 1), 4)
        drift_result["drift_detected"] = drifted_count / max(len(metrics) - 1, 1) > DRIFT_THRESHOLD

        evidently_ok = True
        logger.info(
            f"Drift: {drift_result['number_of_drifted_features']}/{drift_result['number_of_features']} "
            f"features drifted (share={drift_result['drift_share']:.2%})"
        )

    except Exception as e:
        logger.warning(f"Evidently drift detection failed: {e}")
        logger.warning("Falling back to statistical comparison")
        evidently_error = str(e)
    else:
        evidently_error = None

    if not evidently_ok:
        drift_result = _fallback_drift(ref_aligned, cur_aligned)
        drift_result.update({
            "threshold_used": DRIFT_THRESHOLD,
            "reference_rows": len(ref_aligned),
            "current_rows": len(cur_aligned),
            "evidently_error": evidently_error,
        })
        # Write a minimal HTML placeholder
        DRIFT_REPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
        with open(DRIFT_REPORT_HTML, "w") as f:
            f.write(
                f"<html><body><h1>Drift Report</h1>"
                f"<p>Evidently HTML generation failed: {evidently_error}</p>"
                f"<p>Fallback statistical comparison used. See drift_summary.json.</p>"
                f"</body></html>"
            )
        logger.info(f"Fallback drift report saved to {DRIFT_REPORT_HTML}")

    # Save JSON summary
    json_out = Path(output_json_path) if output_json_path else DRIFT_SUMMARY_JSON
    json_out.parent.mkdir(parents=True, exist_ok=True)
    with open(json_out, "w") as f:
        json.dump(drift_result, f, indent=2, default=str)
    logger.info(f"Drift summary saved to {json_out}")

    print("\n" + "=" * 55)
    print("  DRIFT MONITORING COMPLETE")
    print("=" * 55)
    print(f"  Method:              {drift_result.get('method', 'N/A')}")
    print(f"  Features analyzed:   {drift_result.get('number_of_features', 'N/A')}")
    print(f"  Drifted features:    {drift_result.get('number_of_drifted_features', 'N/A')}")
    print(f"  Drift share:         {drift_result.get('drift_share', 'N/A')}")
    print(f"  Drift detected:      {drift_result.get('drift_detected', 'N/A')}")
    print(f"  Reference rows:      {drift_result.get('reference_rows', 'N/A')}")
    print(f"  Current rows:        {drift_result.get('current_rows', 'N/A')}")
    print("=" * 55)
    print(f"\nOutputs:")
    print(f"  HTML report:  {DRIFT_REPORT_HTML}")
    print(f"  JSON summary: {DRIFT_SUMMARY_JSON}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run drift monitoring")
    parser.add_argument(
        "--current-data",
        type=str,
        default=None,
        help="Path to current data Parquet (default: data/processed/test.parquet)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Override path for drift summary JSON output",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    run_drift_monitor(
        current_data_path=args.current_data,
        output_json_path=args.output_json,
    )
