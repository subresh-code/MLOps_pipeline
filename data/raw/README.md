# Raw Data!
This directory should contain the IEEE-CIS Fraud Detection dataset files.

**Required files:**
- `train_transaction.csv`
- `train_identity.csv`

**Download:**
The dataset is available on Kaggle at:
https://www.kaggle.com/c/ieee-fraud-detection/data

**Instructions:**
1. Download the dataset from Kaggle (requires a free Kaggle account).
2. Place `train_transaction.csv` and `train_identity.csv` in this directory.
3. Run `make train` from the project root to start the pipeline.

**Note:** These files are not included in the submission ZIP due to their combined size (~1 GB). The pipeline will raise a clear `FileNotFoundError` if they are missing.
