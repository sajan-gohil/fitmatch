# FitMatch AI-Agent-Executable Tasks

Derived from `BUILD_PLAN.txt`.

This list includes tasks an AI agent can execute end-to-end inside the product/codebase without requiring human approvals, external relationship management, or manual business operations.

## Development Phases (AI-Executable Implementation Tasks)
- [ ] Phase 1: Build core FitMatch product end-to-end.
  - Scope includes platform foundation (`Next.js 14` + `FastAPI`), PostgreSQL schema + `pgvector` migrations, Redis strategy, and env templates (including `OPENAI_API_KEY`).
  - Scope includes auth/onboarding via Supabase (magic link + OAuth), free-tier enforcement, and first-match response flow.
  - Scope includes secure resume ingest and OpenAI parsing via `gpt-4o-mini`, with normalized entity persistence and plan-based resume versioning.
  - Scope includes job ingestion (ATS/static/Playwright), normalization, deduplication, raw + structured persistence, and optional API-source connectors.
  - Scope includes OpenAI embeddings via `text-embedding-3-small`, `pgvector` indexing, locality filtering, taxonomy mapping, and deterministic weighted matching (0–100 ranked outputs).
  - Scope includes paid intelligence + monetization (OpenAI-assisted scoring, gap analysis, narratives, rewrites, Free/Pro/Lifetime model, Stripe checkout/webhooks, feature gating, pricing/paywall UX).
- [ ] Phase 2: Build scale, retention, and operations layer.
  - Scope includes notifications (preferences, triggers, email/in-app/push/SMS hooks, free digests, paid real-time alerts), company watchlists, and application tracking.
  - Scope includes affiliate recommendation flow (catalog ingest/cache/contextual cards/click tracking), salary benchmarking, referral rules, and API-access gating for eligible tiers.
  - Scope includes growth automation (programmatic SEO plus landing/FAQ/content generation from internal product data).
  - Scope includes production hardening: KPI tracking, dashboards, operational alerts, encrypted storage, deletion workflows, privacy-safe defaults, abuse rate limiting, and full QA/CI/CD automation (unit/integration/regression tests, lint/test/migration checks, deployment pipelines).
