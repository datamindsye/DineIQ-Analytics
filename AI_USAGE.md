# DineIQ Analytics — AI Usage Declaration

**Document ID**: `DECLARATION-AI-USAGE-20260926`  
**Repository**: `DineIQ-Analytics`  
**Project**: Data Science Intelligence Arena  
**Date**: September 26, 2026  
**Status**: Official Competition & Academic Integrity Statement  
**Branch**: `feature/phase3-spark-marts`

---

## 1. Purpose & Scope

This document provides a transparent, factual, and comprehensive declaration of artificial intelligence (AI) usage throughout the design, development, testing, and documentation of the **DineIQ Analytics** platform.

In alignment with competition rules, academic integrity standards, and software engineering best practices, this declaration details:
1. The exact scope and nature of AI assistance across project phases.
2. The mandatory human-in-the-loop review, testing, and validation process.
3. The boundary between AI tooling and the human engineering team's ultimate ownership and accountability.
4. The verification protocols ensuring that no metrics, test outputs, or analytical findings were fabricated.

---

## 2. Model & Tooling Overview

During project execution, large language models and agentic developer tooling (specifically Google DeepMind Antigravity and Claude-based engineering assistants) were utilized as **collaborative pair-programming and code-analysis instruments**, analogous to an advanced integrated development environment (IDE) plugin, automated linter, or interactive technical documentation reference.

AI usage is categorized into two distinct modalities:
- **Implementation Assistance**: Scaffolding repetitive schemas, drafting initial query structures, generating unit test fixtures, and assisting in refactoring.
- **Documentation & Review Assistance**: Formatting technical specifications, drafting data dictionary entries, performing static forensic audits of schemas, and checking traceability against the competition SRS.

---

## 3. Human Oversight & Responsibility Statement

**AI assistance does not imply authorship of the DineIQ Analytics platform.**

All architectural blueprints, engineering decisions, business logic rules, mathematical formulas, and code integrations remain the sole work product and responsibility of the human development team (**Data Minds**).

Specifically:
- **No Blind Acceptance**: No code, query, migration script, or configuration generated or suggested by an AI assistant was accepted or merged without line-by-line review, architectural evaluation, and comprehension by human team members.
- **Independent Validation**: Every domain model, API router, data contract, Spark transformation, and cleaning rule was independently validated against the project System Requirements Specification (SRS v1.0).
- **Technical Competence & Defense**: The human team fully understands, can defend, and will explain every architectural pattern, mathematical formula, database constraint, and pipeline algorithm implemented in this repository during competitive technical evaluation and live oral defense.
- **Sole Authorship of Final Product**: AI tools functioned strictly as accelerators; the human engineering team retains full accountability and intellectual ownership for the final system state.
- **No External Generative Decision API**: The system does NOT call external commercial LLMs (OpenAI, Gemini API, Anthropic) at runtime as a black-box decision engine to generate analytical findings, menu classifications, or forecasts. All analytical results are calculated deterministically by native project code and reproducible data science pipelines.

---

## 4. Phase-by-Phase AI Assistance Log

### Phase 1: Architecture & Foundation
- **Tool Name**: Google DeepMind Antigravity / Claude Code
- **Type of Assistance**: Implementation & Review Assistance
- **Purpose**: Modular monolith scaffolding, SQLAlchemy 2.0 ORM models, FastAPI route structuring, and RBAC permission models.
- **Affected Files/Modules**: `apps/api/`, `packages/db/`, `packages/core/`, `tests/api/`
- **Modifications Made by Team**: Replaced generic exceptions with custom `ErrorEnvelope`, refined Alembic migration scripts, and established strict database pre-ping pooling.
- **Tests Performed**: 34 API and unit tests passed under pytest.
- **Reviewed & Verified By**: `[Team Member Name / Reviewer]`

### Phase 2: Dataset Generation & Data Quality Pipeline
- **Tool Name**: Google DeepMind Antigravity
- **Type of Assistance**: Implementation & Documentation Assistance
- **Purpose**: Synthetic transaction logic scaffolding, Pareto distribution curves, SCD Type 2 pricing history modeling, and quality rule definitions.
- **Affected Files/Modules**: `packages/common/generator/`, `packages/common/quality/`, `docs/data-dictionary.md`, `docs/reports/dataset_inspection_report.md`
- **Modifications Made by Team**: Calibrated meal rush hours, added cascading quarantine logic for orphaned order lines, and verified financial reconciliation formulas ($0.00$ variance across 1.31M rows).
- **Tests Performed**: 79 tests passed; empirical verification of 1,302,220 clean records and 9,044 quarantined records.
- **Reviewed & Verified By**: `[Team Member Name / Reviewer]`

