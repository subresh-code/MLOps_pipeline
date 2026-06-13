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

KAGGLE_TOKEN="$TOKEN" RAW_DIR="$RAW_DIR" python3 <<'PY'
import io
import os
import sys
import zipfile

import requests

token = os.environ["KAGGLE_TOKEN"]
out_dir = os.environ["RAW_DIR"]
headers = {"Authorization": f"Bearer {token}"}
base = "https://www.kaggle.com/api/v1/competitions/data/download/ieee-fraud-detection"

files = [
    "sample_submission.csv",
    "test_identity.csv",
    "test_transaction.csv",
    "train_identity.csv",
    "train_transaction.csv",
]

for fname in files:
    print(f"  -> {fname}", flush=True)
    r = requests.get(f"{base}/{fname}", headers=headers, stream=True, allow_redirects=True)
    if r.status_code != 200:
        sys.exit(f"Download failed for {fname}: HTTP {r.status_code}. Check your token.")
    content = b"".join(r.iter_content(chunk_size=1024 * 1024))
    if r.headers.get("Content-Type") == "application/zip":
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            z.extractall(out_dir)
    else:
        with open(os.path.join(out_dir, fname), "wb") as f:
            f.write(content)

print("Done.")
PY

echo "Raw data ready in data/raw/"
