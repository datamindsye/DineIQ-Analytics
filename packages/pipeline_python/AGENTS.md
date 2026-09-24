# Python Data Science Pipeline Package

## Overview

Independent data science pipeline using Pandas, NumPy, and scikit-learn for statistical preprocessing, feature engineering, and predictive modeling.

## Key files

| File | Owns |
|---|---|
| `runner.py` | Pipeline runner interface for independent execution |

## Conventions

- Ingest raw and clean dataset snapshots independently from `data/snapshots/`.
- Never import or use Spark feature tables or Spark ML outputs.
- Write analytical feature marts into `data/marts/{run_id}/python/` in Parquet format.
- Output predictions conforming exactly to the evaluation contract schema.

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
