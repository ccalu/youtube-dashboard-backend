-- ==========================================
-- SCRIPT SQL PARA CRIAR TABELAS DE ANALYTICS AVANÇADO
-- Execute este SQL no Supabase SQL Editor
-- ==========================================

-- 1. Tabela de fontes de tráfego
CREATE TABLE IF NOT EXISTS yt_traffic_summary (
    id BIGSERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    date DATE NOT NULL,
    source_type TEXT NOT NULL, -- 'YT_SEARCH', 'RELATED_VIDEO', 'BROWSE_FEATURES', 'EXTERNAL_URL', etc
    views INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(channel_id, date, source_type)
);

-- 2. Tabela de termos de busca
CREATE TABLE IF NOT EXISTS yt_search_analytics (
    id BIGSERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    date DATE NOT NULL,
    search_term TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    percentage_of_search DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(channel_id, date, search_term)
);

-- 3. Tabela de vídeos que recomendam
CREATE TABLE IF NOT EXISTS yt_suggested_sources (
    id BIGSERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    date DATE NOT NULL,
    source_video_id TEXT,
    source_video_title TEXT,
    source_channel_name TEXT,
    views_generated INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(channel_id, date, source_video_id)
);

-- 4. Tabela de demographics
CREATE TABLE IF NOT EXISTS yt_demographics (
    id BIGSERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    date DATE NOT NULL,
    age_group TEXT, -- 'age13-17', 'age18-24', 'age25-34', 'age35-44', 'age45-54', 'age55-64', 'age65-'
    gender TEXT, -- 'FEMALE', 'MALE', 'USER_SPECIFIED_OTHER'
    views INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(channel_id, date, age_group, gender)
);

-- 5. Tabela de dispositivos
CREATE TABLE IF NOT EXISTS yt_device_metrics (
    id BIGSERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    date DATE NOT NULL,
    device_type TEXT NOT NULL, -- 'MOBILE', 'DESKTOP', 'TV', 'TABLET', 'GAME_CONSOLE', etc
    views INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(channel_id, date, device_type)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_traffic_channel_date ON yt_traffic_summary(channel_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_search_channel_date ON yt_search_analytics(channel_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_suggested_channel_date ON yt_suggested_sources(channel_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_demographics_channel_date ON yt_demographics(channel_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_device_channel_date ON yt_device_metrics(channel_id, date DESC);

-- Criar índices para filtros de período
CREATE INDEX IF NOT EXISTS idx_traffic_date ON yt_traffic_summary(date DESC);
CREATE INDEX IF NOT EXISTS idx_search_date ON yt_search_analytics(date DESC);
CREATE INDEX IF NOT EXISTS idx_suggested_date ON yt_suggested_sources(date DESC);
CREATE INDEX IF NOT EXISTS idx_demographics_date ON yt_demographics(date DESC);
CREATE INDEX IF NOT EXISTS idx_device_date ON yt_device_metrics(date DESC);

-- Adicionar triggers para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar triggers em todas as tabelas
CREATE TRIGGER update_yt_traffic_summary_updated_at BEFORE UPDATE ON yt_traffic_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_yt_search_analytics_updated_at BEFORE UPDATE ON yt_search_analytics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_yt_suggested_sources_updated_at BEFORE UPDATE ON yt_suggested_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_yt_demographics_updated_at BEFORE UPDATE ON yt_demographics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_yt_device_metrics_updated_at BEFORE UPDATE ON yt_device_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Adicionar performance score na tabela de canais (se não existir)
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS performance_score DECIMAL(3,2) DEFAULT 0;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS last_analytics_update TIMESTAMPTZ;

-- Criar view para facilitar consultas agregadas por subnicho
CREATE OR REPLACE VIEW vw_analytics_by_subnicho AS
SELECT
    c.subnicho,
    t.date,
    t.source_type,
    SUM(t.views) as total_views,
    SUM(t.watch_time_minutes) as total_watch_time,
    AVG(t.percentage) as avg_percentage
FROM yt_traffic_summary t
JOIN yt_channels c ON t.channel_id = c.channel_id
WHERE c.subnicho IS NOT NULL
GROUP BY c.subnicho, t.date, t.source_type;

-- View para demographics por subnicho
CREATE OR REPLACE VIEW vw_demographics_by_subnicho AS
SELECT
    c.subnicho,
    d.date,
    d.age_group,
    d.gender,
    SUM(d.views) as total_views,
    AVG(d.percentage) as avg_percentage
FROM yt_demographics d
JOIN yt_channels c ON d.channel_id = c.channel_id
WHERE c.subnicho IS NOT NULL
GROUP BY c.subnicho, d.date, d.age_group, d.gender;

COMMENT ON TABLE yt_traffic_summary IS 'Armazena origem do tráfego dos canais monetizados';
COMMENT ON TABLE yt_search_analytics IS 'Top 10 termos de busca que trazem views';
COMMENT ON TABLE yt_suggested_sources IS 'Top 10 vídeos/canais que recomendam nossos vídeos';
COMMENT ON TABLE yt_demographics IS 'Demografia da audiência (idade e gênero)';
COMMENT ON TABLE yt_device_metrics IS 'Distribuição de dispositivos (mobile, desktop, TV, etc)';

-- ==========================================
-- EXECUTAR ESTE SQL NO SUPABASE!
-- ==========================================