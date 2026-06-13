#!/usr/bin/env bash
#
# run_pipeline.sh — one-command, hands-off MLOps pipeline.
#
# Brings up Airflow in Docker and runs the full DAG:
#   ingest_data -> preprocess_data -> train_model -> evaluate_model
#   -> generate_drift_data -> monitor_drift
#
# Usage:
#   ./run_pipeline.sh              # run the pipeline via Airflow and wait for it to finish
#   ./run_pipeline.sh --no-wait    # trigger the pipeline and return immediately
#   ./run_pipeline.sh --full-stack # also start api, frontend, redis, mariadb, mlflow
#
set -euo pipefail

# Resolve project root to this script's location so it works from any CWD.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

DAG_ID="fraud_detection_mlops_pipeline"
CONTAINER="mlops_pipeline-airflow-1"
WAIT=true
FULL_STACK=false

for arg in "$@"; do
  case "$arg" in
    --no-wait)    WAIT=false ;;
    --full-stack) FULL_STACK=true ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -20
      exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

log() { echo -e "\033[1;34m[pipeline]\033[0m $*"; }

# 1. Make sure raw data is present — the pipeline can't run without it.
if [ ! -f "data/raw/train_transaction.csv" ]; then
  echo "ERROR: data/raw/train_transaction.csv not found." >&2
  echo "Download the IEEE-CIS Fraud Detection dataset into data/raw/ first." >&2
  exit 1
fi

# 2. Ensure the Airflow container user (uid 50000) can write pipeline outputs.
log "Fixing output directory permissions..."
mkdir -p data/processed models reports/metrics reports/figures reports/monitoring mlflow_tracking
chmod -R 777 data/processed models reports mlflow_tracking 2>/dev/null || true

# 3. Start services.
if [ "$FULL_STACK" = true ]; then
  log "Building and starting the full stack (this may take a few minutes)..."
  docker compose up -d --build
else
  log "Building and starting Airflow..."
  docker compose up -d --build airflow
fi

# 4. Wait for Airflow to register the DAG.
log "Waiting for Airflow to register the DAG..."
until docker exec "$CONTAINER" airflow dags list 2>/dev/null | grep -q "$DAG_ID"; do
  sleep 5
done

# 5. Unpause (belt-and-suspenders; compose already sets DAGS_ARE_PAUSED_AT_CREATION=False).
docker exec "$CONTAINER" airflow dags unpause "$DAG_ID" >/dev/null 2>&1 || true

# 6. Trigger a fresh run.
RUN_ID="cli__$(date +%Y%m%dT%H%M%S)"
log "Triggering pipeline run: $RUN_ID"
docker exec "$CONTAINER" airflow dags trigger "$DAG_ID" --run-id "$RUN_ID" >/dev/null

if [ "$WAIT" = false ]; then
  log "Triggered. Track progress at http://localhost:8080 (admin/admin)."
  exit 0
fi

# 7. Wait for the run to reach a terminal state, printing task states as it goes.
log "Waiting for the run to complete..."
while true; do
  STATE="$(docker exec "$CONTAINER" airflow dags list-runs -d "$DAG_ID" 2>/dev/null \
            | grep "$RUN_ID" | awk -F'|' '{gsub(/ /,"",$3); print $3}')"
  echo "  --- $(date +%H:%M:%S)  run state: ${STATE:-starting} ---"
  docker exec "$CONTAINER" airflow tasks states-for-dag-run "$DAG_ID" "$RUN_ID" 2>/dev/null \
    | grep -E "ingest|preprocess|train|evaluate|generate|monitor" | awk -F'|' '{print "   ", $3, $4}'
  case "$STATE" in
    success) log "Pipeline finished successfully ✓"; exit 0 ;;
    failed)  log "Pipeline FAILED ✗ — check logs at http://localhost:8080"; exit 1 ;;
  esac
  sleep 20
done
