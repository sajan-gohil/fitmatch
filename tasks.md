# FitMatch AI-Agent-Executable Tasks

Derived from `BUILD_PLAN.txt`.

This list includes tasks an AI agent can execute end-to-end inside the product/codebase without requiring human approvals, external relationship management, or manual business operations.

## Foundation & Architecture
- [ ] Phase 1: Create initial project structure for frontend (`Next.js 14`) and backend (`FastAPI`).
- [ ] Phase 1: Define PostgreSQL schema for users, resumes, jobs, matches, notifications, watchlists, and applications.
- [ ] Phase 1: Add `pgvector` support and migration scripts for embedding storage.
- [ ] Phase 1: Define Redis key strategy for caching, freshness, and rate limiting.
- [ ] Phase 1: Implement environment configuration templates for API keys/services, including `OPENAI_API_KEY`.

## Auth, Profiles, and Onboarding
- [ ] Phase 1: Implement Supabase auth integration (magic link + OAuth wiring in app code).
- [ ] Phase 1: Build onboarding flow for resume upload, target roles, locations, and work preference selection.
- [ ] Phase 1: Implement free-tier onboarding limits (e.g., location constraints and resume count checks).
- [ ] Phase 1: Build first-match response flow targeting fast initial results after onboarding completion.

## Resume Intake & Intelligence
- [ ] Phase 1: Implement PDF/DOCX upload handling and secure storage integration.
- [ ] Phase 1: Build resume parser pipeline using OpenAI API (`gpt-4o-mini`) to extract contact info, experience, education, skills, certifications, and inferred seniority/domain.
- [ ] Phase 1: Normalize extracted resume entities into structured DB models.
- [ ] Phase 1: Implement resume versioning limits by plan tier.
- [ ] Phase 2: Build paid resume scoring engine (clarity, quantification, keyword density, narrative, skills coverage) with OpenAI API-assisted evaluation where needed.
- [ ] Phase 2: Build AI rewrite suggestions for weak bullets using STAR-style outputs generated via OpenAI API.

## Job Data Pipeline (Scrape → Parse → Normalize → Store)
- [ ] Phase 1: Build company seed ingestion pipeline and storage model.
- [ ] Phase 1: Implement scheduled crawler orchestration by company priority tier.
- [ ] Phase 1: Implement ATS detection layer (Greenhouse, Lever, Workday, iCIMS, SmartRecruiters, BambooHR, Ashby).
- [ ] Phase 1: Build ATS-specific parsers for required job fields (title, description, location, salary, posted date, apply URL).
- [ ] Phase 1: Add static-page scraper path (HTTP + parser) and JS-rendered path (Playwright).
- [ ] Phase 1: Implement deduplication via deterministic job hash strategy.
- [ ] Phase 1: Implement title/location/seniority normalization tables and transforms.
- [ ] Phase 1: Persist raw snapshots and structured job records.
- [ ] Phase 2: Add supplementary source connectors where API access is available (Remotive, The Muse, USAJobs, Arbeitnow).

## Embeddings & Matching Engine
- [ ] Phase 1: Implement resume chunking and embedding generation pipeline via OpenAI API (`text-embedding-3-small`).
- [ ] Phase 1: Implement job embedding generation at ingestion time via OpenAI API (`text-embedding-3-small`).
- [ ] Phase 1: Store vectors in `pgvector` and add similarity-search indexes.
- [ ] Phase 1: Build weighted match scoring (title/skills/experience/education) and deterministic score calculation.
- [ ] Phase 1: Implement locality hard filter before semantic scoring.
- [ ] Phase 1: Normalize and return ranked top-N match results with 0–100 score output.
- [ ] Phase 1: Implement title/seniority taxonomy mapping (Intern → Staff+).

