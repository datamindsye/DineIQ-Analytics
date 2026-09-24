# Epic: Competition

Deliverables required by the data science competition. These are built last because they summarize the work done in all other epics.

---

## Slice 7: Competition deliverables

### 29. Competition deliverables · needs a decision

All artifacts required for competition submission. These are not application features but project level deliverables that document, present, and package the work.

Required deliverables:
- Public GitHub repository with meaningful commits from all team members
- Development log
- Dataset generation script (built in feature 5)
- Data dictionary
- Spark jobs, Spark SQL queries, and Parquet outputs
- Spark MLlib models with evaluation
- Independent Python models with evaluation
- Dual pipeline comparison report (at least 100 unseen cases)
- Reports (analytical outputs, visualizations)
- Tests
- Installation and execution documentation (README with setup, run, and test instructions)
- Demo video
- Technical blog post
- Project presentation
- AI_USAGE.md (documenting AI tool usage during development)
- Team contribution record

Robustness to hidden/unseen data cases:
- missing values
- duplicate orders
- unknown menu items
- new locations
- price changes
- unusual promotions
- extreme wastage
- seasonal changes
- unusual customer behavior
- outliers

**Done when:** all 16 deliverables are complete and accessible in the repository; the system handles all 10 hidden data edge cases without crashing or producing fabricated results; README allows a judge to clone, install, and run the full system; demo video walks through the core flow; blog post explains the technical approach; presentation is ready for delivery.

- [ ] Design it (spec): `/architect competition deliverables`

---

## Explicit out of scope

The following are not part of this build pass:

- Real time streaming analytics (batch processing only)
- Mobile native application (responsive web only)
- Multi tenant SaaS (single organization deployment)
- Third party POS system integration (generated data only)
- Payment processing
- Email/SMS notification system
- Multi language internationalization
- Production cloud deployment and DevOps (local development and demo only)
- Customer facing self service portal
- Advanced NLP on review text (beyond rating anomaly detection)

---

## Non functional requirements

These apply across all features:

- **Performance**: interactive API requests serve precomputed outputs, not raw dataset scans; heavy Spark processing runs asynchronously
- **Responsive UI**: web application adapts to desktop and tablet screen sizes
- **Error handling**: meaningful error messages; no silent failures; graceful handling of unexpected data
- **Search and filtering**: all list views support search and filtering
- **Data integrity**: no fabricated metrics or analytical conclusions; all outputs traceable to source data
- **Reproducibility**: dataset generation is seeded and reproducible; model training is logged with parameters

---

## Acceptance criteria (project level)

1. All 11 source tables are generated at the specified minimum scale
2. Data quality pipeline detects and handles all 17 complexity patterns
3. Both Spark and Python pipelines run independently from the same clean snapshot
4. Dual pipeline comparison covers at least 100 unseen cases with all 7 required columns
5. Spark evaluates at least three MLlib candidate algorithms
6. All 6 major dashboards render with real analytics data
7. Recommendations follow the Observation → Evidence → Interpretation → Recommendation → Priority flow
8. What if scenarios produce clearly labeled estimates for the applicable metrics
9. No future data leakage in time dependent models
10. The system handles all 10 hidden data edge cases without crashing
11. All 16 competition deliverables are complete
12. Authentication and role based access control works
13. CSV/Excel export works from any dashboard view

---

## Major dependencies

| Dependency | Depends on | Notes |
|---|---|---|
| All analytics (features 7 to 22, 30) | Data model (3) and dataset generation (5) | Cannot compute analytics without data |
| Spark pipeline (8) | Stack and architecture (1) | Spark environment must be configured |
| Python pipeline (9) | Stack and architecture (1) | Python data science environment must be configured |
| Comparison framework (10) | Both pipelines (8, 9) | Needs outputs from both to compare |
| All dashboards (11, 14, 17, 18, 25) | Design system (4) and their respective analytics features | Cannot render without data and UI components |
| Recommendations (23) | Analytics features (7 to 22) | Needs analytical outputs as evidence |
| What if (24) | Recommendations (23) and forecasting (16) | Builds on the prediction and analytics layer |
| Competition deliverables (29) | All other features | Summarizes and packages the complete project |

---

## Risks and assumptions

| Risk or assumption | Type | Mitigation |
|---|---|---|
| Spark local mode may not handle 1M records performantly on a development machine | Risk | Test with a smaller sample first; optimize partitioning; profile before scaling |
| Dual pipeline comparison requires both pipelines to define the same target variable and evaluation contract | Assumption | Spec this explicitly in the comparison framework (feature 10) |
| The "next week wastage risk" task assumes weekly aggregation is meaningful for all locations | Assumption | Validate during data exploration; adjust granularity if needed |
| Team members may have different local environments (Java/Spark versions, Python versions) | Risk | Document exact versions in README; consider containerization in the stack spec |
| Generated data realism depends on domain knowledge of restaurant operations | Risk | Review generated data patterns with the team before building analytics on top |
| Some analytical areas may overlap (e.g. churn risk appears in both customer and operational analytics) | Assumption | The scope treats them as shared computations surfaced in multiple views, not duplicated |
| Competition judges may test with unseen data that differs from the generated patterns | Risk | Build robust error handling and validation; do not hard code thresholds |
