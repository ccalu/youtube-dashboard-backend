-- ============================================================
-- MIGRATION 017: CTR Collector (YouTube Reporting API)
-- Data: 2026-02-25
-- Ordem: Rodar ANTES de deployar codigo novo no Railway
-- ============================================================

-- 1. Adicionar colunas de CTR na tabela yt_video_metrics
ALTER TABLE yt_video_metrics ADD COLUMN IF NOT EXISTS impressions BIGINT;
ALTER TABLE yt_video_metrics ADD COLUMN IF NOT EXISTS ctr FLOAT;

-- 2. Adicionar colunas de CTR na tabela yt_video_daily (snapshots)
ALTER TABLE yt_video_daily ADD COLUMN IF NOT EXISTS impressions BIGINT;
ALTER TABLE yt_video_daily ADD COLUMN IF NOT EXISTS ctr FLOAT;

-- 3. Tabela de controle dos Reporting API jobs
CREATE TABLE IF NOT EXISTS yt_reporting_jobs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL,
    job_id VARCHAR(100),
    report_type VARCHAR(50) NOT NULL DEFAULT 'channel_reach_basic_a1',
    status VARCHAR(20) NOT NULL DEFAULT 'pending_creation',
    last_report_date DATE,
    last_report_id VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(channel_id, report_type)
);

-- 4. CTR medio do canal em yt_channels
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS avg_ctr FLOAT;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS total_impressions BIGINT;

-- 5. Indexes
CREATE INDEX IF NOT EXISTS idx_reporting_jobs_channel
    ON yt_reporting_jobs(channel_id);
CREATE INDEX IF NOT EXISTS idx_reporting_jobs_status
    ON yt_reporting_jobs(status);
CREATE INDEX IF NOT EXISTS idx_yt_video_metrics_ctr
    ON yt_video_metrics(channel_id, video_id)
    WHERE ctr IS NOT NULL;
