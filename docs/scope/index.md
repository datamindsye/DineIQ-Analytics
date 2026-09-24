# Scope: DineIQ Analytics — Data Science Intelligence Arena

A complete restaurant analytics and intelligence platform that takes raw restaurant data through data quality, cleaning, feature engineering, dual pipeline analytics (Apache Spark and independent Python), machine learning, comparison, business intelligence, evidence based recommendations, what if analysis, and interactive dashboards. Built for a data science competition with a team.

**Build approach:** Tracer Bullet (prove the whole pipe works before building any part fully; each slice is a working thread through every layer from data to dashboard).
**Workflow:** GA (after /develop: /check verify, /test, /check review, /document). The project default for a competition where tests, docs, and quality are judged. `/architect` first for any feature with a real decision; skippable when the build is already clear.

_These are recommendations to keep your build orderly, not requirements. Skip anything that does not fit: if you already know how to build a feature, use `/develop` and skip `/architect`. You decide when a feature is `done`._

## At a glance

| # | Feature | Phase | Status |
|---|---------|-------|--------|
| 1 | Stack and architecture | Foundation | done |
| 2 | Coding standards and tooling | Foundation | done |
| 3 | Data model and schema | Foundation | in-progress |
| 4 | Design system and UI foundation | Foundation | planned |
| 5 | Dataset generation script | Data | in-progress |
| 6 | Data quality and cleaning pipeline | Data | planned |
| 7 | Menu profitability and classification analytics | Slice 1 | planned |
| 8 | Spark menu analytics pipeline | Slice 1 | planned |
| 9 | Python menu analytics pipeline | Slice 1 | planned |
| 10 | Dual pipeline comparison framework | Slice 1 | planned |
| 11 | Menu Intelligence Dashboard | Slice 1 | planned |
| 12 | Customer segmentation and RFM analytics | Slice 2 | planned |
| 13 | Market basket analysis | Slice 2 | planned |
| 14 | Customer Intelligence Dashboard | Slice 2 | planned |
| 15 | Wastage analysis and prediction | Slice 3 | planned |
| 16 | Demand forecasting | Slice 3 | planned |
| 17 | Wastage and Forecast Dashboards | Slice 3 | planned |
| 18 | Dual Pipeline Comparison Dashboard | Slice 3 | planned |
| 19 | Pricing and promotion analytics | Slice 4 | planned |
| 20 | Anomaly detection (ratings, sales, promotions) | Slice 4 | planned |
| 21 | Location and channel analytics | Slice 4 | planned |
| 22 | Inventory intelligence | Slice 4 | planned |
| 23 | Evidence based recommendation engine | Slice 5 | planned |
| 24 | What if scenario analysis | Slice 5 | planned |
| 25 | Executive Dashboard | Slice 5 | planned |
| 26 | Authentication and role based access | Slice 6 | planned |
| 27 | Report generation and data export | Slice 6 | planned |
| 28 | Job status, audit trail, and model versioning | Slice 6 | planned |
| 29 | Competition deliverables | Slice 7 | planned |
| 30 | Slow moving dish and churn risk analytics | Slice 4 | planned |

## Epics

| Epic | File | Features | Status |
|------|------|----------|--------|
| Foundation | [foundation.md](foundation.md) | 1 to 4 | planned |
| Data | [data.md](data.md) | 5 to 6 | planned |
| Analytics and ML | [analytics.md](analytics.md) | 7 to 10, 12 to 13, 15 to 16, 19 to 22, 30 | planned |
| Dashboards | [dashboards.md](dashboards.md) | 11, 14, 17 to 18, 25 | planned |
| Recommendations and What If | [recommendations.md](recommendations.md) | 23 to 24 | planned |
| Application | [application.md](application.md) | 26 to 28 | planned |
| Competition | [competition.md](competition.md) | 29 | planned |

## Legend

**The decision box.** Every feature carries exactly one, the sub-task whose label ends with `(spec)`. Its wording varies (`Design it (spec)` normally, `Decide the stack (spec)` on Stack and architecture), so skills locate it by that `(spec)` suffix, never by an exact label. Every other box is an execution box and `/architect` never ticks one.

**Feature lifecycle**: the scope updates as a feature moves; each row is what it shows and who sets it:

| State | Set by | The feature shows |
|---|---|---|
| `planned` · needs a decision | `/scope` | one box: `Design it (spec): /architect <feature>` |
| `in-progress` (designed) | **`/architect` at spec capture** | `Design it` ticked; spec linked; `Build it: /develop <feature>` + **2 to 5 milestones**; the tier's closing boxes (`Verify it`, `Test it`, `Review it`, `Document it` at GA) |
| `in-progress` (building) | `/develop` | milestone sub-boxes tick one by one; code pointer filled |
| `in-progress` (verified) | `/check verify` | `Build it` + milestones ticked; `Verify it` ticked |
| `done` | **you, when you decide it is** | boxes you ran ticked, skipped ones marked skipped |

- **Next step** = the first unticked box (always a command or a tracked milestone).
- **needs a decision** = run `/architect` first; otherwise straight to `/develop` (or `/audit` for standards and tooling). The tag drops once the spec is captured.
- **Atomic build tasks live in the spec's `## Build plan`, not here**: the scope carries only the milestone rollup.
- **Status** `planned` → `in-progress` → `done`, plus `existing` (pre-workflow) and `dropped` (de-scoped, kept for history).
- **Approach tag** beside a heading (e.g. `· Facade`) overrides the project default for that feature; no tag = inherits it.
- **Workflow tier tag** beside a heading (e.g. `· GA`, `· Prototype`) sets that one feature's rigor above or below the project default; no tag inherits the default.

## References

### Project sources
- DineIQ Analytics SRS v1.0 (Software Requirements Specification PDF in the repository root)
- Project lead's approved architecture and workflow plan (provided in the scope request)

### Practices and standards
- Tracer Bullet (basis: dual pipelines and multi layer architecture; the highest risk is layers not connecting, so a thin working thread through every layer retires that risk first)
- GA workflow (basis: competition requires tests, documentation, meaningful commits, and code review quality)
- Foundations first (basis: data model is the costliest thing to redo; stack and tooling before features)
- Time aware modeling (basis: SRS requirement to prohibit future data leakage in forecasting and time dependent models)
- Dual pipeline independence (basis: SRS requirement that Spark and Python pipelines share only raw data, entity IDs, target definition, chronological split manifest, and evaluation contract)
