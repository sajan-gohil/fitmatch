# FitMatch AI-Agent Task Phases

This task list includes only implementation work that a coding agent can execute directly from the build plan, organized into iterative phases sized for focused delivery.

## Development Phases

- [x] **Phase 1 — Project foundation and local architecture**
  - [x] Initialize monorepo structure for `frontend` (Next.js) and `backend` (FastAPI).
  - [x] Add shared environment config templates (`.env.example`) and typed settings loaders.
  - [x] Set up PostgreSQL schema migrations for users, resumes, jobs, matches, notifications, subscriptions, and affiliate events.
  - [x] Add Redis wiring for queues/cache plus baseline background worker scaffold.
  - [x] Add basic observability hooks (structured logs + error reporting stubs) and health endpoints.

- [x] **Phase 2 — Authentication, onboarding, and resume ingestion**
  - [x] Implement Supabase auth flow (magic link + Google OAuth) with protected app routes.
  - [x] Build onboarding form for target roles, preferred locations, and work type preferences.
  - [x] Implement resume upload pipeline (PDF/DOCX) to storage with validation and size limits.
  - [x] Implement LLM-based resume parser that stores normalized structured resume data.
  - [x] Add onboarding completion state and first-run dashboard handoff.

- [x] **Phase 3 — Job ingestion pipeline (MVP sources)**
  - [x] Build Playwright/Scrapy ingestion framework with pluggable ATS adapters.
  - [x] Implement adapters for Greenhouse, Lever, Workday, SmartRecruiters, and Ashby.
  - [x] Normalize and deduplicate scraped jobs into canonical job tables.
  - [x] Add scrape scheduling, retry/backoff, and dead-letter handling.
  - [x] Persist raw snapshots/metadata needed for traceability and re-processing.

- [x] **Phase 4 — Embeddings and semantic matching engine**
  - [x] Add resume/job embedding generation pipeline and pgvector persistence.
  - [x] Implement weighted scoring (title, skills, experience, education) with 0–100 normalization.
  - [x] Enforce locality filtering before scoring and ranking.
  - [x] Build match refresh jobs and incremental re-scoring logic.
  - [x] Expose backend APIs for top-N ranked matches per user profile/resume.

- [ ] **Phase 5 — Core user-facing matching experience**
  - [ ] Build dashboard results UI showing ranked jobs and match percentages.
  - [ ] Implement free-tier constraints (e.g., capped matches/locations) in backend + UI.
  - [ ] Add job detail view with match explanation payload rendering.
  - [ ] Add role/location filters and saved search state.
  - [ ] Implement first-match experience target (return initial batch quickly after onboarding).

- [x] **Phase 6 — Billing, tiers, and access control**
  - [x] Integrate Stripe subscriptions + one-time purchase flows and webhook handling.
  - [x] Implement plan entitlements (Free, Pro, Lifetime) in authorization middleware.
  - [x] Add upgrade/paywall UX at premium feature boundaries.
  - [x] Add billing portal/account management entry points.
  - [x] Add server-side enforcement tests for tier-gated API endpoints.

- [x] **Phase 7 — Gap analysis and resume intelligence (paid features)**
  - [x] Implement skill-gap extraction between job requirements and parsed resume skills.
  - [x] Generate structured fit reports with actionable suggestions per match.
  - [x] Implement resume scoring across defined quality dimensions.
  - [x] Add AI rewrite suggestions for weak bullets with accept/edit/dismiss state.
  - [x] Add free preview vs full paid output gating logic.

- [x] **Phase 8 — Notifications and personalization engine**
  - [x] Implement notification rules engine (high-match, watchlist, salary threshold, freshness, deadlines).
  - [x] Add user notification preferences model/API (channels, windows, threshold).
  - [x] Build weekly digest job and transactional email templates.
  - [x] Implement near-real-time alert dispatch via queue workers.
  - [x] Add in-app notification feed and read/unread state.

- [x] **Phase 9 — Affiliate course recommendation layer**
  - [x] Build skill-to-course recommendation service and placement slots in fit/gap reports.
  - [x] Implement provider adapter interface for external course catalogs.
  - [x] Add scheduled catalog sync + caching with stale-data fallback.
  - [x] Track impressions/clicks/conversions for affiliate analytics.
  - [x] Add internal admin config for manual + AI-assisted skill-course mappings.

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
