-- Migration 020: Theme Analysis tables (Agent 5 - Temas)
-- Tabela para armazenar analises de temas especificos por canal

CREATE TABLE IF NOT EXISTS theme_analysis_runs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL,
    channel_name VARCHAR(255),
    run_date TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Metricas
    theme_count INTEGER DEFAULT 0,
    total_videos_analyzed INTEGER DEFAULT 0,
    concentration_pct FLOAT,

    -- Dados (JSONB)
    ranking_json JSONB,
    themes_list JSONB,
    patterns_json JSONB,

    -- LLM output
    report_text TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_theme_runs_channel_id
    ON theme_analysis_runs(channel_id);

CREATE INDEX IF NOT EXISTS idx_theme_runs_channel_date
    ON theme_analysis_runs(channel_id, run_date DESC);
