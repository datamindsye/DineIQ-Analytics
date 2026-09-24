# 0001. Architecture and Technology Stack (Rationale)

## Context

The DineIQ Analytics platform is built for a competitive data science and software engineering challenge. The application must ingest, clean, analyze, and model complex multi table restaurant operational data across 11 relational entities. The dataset scale encompasses up to one million order item lines, one hundred thousand orders, fifty thousand customers, and extensive operational records for inventory, ratings, and wastage over twelve months of historical data.

The project demands both big data processing capabilities (Apache Spark, PySpark, Spark SQL, Spark MLlib) and classical Python data science modeling (Pandas, NumPy, scikit-learn). A core requirement is establishing genuine scientific comparison between these two analytical paradigms without cross contamination. The platform must also deliver responsive interactive dashboards, evidence based business recommendations, scenario simulation tools, and role based security.

Because the system is developed by a team of student engineers and evaluated directly by competition judges, the architecture must balance high analytical throughput with operational simplicity. Introducing complex distributed infrastructure like Kubernetes, Kafka, or distributed workflow engines introduces severe operational risk and high cognitive burden. The architecture must enable complete local execution, rapid debugging, transparent code inspection, and reproducible offline evaluation.

## Options considered

### Option 1: Modular Monolith with Dual Independent Pipelines, FastAPI, React, PostgreSQL, and Parquet (Approved)

A unified modular codebase where frontend, API backend, and data science pipelines reside in organized packages. PostgreSQL handles application metadata, users, job tracking, and model registries. Large scale analytical tables and generated feature marts are stored in compressed Parquet files. PySpark and Python pipelines run independently as background processes without blocking API threads.

**Pros**:
- Combines big data scale with zero cluster overhead by running local PySpark and embedded columnar queries.
- Clean physical separation of concerns without the distributed failure modes of microservices.
- Easily runnable and testable on a single developer workstation without cloud accounts or paid services.
- Delivers sub 50 millisecond dashboard response times by reading precomputed analytical marts.
- Fully adheres to the strict dual pipeline independence rule mandated by the competition requirements.

**Cons**:
- Running local PySpark requires installing a Java Runtime Environment on developer machines.
- Background jobs managed via database tables lack complex graphical DAG dependency visualization.

### Option 2: Distributed Microservices Architecture with Kafka, Redis, and Celery

Splits the system into five independent microservices (Auth Service, Ingestion Service, Spark Analytics Service, Python ML Service, and Dashboard Service) communicating through Apache Kafka event streams, Redis task brokers, and Celery workers.

**Pros**:
- Independent scaling of individual service workloads.
- Explicit service boundaries enforced by network isolation.

**Cons**:
- High operational overhead requiring multi container orchestration, network routing, and distributed tracing.
- Significant setup friction for student developers, increasing configuration failures during local development and judging.
- Unnecessary distributed transaction complexity for an analytical workload that operates naturally in scheduled or on demand batches.
- Violates the core architecture principle of avoiding unneeded distributed infrastructure.

### Option 3: Single Pipeline Monolith (Python and Pandas only, no Spark)

Discards Apache Spark entirely and executes all data cleaning, joins, and modeling exclusively through Python, Pandas, and scikit-learn in a single web application container.

**Pros**:
- Simplest possible technology stack with minimal dependencies and no Java runtime requirement.
- Fastest initial scaffolding speed.

**Cons**:
- Fails the fundamental competition requirement to evaluate PySpark, Spark SQL, and Spark MLlib against Python data science.
- Memory consumption spikes severely when performing multi table joins across one million order rows in pure Pandas.
- Eliminates the big data engineering evaluation criteria established in the project SRS.

### Option 4: Cloud Native Serverless Architecture (AWS Lambda, Glue, DynamoDB, S3)

Deploys the application using serverless cloud services, utilizing AWS Glue for Spark jobs, AWS Lambda for API routing, DynamoDB for metadata, and S3 for analytical data lakes.

**Pros**:
- Zero server maintenance and automatic elastic scaling.
- Native managed cloud services for Spark and serverless functions.

**Cons**:
- Introduces hard cloud lock in and recurring monthly cloud costs.
- Prevents offline evaluation and live judging in environments without internet access or active cloud credentials.
- Execution timeout limits on serverless functions interfere with long running Spark and training tasks.
- Significantly slows developer iteration cycles due to cloud deployment lag.

## Rationale

Option 1 is selected as the approved architecture because it directly satisfies all competition constraints, team realities, and technical requirements.

First, the modular monolith pattern provides clear architectural separation between frontend presentation, backend routing, core domain logic, and analytics pipelines without the operational tax of microservices. A student team can easily navigate the entire repository, run all unit and integration tests locally, and debug end to end workflows without configuring message buses, distributed service registries, or container orchestrators.

Second, the storage partition between PostgreSQL and Parquet aligns storage engines with workload characteristics. PostgreSQL excels at transactional integrity, ACID guarantees, relational indexing, and small mutable records (user credentials, RBAC roles, job statuses, audit trails, and recommendation states). Parquet excels at columnar compression, high throughput vector scans, and immutability for multi million row datasets. Reading precomputed Parquet marts via embedded columnar readers (PyArrow or DuckDB) completely isolates API response times from heavy pipeline execution.

Third, the dual pipeline design guarantees scientific validity. By sharing only the raw clean dataset snapshot, entity identifiers, chronological split manifest, and evaluation contract, neither pipeline can inadvertently leak feature engineering or predictive signals to the other. Judges can inspect both pipelines independently, verify identical split boundaries, and evaluate unbiased comparative metrics.

Fourth, avoiding external queue infrastructure like Redis, Celery, or Kafka keeps the platform self contained. A database backed job table in PostgreSQL (`job_runs`) reliably tracks asynchronous batch jobs with state, progress, and error logging, meeting all concurrency and asynchronous needs for this workload.

## References

### Project sources
- DineIQ Analytics Software Requirements Specification v1.0 (SRS document in workspace root)
- Scope index and epic specifications (`docs/scope/index.md`, `docs/scope/foundation.md`, `docs/scope/analytics.md`)
- Approved project lead architecture and technology guidelines

### Practices and standards
- Modular Monolith Architecture Pattern (clean domain and package boundaries within a unified repository)
- Separation of Storage (OLTP in PostgreSQL, OLAP and feature marts in Apache Parquet)
- Asynchronous Background Execution (heavy analytical tasks run outside HTTP request lifecycles)
- Time Aware Machine Learning (chronological dataset splitting without future data leakage)
- Evaluation Contract Pattern (formal mathematical interfaces for comparing independent predictive models)
