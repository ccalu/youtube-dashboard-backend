-- Migration 031: Tabela de fila para jobs de agentes processados via Claude CLI local
-- Worker na maquina do Marcelo poll essa tabela e processa via Claude Opus 4.6

CREATE TABLE IF NOT EXISTS agent_jobs (
    id SERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,          -- 'temas' ou 'motores'
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    input_data JSONB,                  -- dados serializados para rodar o agente
    result_data JSONB,                 -- resultado (run_id, success, error)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_jobs_status ON agent_jobs(status);
CREATE INDEX IF NOT EXISTS idx_agent_jobs_channel ON agent_jobs(channel_id, agent_type);
