-- Migration 024: Tabela para Agente de Satisfacao (standalone)
-- Anteriormente os dados ficavam embutidos em copy_analysis_runs.results_json
-- Agora o agente de satisfacao tem tabela propria

CREATE TABLE IF NOT EXISTS satisfaction_analysis_runs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL,
    channel_name VARCHAR(255),
    run_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
    total_videos_analyzed INTEGER DEFAULT 0,
    total_videos_excluded INTEGER DEFAULT 0,
    channel_avg_approval FLOAT,
    channel_avg_sub_ratio FLOAT,
    channel_avg_comment_ratio FLOAT,
    results_json JSONB,
    report_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_satisfaction_runs_channel
    ON satisfaction_analysis_runs(channel_id);

CREATE INDEX IF NOT EXISTS idx_satisfaction_runs_date
    ON satisfaction_analysis_runs(channel_id, run_date DESC);
