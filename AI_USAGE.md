# DineIQ Analytics — AI Usage Declaration

**Document ID**: `DECLARATION-AI-USAGE-20260925`  
**Repository**: `DineIQ-Analytics`  
**Project**: Data Science Intelligence Arena  
**Date**: September 25, 2026  
**Status**: Official Competition & Academic Integrity Statement  

---

## 1. Purpose & Scope

This document provides a transparent, factual, and comprehensive declaration of artificial intelligence (AI) usage throughout the design, development, testing, and documentation of the **DineIQ Analytics** platform.

In alignment with competition rules, academic integrity standards, and software engineering best practices, this declaration details:
1. The exact scope and nature of AI assistance.
2. The mandatory human-in-the-loop review, testing, and validation process.
3. The boundary between AI tooling and the human engineering team's ultimate ownership and accountability.
4. The verification protocols ensuring that no metrics, test outputs, or analytical findings were fabricated.

---

## 2. Model & Tooling Overview

During project execution, large language models and agentic developer tooling (specifically Google DeepMind Antigravity and Claude-based engineering assistants) were utilized as **collaborative pair-programming and code-analysis instruments**, analogous to an advanced integrated development environment (IDE) plugin, automated linter, or interactive technical documentation reference.

Key areas of AI assistance included:
- **Architecture & Design Exploration**: Brainstorming modular monolith directory layouts, decoupling strategies between dual analytics pipelines (Apache Spark vs. Python Data Science), and reviewing schema patterns against competition specifications.
- **Boilerplate & Schema Generation**: Scaffolding repetitive structures such as SQLAlchemy 2.0 ORM mappings, Pydantic schemas, and PyArrow schema definitions based on human-defined data contracts.
- **Synthetic Data Generation Logic**: Assisting in the implementation of domain distributions (e.g., peak dining hour curves, menu engineering categories, realistic anomaly injection) according to project design criteria.
- **Test Scaffolding**: Drafting automated unit test suites and edge-case assertions under `pytest` to guarantee comprehensive branch coverage.
- **Documentation & Reporting**: Drafting structural outlines, data dictionary entries, and forensic markdown reports summarizing empirical dataset profiles and quality reconciliation audits.
- **Refactoring & Lint Optimization**: Addressing Ruff lint warnings, type annotations, and import ordering.

---

## 3. Human Oversight & Responsibility Statement

**AI assistance does not imply authorship of the DineIQ Analytics platform.** 

All architectural blueprints, engineering decisions, business logic rules, and code integrations remain the sole work product and responsibility of the human development team (**Data Minds**).

Specifically:
- **No Blind Acceptance**: No code, migration script, or configuration generated or suggested by an AI assistant was accepted or merged without line-by-line review, architectural evaluation, and comprehension by human team members.
- **Independent Validation**: Every domain model, API router, data contract, and cleaning rule was independently validated against the project System Requirements Specification (SRS).
- **Technical Competence & Defense**: The human team fully understands, can defend, and will explain every architectural pattern, mathematical formula, database constraint, and pipeline algorithm implemented in this repository during competitive technical evaluation and live oral defense.
- **Sole Authorship of Final Product**: AI tools functioned strictly as accelerators; the human engineering team retains full accountability and intellectual ownership for the final system state.

---

## 4. Verification Protocols & Metric Integrity

A foundational principle of DineIQ Analytics is strict factual integrity and mathematical reproducibility:

1. **Zero Metric Fabrication**:
   - AI assistants were **strictly prohibited** from fabricating, hallucinating, or approximating dataset counts, data quality defect totals, cleanliness percentages, or test results.
   - All dataset metrics recorded in `docs/data-dictionary.md`, `docs/reports/dataset_inspection_report.md`, and `docs/development_log.md` were derived via automated physical scans of actual Apache Parquet files on disk using embedded Python/PyArrow scripts.
   - The authoritative totals (**1,311,264 raw records**, **1,302,220 cleaned records**, and **9,044 quarantined records**) represent exact, verifiable file calculations.

2. **Automated Test Gate Enforcement**:
   - Code suggested during development was verified using local test suites (`pytest tests/ -q`), static analysis (`ruff check .`), and style formatting (`ruff format --check .`).
   - Every feature gate required 100% test passage (79 of 79 passing tests across unit and API layers) before acceptance.

3. **Reproducibility Guarantee**:
   - All synthetic datasets and data cleaning outputs are deterministically reproducible by running the documented CLI commands with fixed seeds (`--seed 42`). No proprietary, non-reproducible manual interventions were introduced.

---

## 5. Summary Declaration

The team certifies that DineIQ Analytics represents an original engineering effort executed with high professional rigor. AI tools were employed responsibly as modern productivity accelerators, accompanied by comprehensive verification, empirical validation, and complete human technical governance.
