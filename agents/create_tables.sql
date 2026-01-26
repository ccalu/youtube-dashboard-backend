-- ========================================
-- TABELAS PARA O SISTEMA DE AGENTES
-- Execute este SQL no Supabase (SQL Editor)
-- ========================================

-- 1. Tabela para descobertas do Scout Agent
CREATE TABLE IF NOT EXISTS scout_discoveries (
    id SERIAL PRIMARY KEY,
    channel_id TEXT UNIQUE NOT NULL,
    nome_canal TEXT NOT NULL,
    url_canal TEXT NOT NULL,
    descricao TEXT,
    subnicho_sugerido TEXT,
    inscritos INTEGER DEFAULT 0,
    total_videos INTEGER DEFAULT 0,
    scout_score FLOAT DEFAULT 0,
    days_since_last_video INTEGER,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'pending', -- pending, approved, rejected
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index para buscas
CREATE INDEX IF NOT EXISTS idx_scout_discoveries_status ON scout_discoveries(status);
CREATE INDEX IF NOT EXISTS idx_scout_discoveries_subnicho ON scout_discoveries(subnicho_sugerido);
CREATE INDEX IF NOT EXISTS idx_scout_discoveries_score ON scout_discoveries(scout_score DESC);

-- 2. Tabela para historico de tendencias
CREATE TABLE IF NOT EXISTS trend_history (
    id SERIAL PRIMARY KEY,
    data DATE UNIQUE NOT NULL,
    total_trending_videos INTEGER DEFAULT 0,
    total_trending_topics INTEGER DEFAULT 0,
    top_videos TEXT[], -- Array de video_ids
    top_topics TEXT[], -- Array de keywords
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_trend_history_data ON trend_history(data DESC);

-- 3. Tabela para alertas dos agentes
CREATE TABLE IF NOT EXISTS agent_alerts (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL, -- viral, trend, drop, opportunity, recycle
    priority TEXT NOT NULL, -- critical, high, medium, low
    title TEXT NOT NULL,
    message TEXT,
    data JSONB, -- Dados adicionais em JSON
    action_suggested TEXT,
    status TEXT DEFAULT 'new', -- new, seen, actioned, dismissed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    seen_at TIMESTAMP WITH TIME ZONE,
    actioned_at TIMESTAMP WITH TIME ZONE
);

-- Index para alertas
CREATE INDEX IF NOT EXISTS idx_agent_alerts_status ON agent_alerts(status);
CREATE INDEX IF NOT EXISTS idx_agent_alerts_priority ON agent_alerts(priority);
CREATE INDEX IF NOT EXISTS idx_agent_alerts_type ON agent_alerts(type);
CREATE INDEX IF NOT EXISTS idx_agent_alerts_created ON agent_alerts(created_at DESC);

-- 4. Tabela para execucoes dos agentes (log)
CREATE TABLE IF NOT EXISTS agent_executions (
    id SERIAL PRIMARY KEY,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL, -- running, completed, failed
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT,
    metrics JSONB,
    errors TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent ON agent_executions(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_executions_started ON agent_executions(started_at DESC);

-- 5. Tabela para recomendacoes salvas
CREATE TABLE IF NOT EXISTS agent_recommendations (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL, -- clone_video, cross_language, trend_topic, etc
    priority TEXT NOT NULL,
    canal_id INTEGER REFERENCES canais_monitorados(id),
    canal_nome TEXT,
    action TEXT NOT NULL,
    reason TEXT,
    score FLOAT DEFAULT 0,
    data JSONB,
    status TEXT DEFAULT 'pending', -- pending, in_progress, completed, dismissed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_agent_recommendations_canal ON agent_recommendations(canal_id);
CREATE INDEX IF NOT EXISTS idx_agent_recommendations_status ON agent_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_agent_recommendations_priority ON agent_recommendations(priority);

-- ========================================
-- GRANT PERMISSIONS (se necessario)
-- ========================================

-- Permitir acesso anonimo as tabelas (ajustar conforme necessario)
-- GRANT ALL ON scout_discoveries TO anon;
-- GRANT ALL ON trend_history TO anon;
-- GRANT ALL ON agent_alerts TO anon;
-- GRANT ALL ON agent_executions TO anon;
-- GRANT ALL ON agent_recommendations TO anon;

-- ========================================
-- VIEWS UTEIS
-- ========================================

-- View de alertas nao vistos
CREATE OR REPLACE VIEW v_unread_alerts AS
SELECT *
FROM agent_alerts
WHERE status = 'new'
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    created_at DESC;

-- View de descobertas pendentes
CREATE OR REPLACE VIEW v_pending_discoveries AS
SELECT *
FROM scout_discoveries
WHERE status = 'pending'
ORDER BY scout_score DESC, discovered_at DESC;

-- ========================================
-- FIM
-- ========================================
