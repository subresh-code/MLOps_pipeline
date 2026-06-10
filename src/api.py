import hashlib
import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.predict import predictor

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fraud Detection API",
    description="MLOps fraud detection service with XGBoost model",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts — available only when the directories exist
_BASE = Path(__file__).parent.parent
for _mount, _dir in [
    ("/static/eda", _BASE / "notebooks" / "figures"),
    ("/static/reports", _BASE / "reports" / "figures"),
]:
    if _dir.exists():
        app.mount(_mount, StaticFiles(directory=str(_dir)), name=_mount.lstrip("/").replace("/", "_"))


# ── Redis (optional, graceful degradation) ────────────────────────────────
_redis = None
try:
    import redis as _redis_lib

    from src.config import REDIS_HOST, REDIS_PORT, REDIS_TTL

    _redis = _redis_lib.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    _redis.ping()
    logger.info(f"Redis connected at {REDIS_HOST}:{REDIS_PORT}")
except Exception as exc:
    logger.warning(f"Redis unavailable — prediction caching disabled ({exc})")
    _redis = None


def _cache_key(data: dict) -> str:
    return "pred:" + hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


# ── Pydantic models ────────────────────────────────────────────────────────

class TransactionInput(BaseModel):
    TransactionAmt: float = 100.0
    card1: float = 0
    card2: float = 0
    card3: float = 0
    card4: str = "visa"
    card5: float = 0
    card6: str = "debit"
    addr1: float = 0
    addr2: float = 0
    dist1: float = 0
    C1: float = 0
    C2: float = 0
    C3: float = 0
    C4: float = 0
    C5: float = 0
    C6: float = 0
    C7: float = 0
    C8: float = 0
    C9: float = 0
    C10: float = 0
    C11: float = 0
    C12: float = 0
    C13: float = 0
    C14: float = 0
    D1: float = 0
    D2: float = 0
    D3: float = 0
    D4: float = 0
    D5: float = 0
    D10: float = 0
    D11: float = 0
    D15: float = 0
    ProductCD: str = "W"
    P_emaildomain: str = "gmail.com"

    model_config = {"extra": "allow"}


class PredictionOutput(BaseModel):
    fraud_probability: float
    is_fraud: bool
    confidence: float
    cached: bool = False


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    redis_connected: bool


class ModelInfoResponse(BaseModel):
    model_type: str
    n_features: int
    metrics: dict | None


# ── Lifecycle ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def load_model():
    try:
        predictor.load()
    except FileNotFoundError:
        pass


# ── Routes ────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    redis_ok = False
    if _redis:
        try:
            _redis.ping()
            redis_ok = True
        except Exception:
            pass
    return HealthResponse(
        status="healthy",
        model_loaded=predictor.is_loaded,
        redis_connected=redis_ok,
    )


@app.get("/model-info", response_model=ModelInfoResponse)
async def model_info():
    if not predictor.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded. Train first.")
    info = predictor.get_model_info()
    return ModelInfoResponse(
        model_type=info["model_type"],
        n_features=info["n_features"],
        metrics=info["metrics"],
    )


@app.post("/predict", response_model=PredictionOutput)
async def predict(transaction: TransactionInput):
    if not predictor.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded. Train first.")

    data = transaction.model_dump()

    # Check Redis cache
    if _redis:
        try:
            key = _cache_key(data)
            cached = _redis.get(key)
            if cached:
                result = json.loads(cached)
                return PredictionOutput(**result, cached=True)
        except Exception as exc:
            logger.warning(f"Redis read failed: {exc}")

    result = predictor.predict(data)

    # Store in Redis
    if _redis:
        try:
            from src.config import REDIS_TTL
            _redis.setex(_cache_key(data), REDIS_TTL, json.dumps(result))
        except Exception as exc:
            logger.warning(f"Redis write failed: {exc}")

    return PredictionOutput(**result, cached=False)


@app.get("/eda-summary")
async def eda_summary():
    path = _BASE / "notebooks" / "eda_summary.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="EDA summary not found. Run the EDA notebook first.")
    with open(path) as f:
        return json.load(f)


@app.get("/metrics")
async def get_metrics():
    from src.config import EVAL_METRICS_PATH, TRAINING_METRICS_PATH

    data: dict = {}
    for p in [TRAINING_METRICS_PATH, EVAL_METRICS_PATH]:
        if p.exists():
            with open(p) as f:
                data.update(json.load(f))
    if not data:
        raise HTTPException(status_code=404, detail="No metrics found. Run training and evaluation first.")
    return data


@app.get("/drift-summary")
async def drift_summary(scenario: str | None = None):
    from src.config import DATA_PROCESSED_DIR, DRIFT_SUMMARY_JSON, REPORTS_MONITORING_DIR

    if scenario and scenario in ("a", "b", "c"):
        # Run monitor against the requested drifted scenario
        drift_path = DATA_PROCESSED_DIR / f"drifted_{scenario}.parquet"
        if not drift_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Drifted data for scenario '{scenario}' not found. Run 'make generate-drift' first.",
            )
        summary_path = REPORTS_MONITORING_DIR / f"drift_summary_{scenario}.json"
        if not summary_path.exists():
            # Run monitor on demand
            import subprocess, sys
            result = subprocess.run(
                [sys.executable, "-m", "src.monitor", "--current-data", str(drift_path),
                 "--output-json", str(summary_path)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=result.stderr[:500])
        if summary_path.exists():
            with open(summary_path) as f:
                return json.load(f)

    # Default: load the standard drift summary
    if not DRIFT_SUMMARY_JSON.exists():
        raise HTTPException(status_code=404, detail="Drift summary not found. Run 'make monitor' first.")
    with open(DRIFT_SUMMARY_JSON) as f:
        return json.load(f)


@app.get("/analytics/queries")
async def analytics_queries():
    try:
        from src.analytics import run_queries
        return run_queries()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"ColumnStore unavailable: {exc}")


@app.get("/eda-figures")
async def eda_figures():
    """Return list of available EDA figure filenames."""
    fig_dir = _BASE / "notebooks" / "figures"
    if not fig_dir.exists():
        return {"figures": []}
    return {"figures": sorted(p.name for p in fig_dir.glob("*.png"))}


@app.get("/report-figures")
async def report_figures():
    """Return list of available report figure filenames."""
    fig_dir = _BASE / "reports" / "figures"
    if not fig_dir.exists():
        return {"figures": []}
    return {"figures": sorted(p.name for p in fig_dir.glob("*.png"))}
