-- ============================================================
-- MIGRATION 016: Agente de Score de Autenticidade
-- Data: 2026-02-24
-- Ordem: Rodar ANTES de deployar codigo novo no Railway
-- ============================================================

-- Tabela: historico de analises de autenticidade por canal
CREATE TABLE IF NOT EXISTS authenticity_analysis_runs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL,
    channel_name VARCHAR(255),
    run_date TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Score composto (0-100, mais alto = mais autentico)
    authenticity_score FLOAT,
    authenticity_level VARCHAR(20),  -- excelente/bom/atencao/risco/critico

    -- Scores por fator (0-100 cada)
    structure_score FLOAT,
    title_score FLOAT,

    -- Contagens
    total_videos_analyzed INTEGER DEFAULT 0,

    -- Resultados detalhados (JSONB)
    results_json JSONB,
    report_text TEXT,

    -- Alertas
    has_alerts BOOLEAN DEFAULT FALSE,
    alert_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_runs_channel_id
    ON authenticity_analysis_runs(channel_id);
CREATE INDEX IF NOT EXISTS idx_auth_runs_channel_date
    ON authenticity_analysis_runs(channel_id, run_date DESC);
CREATE INDEX IF NOT EXISTS idx_auth_runs_score
    ON authenticity_analysis_runs(authenticity_score DESC)
    WHERE authenticity_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_auth_runs_alerts
    ON authenticity_analysis_runs(has_alerts)
    WHERE has_alerts = TRUE;
