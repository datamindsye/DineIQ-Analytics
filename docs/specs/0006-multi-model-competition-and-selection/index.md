# 0006. Multi-Model Candidate Competition and Champion Selection Architecture

**Date**: 2026-09-28  
**Status**: Accepted  
**Scope**: Phase 6B Multi-Algorithm Machine Learning Competition and Model Selection  

---

## 1. Executive Summary

This specification establishes the formal architecture, algorithmic candidates, evaluation contracts, and anti-leakage governance for **Phase 6B Multi-Algorithm Model Competition** in DineIQ Analytics.

To fulfill the Software Requirements Specification (SRS) requirement for rigorous algorithm selection, both the **Apache Spark MLlib pipeline** and the **independent Python data science pipeline** implement an empirical multi-algorithm tournament for each analytical task:
1. Candidate algorithms are trained exclusively on historical `TRAIN` data.
2. Candidate performance is ranked exclusively on chronological `VALIDATION` data.
3. Exactly one **Champion Model** is selected per pipeline per task using deterministic primary and tie-breaker criteria.
4. The selected Champion is evaluated on held-out `TEST` data to quantify true generalization.
5. The Champion generates the full production prediction marts (`data/marts/{spark|python}/ml_*.parquet`).
6. The Comparison Arena executes a head-to-head comparison strictly between the **Selected Spark Champion** and the **Selected Python Champion**.

At no point are candidates compared across pipelines in a combinatorial 3×3 matrix; each pipeline selects its own internal champion independently.

---

## 2. Multi-Algorithm Candidate Matrix

### 2.1 Supervised Regression: Demand Forecasting

| Pipeline | Candidate Algorithm | Hyperparameters / Configuration | Role |
|---|---|---|---|
| **Spark MLlib** | `LinearRegression` | `regParam=0.1, elasticNetParam=0.5, maxIter=100` | Baseline regularized linear model |
| **Spark MLlib** | `RandomForestRegressor` | `numTrees=20, maxDepth=5, seed=42` | Ensemble bagging tree regressor |
| **Spark MLlib** | `GBTRegressor` | `maxIter=25, maxDepth=4, stepSize=0.1, seed=42` | Gradient boosted tree regressor |
| **Python** | `Ridge` | `StandardScaler() + Ridge(alpha=1.0, random_state=42)` | L2-regularized linear regressor |
| **Python** | `RandomForestRegressor` | `n_estimators=40, max_depth=5, random_state=42, n_jobs=-1` | Ensemble bagging tree regressor |
| **Python** | `GradientBoostingRegressor` | `n_estimators=60, max_depth=4, learning_rate=0.1, random_state=42` | Gradient boosted tree regressor |

- **Primary Selection Metric**: Validation Root Mean Squared Error (RMSE) — lower is better.
- **Tie-Breaker Metric**: Validation Mean Absolute Error (MAE) — lower is better.

---

### 2.2 Supervised Classification: Wastage Risk

| Pipeline | Candidate Algorithm | Hyperparameters / Configuration | Role |
|---|---|---|---|
| **Spark MLlib** | `LogisticRegression` | `maxIter=100, regParam=0.01` | Linear probabilistic baseline |
| **Spark MLlib** | `RandomForestClassifier` | `numTrees=20, maxDepth=5, seed=42` | Bagged decision tree ensemble |
| **Spark MLlib** | `GBTClassifier` | `maxIter=25, maxDepth=4, stepSize=0.1, seed=42` | Gradient boosted classification trees |
| **Python** | `LogisticRegression` | `StandardScaler() + LogisticRegression(max_iter=500, random_state=42)` | Scaled L2 logistic regression |
| **Python** | `RandomForestClassifier` | `n_estimators=40, max_depth=5, random_state=42, n_jobs=-1` | Bagged decision tree classifier |
| **Python** | `GradientBoostingClassifier` | `n_estimators=60, max_depth=4, learning_rate=0.1, random_state=42` | Gradient boosted tree classifier |

- **Primary Selection Metric**: Validation Area Under ROC Curve (ROC-AUC) — higher is better.
- **Tie-Breaker Metric**: Validation F1-Score — higher is better.

---

### 2.3 Supervised Classification: Churn Risk

| Pipeline | Candidate Algorithm | Hyperparameters / Configuration | Role |
|---|---|---|---|
| **Spark MLlib** | `LogisticRegression` | `maxIter=100, regParam=0.01` | Linear probabilistic baseline |
| **Spark MLlib** | `RandomForestClassifier` | `numTrees=20, maxDepth=5, seed=42` | Bagged decision tree ensemble |
| **Spark MLlib** | `GBTClassifier` | `maxIter=30, maxDepth=4, stepSize=0.1, seed=42` | Gradient boosted classification trees |
| **Python** | `LogisticRegression` | `StandardScaler() + LogisticRegression(max_iter=500, random_state=42)` | Scaled L2 logistic regression |
| **Python** | `RandomForestClassifier` | `n_estimators=40, max_depth=5, random_state=42, n_jobs=-1` | Bagged decision tree classifier |
| **Python** | `GradientBoostingClassifier` | `n_estimators=60, max_depth=4, learning_rate=0.1, random_state=42` | Gradient boosted tree classifier |

- **Primary Selection Metric**: Validation Area Under ROC Curve (ROC-AUC) — higher is better.
- **Tie-Breaker Metric**: Validation F1-Score — higher is better.

---

### 2.4 Unsupervised Clustering: Customer Segmentation

