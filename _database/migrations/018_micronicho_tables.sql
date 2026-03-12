-- ============================================================
-- MIGRATION 018: Agente 3 - Analise de Micronichos
-- Data: 2026-02-27
-- Ordem: Rodar ANTES de deployar codigo novo no Railway
-- ============================================================

-- Tabela: historico de analises de micronichos por canal
CREATE TABLE IF NOT EXISTS micronicho_analysis_runs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL,
    channel_name VARCHAR(255),
    run_date TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Metricas
    micronicho_count INTEGER DEFAULT 0,
    total_videos_analyzed INTEGER DEFAULT 0,
    concentration_pct FLOAT,

    -- Dados (JSONB)
    ranking_json JSONB,
    micronichos_list JSONB,
    patterns_json JSONB,

    -- LLM output
    report_text TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_micro_runs_channel_id
    ON micronicho_analysis_runs(channel_id);
CREATE INDEX IF NOT EXISTS idx_micro_runs_channel_date
    ON micronicho_analysis_runs(channel_id, run_date DESC);
