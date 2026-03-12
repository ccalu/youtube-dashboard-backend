-- ============================================================
-- MIGRATION 019: Agente 4 - Estruturas de Titulo
-- Data: 2026-02-27
-- Ordem: Rodar ANTES de deployar codigo novo no Railway
-- ============================================================

-- Tabela: historico de analises de estruturas de titulo por canal
CREATE TABLE IF NOT EXISTS title_structure_analysis_runs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL,
    channel_name VARCHAR(255),
    run_date TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Metricas
    structure_count INTEGER DEFAULT 0,
    total_videos_analyzed INTEGER DEFAULT 0,
    has_ctr_data BOOLEAN DEFAULT FALSE,

    -- Dados (JSONB)
    ranking_json JSONB,
    structures_list JSONB,
    patterns_json JSONB,

    -- LLM output
    report_text TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_title_runs_channel_id
    ON title_structure_analysis_runs(channel_id);
CREATE INDEX IF NOT EXISTS idx_title_runs_channel_date
    ON title_structure_analysis_runs(channel_id, run_date DESC);
