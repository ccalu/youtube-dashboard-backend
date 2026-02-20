-- ============================================================
-- MIGRATION 015: Agente de Analise de Copy
-- Data: 2026-02-20
-- Ordem: Rodar ANTES de deployar codigo novo no Railway
-- ============================================================

-- 1. Tabela unica: historico de analises por canal
--    results_json guarda tudo (ranking + videos + anomalias)
CREATE TABLE IF NOT EXISTS copy_analysis_runs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL,
    channel_name VARCHAR(255),
    run_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
    total_videos_analyzed INTEGER DEFAULT 0,
    total_videos_excluded INTEGER DEFAULT 0,
    total_videos_no_match INTEGER DEFAULT 0,
    channel_avg_retention FLOAT,
    channel_avg_watch_time FLOAT,
    channel_avg_views FLOAT,
    results_json JSONB,
    report_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_copy_runs_channel_id ON copy_analysis_runs(channel_id);
CREATE INDEX IF NOT EXISTS idx_copy_runs_channel_date ON copy_analysis_runs(channel_id, run_date DESC);

-- 2. Colunas de retencao em yt_video_metrics (collector salva aqui)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'yt_video_metrics' AND column_name = 'avg_view_duration') THEN
        ALTER TABLE yt_video_metrics ADD COLUMN avg_view_duration FLOAT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'yt_video_metrics' AND column_name = 'avg_retention_pct') THEN
        ALTER TABLE yt_video_metrics ADD COLUMN avg_retention_pct FLOAT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'yt_video_metrics' AND column_name = 'card_click_rate') THEN
        ALTER TABLE yt_video_metrics ADD COLUMN card_click_rate FLOAT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_yt_video_metrics_retention
    ON yt_video_metrics(channel_id, video_id)
    WHERE avg_retention_pct IS NOT NULL;

-- 3. Mesmas colunas em yt_video_daily (snapshots diarios)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'yt_video_daily' AND column_name = 'avg_view_duration') THEN
        ALTER TABLE yt_video_daily ADD COLUMN avg_view_duration FLOAT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'yt_video_daily' AND column_name = 'avg_retention_pct') THEN
        ALTER TABLE yt_video_daily ADD COLUMN avg_retention_pct FLOAT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'yt_video_daily' AND column_name = 'card_click_rate') THEN
        ALTER TABLE yt_video_daily ADD COLUMN card_click_rate FLOAT;
    END IF;
END $$;
