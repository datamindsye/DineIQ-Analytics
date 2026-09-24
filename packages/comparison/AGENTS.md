# Cross Pipeline Comparison Package

## Overview

Independent evaluation and comparison framework. Ingests test set predictions from Spark and Python pipelines, applies formal evaluation contracts, and calculates comparative metrics and diffs.

## Key files

| File | Owns |
|---|---|
| `evaluator.py` | Comparator implementation calculating metric diffs and agreement |

## Conventions

- Ingest prediction marts from both pipelines in a read only manner.
- Compute Precision, Recall, F1 Score, ROC AUC, PR AUC, and Brier Score using identical mathematical definitions.
- Write comparison records to PostgreSQL and comparison Parquet marts.

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
