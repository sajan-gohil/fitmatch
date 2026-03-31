# FitMatch AI-Agent Task Phases

This task list includes only implementation work that a coding agent can execute directly from the build plan, organized into iterative phases sized for focused delivery.

## Development Phases

- [x] **Phase 1 — Project foundation and local architecture**
  - [x] Initialize monorepo structure for `frontend` (Next.js) and `backend` (FastAPI).
  - [x] Add shared environment config templates (`.env.example`) and typed settings loaders.
  - [x] Set up PostgreSQL schema migrations for users, resumes, jobs, matches, notifications, subscriptions, and affiliate events.
  - [x] Add Redis wiring for queues/cache plus baseline background worker scaffold.
  - [x] Add basic observability hooks (structured logs + error reporting stubs) and health endpoints.

- [ ] **Phase 2 — Authentication, onboarding, and resume ingestion**
  - [ ] Implement Supabase auth flow (magic link + Google OAuth) with protected app routes.
  - [ ] Build onboarding form for target roles, preferred locations, and work type preferences.
  - [ ] Implement resume upload pipeline (PDF/DOCX) to storage with validation and size limits.
  - [ ] Implement LLM-based resume parser that stores normalized structured resume data.
  - [ ] Add onboarding completion state and first-run dashboard handoff.

- [ ] **Phase 3 — Job ingestion pipeline (MVP sources)**
  - [ ] Build Playwright/Scrapy ingestion framework with pluggable ATS adapters.
  - [ ] Implement adapters for Greenhouse, Lever, Workday, SmartRecruiters, and Ashby.
  - [ ] Normalize and deduplicate scraped jobs into canonical job tables.
  - [ ] Add scrape scheduling, retry/backoff, and dead-letter handling.
  - [ ] Persist raw snapshots/metadata needed for traceability and re-processing.

- [ ] **Phase 4 — Embeddings and semantic matching engine**
  - [ ] Add resume/job embedding generation pipeline and pgvector persistence.
  - [ ] Implement weighted scoring (title, skills, experience, education) with 0–100 normalization.
  - [ ] Enforce locality filtering before scoring and ranking.
  - [ ] Build match refresh jobs and incremental re-scoring logic.
  - [ ] Expose backend APIs for top-N ranked matches per user profile/resume.

- [ ] **Phase 5 — Core user-facing matching experience**
  - [ ] Build dashboard results UI showing ranked jobs and match percentages.
  - [ ] Implement free-tier constraints (e.g., capped matches/locations) in backend + UI.
  - [ ] Add job detail view with match explanation payload rendering.
  - [ ] Add role/location filters and saved search state.
  - [ ] Implement first-match experience target (return initial batch quickly after onboarding).

- [ ] **Phase 6 — Billing, tiers, and access control**
  - [ ] Integrate Stripe subscriptions + one-time purchase flows and webhook handling.
  - [ ] Implement plan entitlements (Free, Pro, Lifetime) in authorization middleware.
  - [ ] Add upgrade/paywall UX at premium feature boundaries.
  - [ ] Add billing portal/account management entry points.
  - [ ] Add server-side enforcement tests for tier-gated API endpoints.

- [ ] **Phase 7 — Gap analysis and resume intelligence (paid features)**
  - [ ] Implement skill-gap extraction between job requirements and parsed resume skills.
  - [ ] Generate structured fit reports with actionable suggestions per match.
  - [ ] Implement resume scoring across defined quality dimensions.
  - [ ] Add AI rewrite suggestions for weak bullets with accept/edit/dismiss state.
  - [ ] Add free preview vs full paid output gating logic.

- [ ] **Phase 8 — Notifications and personalization engine**
  - [ ] Implement notification rules engine (high-match, watchlist, salary threshold, freshness, deadlines).
  - [ ] Add user notification preferences model/API (channels, windows, threshold).
  - [ ] Build weekly digest job and transactional email templates.
  - [ ] Implement near-real-time alert dispatch via queue workers.
  - [ ] Add in-app notification feed and read/unread state.

- [ ] **Phase 9 — Affiliate course recommendation layer**
  - [ ] Build skill-to-course recommendation service and placement slots in fit/gap reports.
  - [ ] Implement provider adapter interface for external course catalogs.
  - [ ] Add scheduled catalog sync + caching with stale-data fallback.
  - [ ] Track impressions/clicks/conversions for affiliate analytics.
  - [ ] Add internal admin config for manual + AI-assisted skill-course mappings.

- [ ] **Phase 10 — Growth feature set and scale hardening**
  - [ ] Implement company watchlist and application tracker modules.
  - [ ] Add SEO programmatic landing page generation for role/location combinations.
  - [ ] Add scraper scaling controls for larger company coverage (rate limiting + partitioned queues).
  - [ ] Implement salary benchmarking from aggregated job data.
  - [ ] Add API access layer for Lifetime tier (token auth + quota limits).

- [ ] **Phase 11 — Advanced platform extensions**
  - [ ] Implement Slack alert integration for opted-in users.
  - [ ] Add referral tracking and reward-credit logic.
  - [ ] Implement PWA enhancements for mobile-first experience (installable + offline shell).
  - [ ] Add feature flags for staged rollouts of advanced modules.
  - [ ] Add performance and reliability improvements (query tuning, caching strategy updates, queue throughput tuning).