## Gap Analysis & Explainability (Paid)
- [ ] Phase 1: Build job-vs-resume skill delta detector with skill categorization.
- [ ] Phase 1: Generate fit narrative explaining strengths and missing skills via OpenAI API (`gpt-4o-mini`).
- [ ] Phase 1: Generate actionable resume-improvement suggestions per matched role via OpenAI API.
- [ ] Phase 1: Gate full analysis behind paid plan while preserving free preview behavior.

## Notifications & Personalization
- [ ] Phase 1: Implement digest scheduler for free users and baseline notification jobs.
- [ ] Phase 2: Implement trigger engine for high-match, company-watch, salary-threshold, deadline, resume-freshness, and skill-gap signals.
- [ ] Phase 2: Build notification preference model (trigger/channel/time-window/min-score).
- [ ] Phase 2: Implement email notification channel and templated delivery flow.
- [ ] Phase 2: Implement in-app/web push notification flow.
- [ ] Phase 2: Implement optional SMS channel integration hooks.
- [ ] Phase 2: Build real-time alert delivery path for paid users.

## Monetization & Access Control
- [ ] Phase 1: Implement plan model (Free / Pro / Lifetime) and feature flags.
- [ ] Phase 1: Integrate Stripe checkout and subscription lifecycle webhooks.
- [ ] Phase 1: Enforce tier-based limits across matching, resume analysis, alerts, and filters.
- [ ] Phase 1: Build pricing comparison UI and paywall prompts at conversion points.

## Affiliate Course Recommendation Layer
- [ ] Phase 2: Build skill-gap-to-course recommendation pipeline.
- [ ] Phase 2: Integrate course catalog ingestion (where APIs are available).
- [ ] Phase 2: Implement catalog caching and refresh jobs.
- [ ] Phase 2: Add contextual course card placement in gap analysis and resume score surfaces.
- [ ] Phase 2: Track affiliate click events and conversion funnel metrics.

## Product Features in Growth/Scale Roadmap
- [ ] Phase 2: Build company watchlist feature and related notifications.
- [ ] Phase 2: Build application tracker (status, notes, follow-ups).
- [ ] Phase 3: Build salary benchmarking from aggregated scraped data.
- [ ] Phase 3: Build referral logic (reward tracking and eligibility rules).
- [ ] Phase 3: Build API-access gating for eligible tier users.

## Marketing/SEO Tasks AI Can Fully Automate In-Product
- [ ] Phase 2: Generate programmatic SEO pages from job data templates (role/city/company/skill variants).
- [ ] Phase 1: Build landing page sections and copy variants from approved messaging.
- [ ] Phase 1: Auto-generate FAQ drafts from known objections and product capabilities.
- [ ] Phase 2: Generate ongoing data-driven content drafts from internal analytics datasets.

## Analytics, Monitoring, and Reliability
- [ ] Phase 1: Implement KPI event tracking (activation, conversion, match quality, CTR, churn proxies, freshness, latency).
- [ ] Phase 2: Build internal dashboards for core funnel and operational metrics.
- [ ] Phase 1: Add structured error logging and monitoring hooks.
- [ ] Phase 2: Add alerting for scraper failures, stale job data, and notification failures.

## Security, Privacy, and Compliance Implementation
- [ ] Phase 1: Implement encrypted resume storage/access patterns.
- [ ] Phase 1: Implement user-initiated resume deletion workflows.
- [ ] Phase 1: Build privacy-safe data handling defaults in parser and analytics flows.
- [ ] Phase 1: Add rate limiting and abuse-protection middleware.

## QA, Testing, and Release Automation
- [ ] Phase 1: Write unit tests for parsing, normalization, matching, and gating logic.
- [ ] Phase 1: Write integration tests for scraper-to-storage and match retrieval pipelines.
- [ ] Phase 1: Add regression tests for paid/free feature boundaries.
- [ ] Phase 1: Add CI workflows for tests, linting, and migration validation.
- [ ] Phase 1: Add deployment automation for frontend, API, and worker processes.
