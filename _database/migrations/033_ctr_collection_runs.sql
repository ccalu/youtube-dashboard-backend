CREATE TABLE IF NOT EXISTS ctr_collection_runs (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    total_records INTEGER DEFAULT 0,
    total_channels INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ctr_collection_runs_date ON ctr_collection_runs(started_at DESC);
