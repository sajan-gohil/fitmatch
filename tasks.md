# FitMatch AI-Agent-Executable Tasks

Derived from `BUILD_PLAN.txt`.

This list includes tasks an AI agent can execute end-to-end inside the product/codebase without requiring human approvals, external relationship management, or manual business operations.

## Foundation & Architecture
- [ ] Create initial project structure for frontend (`Next.js 14`) and backend (`FastAPI`).
- [ ] Define PostgreSQL schema for users, resumes, jobs, matches, notifications, watchlists, and applications.
- [ ] Add `pgvector` support and migration scripts for embedding storage.
- [ ] Define Redis key strategy for caching, freshness, and rate limiting.
- [ ] Implement environment configuration templates for API keys/services.

## Auth, Profiles, and Onboarding
- [ ] Implement Supabase auth integration (magic link + OAuth wiring in app code).
- [ ] Build onboarding flow: resume upload, target roles, locations, work preference.
- [ ] Implement free-tier limits in onboarding (e.g., location constraints).
- [ ] Build first-match response flow targeting fast initial results.

## Resume Intake & Intelligence
- [ ] Implement PDF/DOCX upload handling and secure storage integration.
- [ ] Build resume parser pipeline to extract contact info, experience, education, skills, certifications, and inferred seniority/domain.
- [ ] Normalize extracted resume entities into structured DB models.
- [ ] Implement resume versioning limits by plan tier.
- [ ] Build paid resume scoring engine (clarity, quantification, keyword density, narrative, skills coverage).
- [ ] Build AI rewrite suggestions for weak bullets using STAR-style outputs.

## Job Data Pipeline (Scrape → Parse → Normalize → Store)
- [ ] Build company seed ingestion pipeline and storage model.
- [ ] Implement scheduled crawler orchestration by company priority tier.
- [ ] Implement ATS detection layer (Greenhouse, Lever, Workday, iCIMS, SmartRecruiters, BambooHR, Ashby).
- [ ] Build ATS-specific parsers for required job fields.
- [ ] Add static-page scraper path (HTTP + parser) and JS-rendered path (Playwright).
- [ ] Implement deduplication via deterministic job hash strategy.
- [ ] Implement title/location/seniority normalization tables and transforms.
- [ ] Persist raw snapshots and structured job records.
- [ ] Add supplementary source connectors where API access is available (Remotive, The Muse, USAJobs, Arbeitnow).

## Embeddings & Matching Engine
- [ ] Implement resume chunking and embedding generation pipeline.
- [ ] Implement job embedding generation at ingestion time.
- [ ] Store vectors in `pgvector` and index for similarity search.
- [ ] Build weighted match scoring (title/skills/experience/education).
- [ ] Implement locality hard filter before semantic scoring.
- [ ] Normalize and return ranked top-N match results with 0–100 score output.
- [ ] Implement title/seniority taxonomy mapping (Intern → Staff+).

## Gap Analysis & Explainability (Paid)
- [ ] Build job-vs-resume skill delta detector with skill categorization.
- [ ] Generate fit narrative explaining strengths and missing skills.
- [ ] Generate actionable resume-improvement suggestions per matched role.
- [ ] Gate full analysis behind paid plan while preserving free preview behavior.

## Notifications & Personalization
- [ ] Implement trigger engine for high-match, company-watch, salary-threshold, deadline, resume-freshness, and skill-gap signals.
- [ ] Build notification preference model (trigger/channel/time-window/min-score).
- [ ] Implement email notification channel and templated delivery flow.
- [ ] Implement in-app/web push notification flow.
- [ ] Implement optional SMS channel integration hooks.
- [ ] Build digest scheduler for free users and real-time alert path for paid users.

## Monetization & Access Control
- [ ] Implement plan model (Free / Pro / Lifetime) and feature flags.
- [ ] Integrate Stripe checkout and subscription lifecycle webhooks.
- [ ] Enforce tier-based limits across matching, resume analysis, alerts, and filters.
- [ ] Build pricing comparison UI and paywall prompts at conversion points.

## Affiliate Course Recommendation Layer
- [ ] Build skill-gap-to-course recommendation pipeline.
- [ ] Integrate course catalog ingestion (where APIs are available).
- [ ] Implement catalog caching and refresh jobs.
- [ ] Add contextual course card placement in gap analysis and resume score surfaces.
- [ ] Track affiliate click events and conversion funnel metrics.

## Product Features in Growth/Scale Roadmap
- [ ] Build company watchlist feature and related notifications.
- [ ] Build application tracker (status, notes, follow-ups).
- [ ] Build salary benchmarking from aggregated scraped data.
- [ ] Build referral logic (reward tracking and eligibility rules).
- [ ] Build API-access gating for eligible tier users.

## Marketing/SEO Tasks AI Can Fully Automate In-Product
- [ ] Generate programmatic SEO pages from job data templates (role/city/company/skill variants).
- [ ] Build landing page sections and copy variants from approved messaging.
- [ ] Auto-generate FAQ drafts from known objections and product capabilities.
- [ ] Generate ongoing data-driven content drafts from internal analytics datasets.

## Analytics, Monitoring, and Reliability
- [ ] Implement KPI event tracking (activation, conversion, match quality, CTR, churn proxies, freshness, latency).
- [ ] Build internal dashboards for core funnel and operational metrics.
- [ ] Add structured error logging and monitoring hooks.
- [ ] Add alerting for scraper failures, stale job data, and notification failures.

## Security, Privacy, and Compliance Implementation
- [ ] Implement encrypted resume storage/access patterns.
- [ ] Implement user-initiated resume deletion workflows.
- [ ] Build privacy-safe data handling defaults in parser and analytics flows.
- [ ] Add rate limiting and abuse-protection middleware.

## QA, Testing, and Release Automation
- [ ] Write unit tests for parsing, normalization, matching, and gating logic.
- [ ] Write integration tests for scraper-to-storage and match retrieval pipelines.
- [ ] Add regression tests for paid/free feature boundaries.
- [ ] Add CI workflows for tests, linting, and migration validation.
- [ ] Add deployment automation for frontend, API, and worker processes.