| Pipeline | Candidate Algorithm | Hyperparameters / Configuration | Role |
|---|---|---|---|
| **Spark MLlib** | `KMeans` | `k=4, seed=42, maxIter=50` | Standard centroid partitioning |
| **Spark MLlib** | `BisectingKMeans` | `k=4, seed=42, maxIter=50` | Hierarchical divisive bisection clustering |
| **Python** | `KMeans` | `n_clusters=4, random_state=42, n_init=10, max_iter=300` | Standard k-means clustering |
| **Python** | `GaussianMixture` | `n_components=4, random_state=42` | Expectation-maximization mixture model |

- **Selection Metric**: Silhouette Score computed on standardized RFM features (`recency_days`, `frequency`, `monetary_total`) — higher is better.
- **Label Mapping**: Post-hoc deterministic mapping based on centroid RFM ordering (`Champions`, `Loyal`, `At Risk`, `Lost`).

---

## 3. Temporal Anti-Leakage & Selection Isolation Protocol

To guarantee mathematical integrity and avoid lookahead bias, the four chronological partitions are strictly isolated:

```
[       TRAIN        ] [   VALIDATION   ] [      TEST      ] [ UNSEEN COMPARISON ]
  Jan 1 - Aug 31, 2025   Sep 1 - Oct 31     Nov 1 - Nov 30      Dec 1 - Dec 31
  ────────────────────   ───────────────    ──────────────      ─────────────────
  Fit all candidates     Rank candidates    Evaluate ONLY       Cross-Pipeline
                         Select Champion    Selected Champion   Consensus Arena
```

1. **Candidate Training**: Fit solely on `TRAIN` ($\le$ 2025-08-31). Zero access to validation, test, or unseen data during fitting.
2. **Champion Selection**: Predict and evaluate exclusively on `VALIDATION` (2025-09-01 to 2025-10-31). Primary metrics rank the candidates, and tie-breakers resolve any ties deterministically.
3. **Test Evaluation**: Only the single winning champion is evaluated on `TEST` (2025-11-01 to 2025-11-30). Test metrics never feed back into candidate selection.
4. **Unseen Comparison Isolation**: December 2025 is reserved exclusively for the Cross-Pipeline Comparison Arena. Neither candidate training nor selection ever touches December records.

---

## 4. Dual-Pipeline Independence Rule

The Spark and Python pipelines maintain strict architectural and computational independence:
- **No Shared Feature DataFrames**: Spark builds its feature sets using PySpark DataFrames and SQL Window functions; Python builds its feature sets using Pandas and NumPy.
- **No Shared Model Objects or Weights**: Spark models exist solely in PySpark MLlib; Python models exist solely in scikit-learn.
- **No Prediction Cross-Talk**: Output marts are written to distinct physical directories (`data/marts/spark/` and `data/marts/python/`).
- **Code Import Boundary**: Static analysis verifies zero cross-package imports between `packages.pipeline_spark` and `packages.pipeline_python`.

---

## 5. Metadata and Governance Schema

Each pipeline execution saves an enriched, versioned metadata document into `data/artifacts/{pipeline}_{task}_metadata.json`:

```json
{
  "pipeline": "spark",
  "task": "demand_forecast",
  "model_version": "v2.0-phase6b",
  "selected_algorithm": "GBTRegressor",
  "algorithm": "GBTRegressor",
  "selection_criteria": "validation_rmse (lower is better, validation_mae tie-breaker)",
  "selection_reason": "GBTRegressor selected with validation RMSE=3.8912 and MAE=2.5401",
  "candidates": [
    {
      "algorithm": "LinearRegression",
      "hyperparameters": { "regParam": 0.1, "elasticNetParam": 0.5, "maxIter": 100 },
      "validation_metrics": { "rmse": 4.8123, "mae": 3.0112 },
      "training_duration_sec": 4.12
    },
    {
      "algorithm": "RandomForestRegressor",
      "hyperparameters": { "numTrees": 20, "maxDepth": 5, "seed": 42 },
      "validation_metrics": { "rmse": 4.1025, "mae": 2.7104 },
      "training_duration_sec": 7.35
    },
    {
      "algorithm": "GBTRegressor",
      "hyperparameters": { "maxIter": 25, "maxDepth": 4, "stepSize": 0.1, "seed": 42 },
      "validation_metrics": { "rmse": 3.8912, "mae": 2.5401 },
      "training_duration_sec": 12.80
    }
  ],
  "feature_cols": [...],
  "target_col": "weekly_quantity",
  "rows_train": 94805,
  "rows_validation": 24449,
  "rows_test": 10850,
  "validation_metrics": { "rmse": 3.8912, "mae": 2.5401 },
  "test_metrics": { "rmse": 4.2150, "mae": 2.8910 },
  "metrics": {
    "validation": { "rmse": 3.8912, "mae": 2.5401 },
    "test": { "rmse": 4.2150, "mae": 2.8910 }
  },
  "duration_sec": 45.12
}
```

---

## 6. Comparison Arena Integration

The Comparison Arena (`packages/comparison/evaluator.py`) consumes the final prediction marts from both pipelines and compares:
$$\text{Selected Spark Champion} \quad \text{vs} \quad \text{Selected Python Champion}$$

The overall agreement rate remains defined as the unweighted arithmetic mean across the four analytical domains:
$$\text{Overall Agreement \%} = \frac{A_{\text{demand}} + A_{\text{wastage}} + A_{\text{churn}} + A_{\text{segmentation}}}{4}$$

Comparison summaries explicitly log:
- `spark_selected_algorithm`
- `python_selected_algorithm`
Ensuring full traceability from candidate competition to the final consensus scorecard.
