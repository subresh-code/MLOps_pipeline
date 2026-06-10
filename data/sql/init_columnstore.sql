-- MariaDB ColumnStore initialization
-- The fraud_transactions table is created dynamically by src/analytics.py
-- based on the actual Parquet schema. This script only creates the database.

CREATE DATABASE IF NOT EXISTS fraud_analytics
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'analyst'@'%' IDENTIFIED BY 'analyst123';
GRANT ALL PRIVILEGES ON fraud_analytics.* TO 'analyst'@'%';
FLUSH PRIVILEGES;
