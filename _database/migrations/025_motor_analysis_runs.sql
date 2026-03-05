-- Migration 025: Tabela para Agente 4 (Motores Psicologicos)
-- Separado do Agente 3 (Temas) para analise independente

CREATE TABLE IF NOT EXISTS motor_analysis_runs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL,
    channel_name VARCHAR(255),
    run_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
    run_number INTEGER DEFAULT 1,

    -- Link ao theme run usado como input
    theme_run_id INTEGER REFERENCES theme_analysis_runs(id),

    -- Output do LLM MOTORES
    report_text TEXT,

    -- Estatisticas de motores {motor, count, total_videos, pct, avg_score}
    motor_counts_json JSONB,

    -- Snapshot do ranking usado (reprodutibilidade)
    ranking_snapshot JSONB,

    -- Metadata
    total_videos INTEGER DEFAULT 0,
    is_first_analysis BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_motor_runs_channel
    ON motor_analysis_runs(channel_id);

CREATE INDEX IF NOT EXISTS idx_motor_runs_channel_date
    ON motor_analysis_runs(channel_id, run_date DESC);
