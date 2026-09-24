# Epic: Application

Cross cutting application features: authentication, access control, reporting, exports, operational infrastructure.

---

## Slice 6: Application infrastructure

### 26. Authentication and role based access · needs a decision · GA

User authentication and role based permissions. The SRS requires authentication and role based access but does not prescribe specific roles or auth providers. Heavy Spark processing must run asynchronously. Interactive API requests should serve published/precomputed analytical outputs rather than scanning the complete order line dataset.

**Done when:** users can register, log in, and log out; role based permissions gate access to dashboards and features; API endpoints enforce access control; sessions are managed securely; the auth system integrates with the async job architecture.

- [ ] Design it (spec): `/architect authentication and role based access`

### 27. Report generation and data export

Generate downloadable reports from dashboard views. Support CSV and Excel compatible exports. Reports should capture the current filtered view with metadata (date range, filters applied, generation timestamp).

**Done when:** users can export any dashboard view as CSV or Excel compatible format; reports include metadata; export handles large datasets without blocking the UI; generated reports are logged in the audit trail.

- [ ] `/develop report generation and data export`

### 28. Job status, audit trail, and model versioning · needs a decision

Async job management: track Spark job status (queued, running, completed, failed) with progress indicators. Audit trail: log user actions, data access, report generation, and model runs. Model version tracking: record which model version produced each prediction, its training data window, and evaluation metrics.

**Done when:** job status is visible in the UI with progress and error reporting; audit trail logs are queryable; model versions are tracked with training window and metrics; users can see which model version is behind any prediction; error handling surfaces meaningful messages.

- [ ] Design it (spec): `/architect job status, audit trail, and model versioning`
