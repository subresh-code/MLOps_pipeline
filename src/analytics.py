"""
MariaDB ColumnStore analytical layer.

Creates and populates the fraud_transactions table using the ColumnStore
columnar engine, then exposes analytical query functions for Data Scientists
and Analysts to run ad hoc SQL over the stored data.
"""
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def _get_engine():
    from sqlalchemy import create_engine

    from src.config import (
        COLUMNSTORE_DATABASE,
        COLUMNSTORE_HOST,
        COLUMNSTORE_PASSWORD,
        COLUMNSTORE_PORT,
        COLUMNSTORE_USER,
    )

    dsn = (
        f"mysql+pymysql://{COLUMNSTORE_USER}:{COLUMNSTORE_PASSWORD}"
        f"@{COLUMNSTORE_HOST}:{COLUMNSTORE_PORT}/{COLUMNSTORE_DATABASE}"
        "?charset=utf8mb4"
    )
    return create_engine(dsn, pool_pre_ping=True)


def _pandas_dtype_to_sql(dtype) -> str:
    kind = dtype.kind
    if kind == "f":
        return "DOUBLE"
    if kind == "i" or kind == "u":
        return "BIGINT"
    return "VARCHAR(64)"


def _check_columnstore_available(engine) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            __import__("sqlalchemy").text("SHOW ENGINES")
        )
        for row in result:
            if "columnstore" in str(row[0]).lower():
                return True
    return False


def create_table(engine, df: pd.DataFrame, table: str, use_columnstore: bool = True) -> None:
    """Create the analytical table with ColumnStore (or InnoDB fallback) engine."""
    col_defs = ",\n  ".join(
        f"`{col}` {_pandas_dtype_to_sql(df[col].dtype)}"
        for col in df.columns
    )
    engine_clause = "ENGINE=ColumnStore" if use_columnstore else "ENGINE=InnoDB"
    ddl = (
        f"CREATE TABLE IF NOT EXISTS `{table}` (\n  {col_defs}\n) "
        f"{engine_clause} DEFAULT CHARSET=utf8mb4;"
    )
    with engine.connect() as conn:
        conn.execute(__import__("sqlalchemy").text(f"DROP TABLE IF EXISTS `{table}`"))
        conn.execute(__import__("sqlalchemy").text(ddl))
        conn.commit()
    logger.info(f"Table `{table}` created ({engine_clause})")


def load_parquet(parquet_path, table: str | None = None, chunksize: int = 5000) -> dict:
    """
    Load a processed Parquet file into the ColumnStore analytical table.

    Returns a summary dict with row counts and table name.
    """
    from src.config import COLUMNSTORE_TABLE, PROCESSED_TEST_FILE, PROCESSED_TRAIN_FILE

    import sqlalchemy as sa

    if table is None:
        table = COLUMNSTORE_TABLE

    engine = _get_engine()

    use_cs = _check_columnstore_available(engine)
    if not use_cs:
        logger.warning("ColumnStore engine not found — falling back to InnoDB")

    train = pd.read_parquet(PROCESSED_TRAIN_FILE)
    test = pd.read_parquet(PROCESSED_TEST_FILE)
    df = pd.concat([train, test], ignore_index=True)
    logger.info(f"Loaded {len(df):,} rows × {df.shape[1]} columns from Parquet")

    create_table(engine, df, table, use_columnstore=use_cs)

    df.to_sql(
        table,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=chunksize,
        method="multi",
    )
    logger.info(f"Inserted {len(df):,} rows into `{table}`")

    return {
        "rows_loaded": len(df),
        "columns": df.shape[1],
        "engine": "ColumnStore" if use_cs else "InnoDB",
        "table": table,
    }


def run_queries() -> dict[str, Any]:
    """Run a standard set of analytical queries and return results as dicts."""
    import sqlalchemy as sa

    from src.config import COLUMNSTORE_TABLE

    engine = _get_engine()
    table = COLUMNSTORE_TABLE

    results: dict[str, Any] = {}

    def q(sql: str) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(sa.text(sql)).fetchall()
            cols = conn.execute(sa.text(sql)).keys()
        # re-run to get column names properly
        with engine.connect() as conn:
            res = conn.execute(sa.text(sql))
            keys = list(res.keys())
            return [dict(zip(keys, row)) for row in res.fetchall()]

    # 1. Fraud rate by ProductCD (label-encoded)
    results["fraud_rate_by_product"] = q(f"""
        SELECT ProductCD,
               COUNT(*) AS txn_count,
               SUM(isFraud) AS fraud_count,
               ROUND(AVG(isFraud) * 100, 2) AS fraud_rate_pct
        FROM `{table}`
        GROUP BY ProductCD
        ORDER BY fraud_rate_pct DESC
    """)

    # 2. Average transaction amount by fraud/non-fraud
    results["amount_by_fraud"] = q(f"""
        SELECT isFraud,
               COUNT(*) AS txn_count,
               ROUND(AVG(TransactionAmt), 2) AS avg_amount,
               ROUND(MIN(TransactionAmt), 2) AS min_amount,
               ROUND(MAX(TransactionAmt), 2) AS max_amount
        FROM `{table}`
        GROUP BY isFraud
    """)

    # 3. Fraud rate by card type
    results["fraud_rate_by_card_type"] = q(f"""
        SELECT card6,
               COUNT(*) AS txn_count,
               ROUND(AVG(isFraud) * 100, 2) AS fraud_rate_pct
        FROM `{table}`
        GROUP BY card6
        ORDER BY fraud_rate_pct DESC
    """)

    # 4. Top 10 C-features by average value for fraud vs non-fraud
    results["c_features_fraud_vs_legit"] = q(f"""
        SELECT isFraud,
               ROUND(AVG(C1), 4) AS C1, ROUND(AVG(C2), 4) AS C2,
               ROUND(AVG(C3), 4) AS C3, ROUND(AVG(C4), 4) AS C4,
               ROUND(AVG(C5), 4) AS C5, ROUND(AVG(C6), 4) AS C6
        FROM `{table}`
        GROUP BY isFraud
    """)

    # 5. Overall summary
    results["summary"] = q(f"""
        SELECT COUNT(*) AS total_rows,
               SUM(isFraud) AS total_fraud,
               ROUND(AVG(isFraud) * 100, 2) AS fraud_rate_pct,
               ROUND(AVG(TransactionAmt), 2) AS avg_amount
        FROM `{table}`
    """)

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    summary = load_parquet(None)
    print(f"\nLoaded: {summary['rows_loaded']:,} rows into `{summary['table']}` ({summary['engine']})")
