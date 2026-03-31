# FitMatch AI-Agent-Executable Tasks

Derived from `BUILD_PLAN.txt`.

This list includes tasks an AI agent can execute end-to-end inside the product/codebase without requiring human approvals, external relationship management, or manual business operations.

## Development Phases (AI-Executable Implementation Tasks)
- [ ] Phase 1: Build core FitMatch product end-to-end.
  - [ ] Subtask: Scaffold `Next.js 14` + `FastAPI`, define PostgreSQL schema + `pgvector` migrations, set Redis strategy, and wire env templates (including `OPENAI_API_KEY`).
  - [ ] Subtask: Integrate Supabase auth (magic link + OAuth), implement onboarding capture, enforce free-tier limits, and return first-match response.
  - [ ] Subtask: Implement secure resume ingest and OpenAI parsing via `gpt-4o-mini`, then persist normalized resume entities with plan-based versioning.
  - [ ] Subtask: Implement job ingestion (ATS/static/Playwright), normalization + deterministic deduplication, and raw + structured persistence with optional API-source connectors.
  - [ ] Subtask: Generate embeddings via OpenAI `text-embedding-3-small`, store/index vectors in `pgvector`, apply locality filters, and return deterministic weighted 0–100 ranked matches.
  - [ ] Subtask: Deliver paid intelligence + monetization (OpenAI-assisted scoring, gap analysis, narratives/rewrites, Free/Pro/Lifetime tiers, Stripe checkout/webhooks, feature gating, paywall UX).
- [ ] Phase 2: Build scale, retention, and operations layer.
  - [ ] Subtask: Implement notifications (preferences/triggers/channels), company watchlists, and application tracking with free digests + paid real-time alerts.
  - [ ] Subtask: Implement affiliate recommendation flow (catalog ingest/cache/contextual cards/click tracking), salary benchmarking, referral rules, and API-access gating by tier.
  - [ ] Subtask: Implement growth automation through programmatic SEO and auto-generated landing/FAQ/content from internal product data.
  - [ ] Subtask: Harden production with KPI dashboards + operational alerts, encrypted storage + deletion workflows + privacy-safe defaults + abuse rate limits, and full QA/CI/CD automation.
