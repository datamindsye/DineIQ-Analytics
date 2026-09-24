# 0003. Dataset Contract and Generation Strategy — Decision Record

## Context

The DineIQ Analytics platform requires a high volume, realistic dataset to power two independent analytics pipelines (Apache Spark and Python data science), executive business intelligence dashboards, and machine learning models. The competition Software Requirements Specification mandates an extensive dataset spanning eleven core business tables with at least one million order line items, one hundred thousand unique orders, fifty thousand customers, one hundred fifty menu items across ten categories, twenty restaurant locations, twelve months of transaction history, one hundred thousand ratings, and fifty thousand wastage entries.

Beyond mere record volume, the SRS explicitly demands realistic operational complexity. Restaurant point of sale systems do not produce uniformly distributed, clean records. In production environments, transaction volume ebbs and flows according to meal times, weekends, and holidays. Customer purchasing behaviors follow power law Pareto curves. Inventory spoils at varying rates depending on item perishability. Discounts sometimes result in promotion traps where high sales volume produces negative contribution margins. Furthermore, real world data pipelines must handle guest checkouts with missing customer identifiers, occasional duplicate records, out of range ratings, and price transitions over time.

Generating this dataset presents two severe failure modes if designed improperly:
1. Trivial uniform noise: if data is generated using uniform random numbers across all entities, downstream analytical algorithms (such as K-Means customer clustering, market basket association mining, demand forecasting, and menu BCG matrix classification) will encounter flat, homogenous distributions devoid of meaningful clusters or statistical signals.
2. Future data leakage: if temporal boundaries are not strictly established at generation time, feature engineering routines could draw upon future sales to predict past outcomes, destroying the credibility of the competition submission.

This specification addresses these forces by formalizing the dataset generation contract, statistical distributions, data quality rules, and chronological split boundaries.

## Options considered

### Option 1: Deterministic Multi Profile Synthetic Generator with Embedded Business Realism (Chosen)

In this approach, a custom generator script in `packages/common/generator/` utilizes fixed random seeds and parameterized statistical distributions (bimodal temporal curves, Pareto customer frequency, Zipf item popularity, sinusoidal seasonal modulations) to produce realistic, reproducible data across all eleven tables. The generator supports three configuration profiles (`dev`, `competition`, `stress`), provides chunked streaming writes to Parquet and CSV to conserve local RAM, and exports a chronological split manifest locking the evaluation windows.

**Pros**:
- Produces realistic business patterns that allow machine learning algorithms and executive dashboards to discover genuine insights.
- Fully reproducible using a single master seed, enabling identical datasets across all team member machines and CI pipelines.
- Supports lightweight local development testing (< 15 seconds) alongside full scale one million row generation.
- Strict chronological split manifests eliminate future data leakage.
- Preserves stable business identifiers (`source_*_id`) across all tables.

**Cons**:
- Requires deliberate engineering of seventeen domain specific complexity injection rules.
- Streaming generation of one million rows requires careful memory management to run smoothly on developer workstations.

### Option 2: Generic Uniform Random Generator

In this approach, standard random generators (such as pure random uniform integers and dates) populate fields without modeling dining categories, meal peak hours, customer loyalty tiers, or menu engineering margin quadrants.

**Pros**:
- Simpler to write and quick to generate initially.

**Cons**:
- Fails to produce realistic business patterns: all items sell with equal probability, meal rushes do not exist, and customer RFM distributions are flat.
- Downstream machine learning models (clustering, forecasting, association rules) achieve low accuracy or meaningless results because no underlying statistical signal exists.
- Violates explicit SRS requirements demanding realistic operational complexity.

### Option 3: External Synthetic Data Cloud Service or LLM Generation

In this approach, commercial cloud services or large language models are invoked via external APIs to generate millions of tabular records.

**Pros**:
- Offloads local generation compute.

**Cons**:
- Incurs substantial monetary costs and token quotas to generate one million rows.
- Violates the core competition constraint prohibiting external proprietary cloud services.
- Generation cannot be run offline, in CI, or deterministically reproduced from a fixed local seed.

## Rationale

Option 1 is selected because it directly aligns with the competition objectives and technical constraints. By incorporating verified statistical distributions (bimodal Gaussian peak hours, Pareto customer spend, sinusoidal annual seasonality, and power law dish popularity), the synthetic dataset mirrors real restaurant operational dynamics. Downstream machine learning models in Spark MLlib and scikit-learn will have authentic patterns to discover, validate, and compare.

The multi profile architecture ensures that developers can run automated unit tests on a five second mini dataset (`dev` profile) without waiting for a million rows to generate, while the `competition` profile satisfies every scale requirement in the SRS. Locking train, validation, and test boundaries in `split_manifest.json` ensures zero future data leakage, and providing an unseen evaluation slice of over one hundred cases in month twelve directly satisfies the SRS comparative evaluation requirement.

## GitHub Evidence and Team Commit Strategy

To maintain complete transparency and provide auditable evidence of collaborative engineering without bloating version control:

1. **What Is Committed to Git**:
   - Generator source code in `packages/common/generator/`
   - Configuration profiles in `config/generator/`
   - Data dictionary document in `docs/data-dictionary.md`
   - Split manifest specification and sample generation manifest
   - Automated generator test suite in `tests/unit/test_generator.py`
   - A committed mini seed dataset in `tests/data/sample_dataset/` containing exactly 100 rows per table, allowing CI test runs without generating bulk data.

2. **What Is Excluded from Git**:
   - Full scale generated files in `data/snapshots/*`
   - Computed analytical marts in `data/marts/*`
   - Serialized model weights in `data/artifacts/*`
   - Pre commit hooks enforce `--maxkb=1000` to prevent accidental commits of multi megabyte CSV or Parquet files.

3. **Team Participation and Meaningful Commits**:
   - The dataset generation module is cleanly partitioned to support independent contributions from team members:
     - Member A: Configuration schemas, CLI interface, and master seed derivation (`config.py`, `cli.py`)
     - Member B: Master dimensions generation (`customers.py`, `restaurants.py`, `catalogs.py`)
     - Member C: Transactional engine and line item metric math (`transactions.py`)
     - Member D: Feedback, inventory, and wastage generation (`feedback.py`, `operations.py`)
     - Member E: Manifest generation, split locking, and unit tests (`manifest.py`, `test_generator.py`)

## Open Decisions and Risk Assessment

1. **Workstation RAM Limits**:
   - *Risk*: Generating one million order lines in memory simultaneously could cause memory exhaustion on laptops with 8GB RAM.
   - *Mitigation*: The generator will stream order item records in batches of 50,000 rows, writing directly to appendable Parquet row groups rather than holding all one million records in memory.
2. **File Generation Duration**:
   - *Risk*: Generating one million rows sequentially in Python could take several minutes.
   - *Mitigation*: Vectorized NumPy operations and batch generation loops will be used, targeting a completion time under 90 seconds for the full one million row dataset on standard developer hardware.

## References

**Project sources**:
- `AGENTS.md` (dual pipeline independence and Parquet mart rules)
- `docs/specs/0001-stack-and-architecture/index.md` (foundation architecture specification)
- `docs/specs/0002-data-model-and-schema/index.md` (eleven core tables and metric formulas)
- DineIQ Analytics SRS v1.0 (dataset minimums, realistic complexity patterns, and evaluation rules)

**Practices and standards**:
- Fixed seed pseudo random generation for reproducible science
- Zipf power law and Pareto distributions for commercial retail modeling
- Slowly Changing Dimensions Type 2 for historical price tracking
- Chronological time series partitioning to eliminate future data leakage
