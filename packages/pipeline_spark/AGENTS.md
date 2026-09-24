# Spark Analytics Pipeline Package

## Overview

Big data ingestion, data quality verification, multi table joins, and Spark MLlib modeling package built with Apache Spark, PySpark, and Spark SQL.

## Key files

| File | Owns |
|---|---|
| `session.py` | SparkSession factory and local cluster configuration |

## Conventions

- Run PySpark in local mode (`local[*]`) for local development without distributed cluster requirements.
- Write analytical feature marts into `data/marts/{run_id}/spark/` in Parquet format.
- Strictly adhere to dual pipeline isolation rules: never share prepared feature dataframes, trained model weights, or predictions with the Python pipeline.
- Implement time aware modeling: prevent future data leakage by splitting datasets chronologically.

## Gotchas

- PySpark requires a Java Runtime Environment (JRE 11 or 17). Check `is_spark_available()` before attempting Spark operations.

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
