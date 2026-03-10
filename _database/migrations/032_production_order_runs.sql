-- Migration 032: Tabela para Agente 7 (Ordenador de Producao)
-- Recomenda ordem otima de producao/postagem baseado nos motores psicologicos + saude do canal

CREATE TABLE IF NOT EXISTS production_order_runs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL,
    channel_name VARCHAR(255),
    run_date TIMESTAMPTZ DEFAULT now(),
    run_number INTEGER DEFAULT 1,

    -- Links aos runs usados como input
    motor_run_id INTEGER REFERENCES motor_analysis_runs(id),
    auth_run_id INTEGER REFERENCES authenticity_analysis_runs(id),

    -- Output do LLM
    report_text TEXT,

    -- JSON estruturado: ordered scripts + tiers
    order_json JSONB,

    -- Snapshot dos scripts pendentes (para deteccao incremental)
    pending_scripts_snapshot JSONB,

    -- Metadata
    total_scripts INTEGER DEFAULT 0,
    channel_health VARCHAR(20),
    is_first_analysis BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_prod_order_channel ON production_order_runs(channel_id);
CREATE INDEX IF NOT EXISTS idx_prod_order_channel_date ON production_order_runs(channel_id, run_date DESC);
