#!/usr/bin/env bash
#
# download_data.sh — fetch the IEEE-CIS Fraud Detection raw dataset into data/raw/.
#
# The raw data (~1.3 GB) is too large to commit, so a fresh clone must download it
# once before running the pipeline.
#
# Auth (no secrets are stored in this repo). Provide a Kaggle API token via either:
#   - environment variable:  export KAGGLE_API_TOKEN=KGAT_xxxxxxxx
#   - token file:            ~/.kaggle/access_token   (contains just the token string)
# Generate one at: https://www.kaggle.com/settings  ->  API  ->  Create New Token
#
# Usage:
#   ./download_data.sh
#
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_DIR="$PROJECT_ROOT/data/raw"
mkdir -p "$RAW_DIR"

# Resolve the token: env var takes precedence, then the token file.
TOKEN="${KAGGLE_API_TOKEN:-}"
if [ -z "$TOKEN" ] && [ -f "$HOME/.kaggle/access_token" ]; then
  TOKEN="$(tr -d '[:space:]' < "$HOME/.kaggle/access_token")"
fi
if [ -z "$TOKEN" ]; then
  echo "ERROR: No Kaggle token found." >&2
  echo "Set KAGGLE_API_TOKEN or save your token to ~/.kaggle/access_token." >&2
  echo "Create one at https://www.kaggle.com/settings -> API -> Create New Token." >&2
  exit 1
fi

# Skip if the data is already present.
if [ -f "$RAW_DIR/train_transaction.csv" ]; then
  echo "Raw data already present in data/raw/ — nothing to do."
  exit 0
fi

echo "Downloading IEEE-CIS Fraud Detection dataset (~1.3 GB) into data/raw/ ..."

BASE="https://www.kaggle.com/api/v1/competitions/data/download/ieee-fraud-detection"
FILES=(
  sample_submission.csv
  test_identity.csv
  test_transaction.csv
  train_identity.csv
  train_transaction.csv
)

# Use curl (near-universal) for the download and Python's stdlib for unzip, so
# this script has no third-party dependencies on a fresh machine.
for fname in "${FILES[@]}"; do
  echo "  -> $fname"
  tmp="$RAW_DIR/$fname.download"
  http_code=$(curl -sSL -w "%{http_code}" -o "$tmp" \
    -H "Authorization: Bearer $TOKEN" "$BASE/$fname")
  if [ "$http_code" != "200" ]; then
    rm -f "$tmp"
    echo "ERROR: download failed for $fname (HTTP $http_code). Check your token." >&2
    exit 1
  fi
  # Kaggle serves each file as a zip; extract if so, otherwise keep as-is.
  if python3 -c "import zipfile,sys; sys.exit(0 if zipfile.is_zipfile('$tmp') else 1)"; then
    python3 -c "import zipfile; zipfile.ZipFile('$tmp').extractall('$RAW_DIR')"
    rm -f "$tmp"
  else
    mv "$tmp" "$RAW_DIR/$fname"
  fi
done

echo "Raw data ready in data/raw/"
