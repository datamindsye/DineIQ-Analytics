# Frontend Web Application

## Overview

React 19 and TypeScript frontend application scaffolded with Vite. It renders executive dashboards, pipeline comparison views, system health status, and Plotly interactive visualizations.

## Key files

| File | Owns |
|---|---|
| `src/App.tsx` | Client side routing and route definitions |
| `src/components/layout/AppLayout.tsx` | Main shell layout with Header and Sidebar |
| `src/components/charts/PlotlyChart.tsx` | Reusable Plotly chart wrapper with automatic resizing |
| `src/pages/DashboardPage.tsx` | Executive dashboard overview and sample menu matrix |
| `src/pages/PipelinesPage.tsx` | Dual pipeline architecture overview |
| `src/pages/HealthPage.tsx` | System and database health status monitor |
| `src/services/api.ts` | Typed API client for FastAPI backend communication |
| `src/types/index.ts` | TypeScript domain and response interfaces |

## Commands

```bash
# Start Vite development server
npm run dev

# Compile TypeScript and build production bundle
npm run build

# Run fast linter
npx oxlint
```

## Conventions

- Keep all business logic and data manipulation outside React components.
- Use typed interfaces in `src/types/` for all API responses and domain entities.
- Wrap all Plotly charts inside `PlotlyChart` to prevent memory leaks and handle responsive resizing.
- Use `import type` when importing TypeScript types under verbatim module syntax.
- Maintain the dark slate color palette and responsive layout defined in `src/index.css`.

## Gotchas

- Calling state setters synchronously inside `useEffect` triggers linter warnings; initialize state directly or guard with mounted flags.
- Plotly chart containers require a defined minimum height to avoid zero height rendering issues.

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