### Phase 3: Apache Spark Analytical Pipeline & Feature Engineering
- **Tool Name**: Google DeepMind Antigravity
- **Type of Assistance**: Implementation & Review Assistance
- **Purpose**: Scaffolding native PySpark DataFrame transformations and Spark SQL temporary views for 12 analytical marts, authoring analytical Pydantic schemas, and authoring unit tests.
- **Affected Files/Modules**:
  - `packages/pipeline_spark/session.py` (Local SparkSession factory, Hadoop winutils config)
  - `packages/pipeline_spark/schemas.py` (Typed StructType schemas for clean tables)
  - `packages/pipeline_spark/loader.py` (Parquet table loader)
  - `packages/pipeline_spark/joins.py` (Standardized broadcast/hash joins)
  - `packages/pipeline_spark/marts/` (12 mart generators)
  - `packages/pipeline_spark/runner.py` (Orchestration runner)
  - `packages/core/contracts/analytical_contracts.py` (Pydantic mart contracts)
  - `tests/unit/test_spark_pipeline.py`, `tests/unit/test_marts.py`, `tests/unit/test_analytical_contracts.py`
  - `docs/specs/0005-spark-analytical-pipeline-and-marts/index.md`
- **Modifications & Critical Corrections Made by Team**:
  - **Forensic Physical Schema Verification**: Cross-checked all PySpark references against actual Parquet schemas in `data/cleaned/competition_benchmark_v1/`, eliminating any prospective or non-existent columns.
  - **Defect Discovery and Correction in Sales Anomalies**: During forensic audit, the team detected a baseline leakage defect in `packages/pipeline_spark/marts/sales_anomalies.py` where `rowsBetween(-13, 0)` included the current day $t$ in its own 14-day rolling average and standard deviation. The team corrected this window to `rowsBetween(-14, -1)`, strictly isolating prior historical observations and preventing self-contamination.
  - **Regression Test Authoring**: Implemented `test_sales_anomalies_rolling_baseline_excludes_current_day` in `tests/unit/test_marts.py` to permanently protect against future baseline leakage.
  - **Runtime Verification**: Configured native Windows Hadoop 3.3.0 binary tooling (`winutils.exe`, `hadoop.dll`) under `C:\hadoop` to enable native Spark `FileOutputCommitter` and Snappy Parquet materialization on local Windows environments.
  - **Physical Mart Verification**: Executed the Spark pipeline end-to-end and physically inspected the 12 output directories in `data/marts/spark/`, validating row counts, column counts, and `_SUCCESS` markers (741,310 total records).
- **Tests Performed**:
  - Full automated pytest suite: **108 passed out of 108 tests** (100% pass rate in ~71 seconds).
  - Ruff static analysis: `ruff check .` passed with 0 errors and 0 warnings.
  - Targeted regression test verifying that day $t$ does not contaminate rolling baseline calculations.
- **Reviewed & Verified By**: `[Team Member Name / Reviewer]`

---

## 5. Verification Protocols & Metric Integrity

A foundational principle of DineIQ Analytics is strict factual integrity and mathematical reproducibility:

1. **Zero Metric Fabrication**:
   - AI assistants were **strictly prohibited** from fabricating, hallucinating, or approximating dataset counts, data quality defect totals, cleanliness percentages, or test results.
   - All dataset metrics recorded in `docs/data-dictionary.md`, `docs/reports/dataset_inspection_report.md`, and `docs/development_log.md` were derived via automated physical scans of actual Apache Parquet files on disk using embedded Python/PyArrow scripts.
   - The authoritative totals (**1,311,264 raw records**, **1,302,220 cleaned records**, and **9,044 quarantined records**) represent exact, verifiable file calculations.
   - All mart row counts (**741,310 precomputed records across 12 analytical marts**) were physically verified from the materialized Parquet part-files.

2. **Automated Test Gate Enforcement**:
   - Code suggested during development was verified using local test suites (`pytest tests/ -v`), static analysis (`ruff check .`), and style formatting (`ruff format --check .`).
   - Every feature gate required 100% test passage (**108 of 108 passing tests**) before acceptance.

3. **Reproducibility Guarantee**:
   - All synthetic datasets, data cleaning outputs, and analytical marts are deterministically reproducible by running the documented CLI commands with fixed seeds (`--seed 42`). No proprietary, non-reproducible manual interventions were introduced.

---

## 6. Summary Declaration

The team certifies that DineIQ Analytics represents an original engineering effort executed with high professional rigor. AI tools were employed responsibly as modern productivity accelerators, accompanied by comprehensive verification, empirical validation, and complete human technical governance.
