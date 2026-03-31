CREATE TABLE IF NOT EXISTS scrape_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    ats TEXT NOT NULL,
    status TEXT NOT NULL,
    jobs_found INTEGER NOT NULL DEFAULT 0,
    jobs_inserted INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS raw_job_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scrape_run_id UUID NOT NULL REFERENCES scrape_runs(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    ats TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS dead_letter_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    ats TEXT NOT NULL,
    payload JSONB NOT NULL,
    error_message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_phase3_dedup
    ON jobs (lower(company_name), lower(title), lower(COALESCE(location, '')), date(posted_at));
