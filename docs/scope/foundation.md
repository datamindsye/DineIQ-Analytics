# Epic: Foundation

Features that every later slice builds on. Nothing else starts until these are in place.

---

### 1. Stack and architecture

Decide the full technology stack (frontend framework, backend framework, database, Spark setup, Python environment, hosting) and scaffold a runnable project so every later slice builds on real structure. The SRS establishes Apache Spark, PySpark, Spark SQL, Spark MLlib for Pipeline 1 and Python, Pandas, NumPy, Scikit learn, XGBoost for Pipeline 2. The web framework, database, and deployment choices are open.

**Done when:** the stack is recorded in a spec and the empty scaffold boots locally, the dev server runs, and both Spark and Python environments are initialized.

- [x] Decide the stack (spec): [0001](../specs/0001-stack-and-architecture/index.md)
- [x] Scaffold from the decision: `/develop stack and architecture` (code in `apps/` and `packages/`)

---

### 2. Coding standards and tooling

Capture coding conventions from the real scaffolded project, then install lint, format, pre commit, and CI enforcement. This happens after the stack is scaffolded, not before.

**Done when:** root `AGENTS.md` reflects the real stack, and lint, format, type checking, and pre commit hooks run clean.

- [x] Capture conventions and tooling choices: `/audit`
- [x] Install the tooling: `/develop tooling`

---

### 3. Data model and schema

The core relational schema for all 11 required source tables: Customers, Orders, Order_Items, Menu_Items, Menu_Categories, Restaurants, Pricing_History, Promotions, Ratings, Inventory, Wastage. Defines entities, relationships, constraints, indexes, and the persistence shape (relational DB for the web app, Parquet for Spark and Python pipelines).

**Done when:** all 11 source tables are defined with proper relationships and constraints; the schema supports the required dataset scale (1M order lines, 100K orders, 50K customers, 150 menu items, 10 categories, 20 locations, 12 months history, 100K ratings, 50K wastage records); migration runs cleanly; Parquet export shape is defined.

- [x] Design it (spec): [0002](../specs/0002-data-model-and-schema/index.md)
- [ ] Build it: `/develop data model and schema`
  - [ ] Create Alembic migration for 11 core tables (AC-1, AC-7, AC-8, AC-9)
  - [ ] Implement SQLAlchemy 2.0 ORM models and constraints (AC-1, AC-4, AC-7)
  - [ ] Implement domain contracts and transaction metric validators (AC-2, AC-4)
  - [ ] Define snapshot manifest and Parquet schema contracts (AC-5, AC-6, AC-10)
  - [ ] Add unit and integration tests for schema constraints and math (AC-1, AC-2, AC-3, AC-8)
- [ ] Verify it: `/check verify data model and schema`
- [ ] Test it: `/test data model and schema`
- [ ] Review it (fresh model): `/check review data model and schema`
- [ ] Document it: `/document data model and schema`

---

### 4. Design system and UI foundation · needs a decision

Visual language, layout primitives, and base components so every dashboard and page feels cohesive. Includes typography, color system, spacing, chart component library, responsive grid, and accessibility baseline.

**Done when:** `design.md` covers type, color, spacing, chart styling, and layout components; base components handle focus, keyboard, and responsive breakpoints; a chart wrapper component renders one example chart.

- [ ] Design it (spec): `/architect design system and UI foundation`
