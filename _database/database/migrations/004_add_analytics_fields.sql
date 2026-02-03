-- Migration: Adicionar campos para Analytics
-- Data: 19/01/2026
-- Autor: cellibs-escritorio

-- ==================================================
-- 1. ADICIONAR NOVOS CAMPOS EM canais_monitorados
-- ==================================================

ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS published_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS custom_url TEXT,
ADD COLUMN IF NOT EXISTS melhor_dia_semana INTEGER,
ADD COLUMN IF NOT EXISTS melhor_hora INTEGER,
ADD COLUMN IF NOT EXISTS frequencia_semanal NUMERIC(4,2);

-- Adicionar comentários explicativos
COMMENT ON COLUMN canais_monitorados.published_at IS 'Data de criação do canal no YouTube';
COMMENT ON COLUMN canais_monitorados.custom_url IS 'URL customizada do canal (@handle)';
COMMENT ON COLUMN canais_monitorados.melhor_dia_semana IS 'Melhor dia da semana para postar (0=Dom, 6=Sab)';
COMMENT ON COLUMN canais_monitorados.melhor_hora IS 'Melhor hora do dia para postar (0-23)';
COMMENT ON COLUMN canais_monitorados.frequencia_semanal IS 'Média de vídeos publicados por semana';

-- ==================================================
-- 2. CRIAR TABELA PARA CACHE DE ANALYTICS
-- ==================================================

CREATE TABLE IF NOT EXISTS canal_analytics_cache (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,

    -- Padrões identificados através de análise estatística
    padroes_identificados JSONB DEFAULT '[]',

    -- Clustering de conteúdo por performance
    clusters_conteudo JSONB DEFAULT '[]',

    -- Anomalias detectadas (outliers, tendências)
    anomalias_detectadas JSONB DEFAULT '[]',

    -- Cache dos top 10 vídeos (atualizado 1x/dia)
    top_videos_cache JSONB DEFAULT '[]',

    -- Melhor momento para postar (análise temporal)
    melhor_posting_time JSONB DEFAULT '{}',

    -- Timestamp de última atualização
    updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Índice único para evitar duplicatas
    CONSTRAINT unique_canal_analytics UNIQUE (canal_id)
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_analytics_cache_canal_id ON canal_analytics_cache(canal_id);
CREATE INDEX IF NOT EXISTS idx_analytics_cache_updated_at ON canal_analytics_cache(updated_at);

-- Adicionar comentários na tabela
COMMENT ON TABLE canal_analytics_cache IS 'Cache de análises processadas para evitar recálculo constante';
COMMENT ON COLUMN canal_analytics_cache.padroes_identificados IS 'Padrões de sucesso identificados (títulos, duração, etc)';
COMMENT ON COLUMN canal_analytics_cache.clusters_conteudo IS 'Agrupamento de vídeos por tema e performance';
COMMENT ON COLUMN canal_analytics_cache.anomalias_detectadas IS 'Anomalias estatísticas (outliers, quedas abruptas)';
COMMENT ON COLUMN canal_analytics_cache.top_videos_cache IS 'Top 10 vídeos dos últimos 30 dias';

-- ==================================================
-- 3. FUNÇÃO PARA ATUALIZAR TIMESTAMP AUTOMATICAMENTE
-- ==================================================

CREATE OR REPLACE FUNCTION update_analytics_cache_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criar trigger para atualizar timestamp
DROP TRIGGER IF EXISTS update_analytics_cache_updated_at ON canal_analytics_cache;
CREATE TRIGGER update_analytics_cache_updated_at
BEFORE UPDATE ON canal_analytics_cache
FOR EACH ROW
EXECUTE FUNCTION update_analytics_cache_timestamp();

-- ==================================================
-- 4. ADICIONAR ÍNDICES PARA MELHORAR QUERIES DE ANALYTICS
-- ==================================================

-- Índice para buscar vídeos por canal e data
CREATE INDEX IF NOT EXISTS idx_videos_historico_canal_data
ON videos_historico(canal_id, data_publicacao DESC);

-- Índice para buscar histórico recente
CREATE INDEX IF NOT EXISTS idx_dados_canais_historico_canal_data
ON dados_canais_historico(canal_id, data_coleta DESC);

-- ==================================================
-- 5. VERIFICAR SE MIGRATION FOI APLICADA COM SUCESSO
-- ==================================================

DO $$
BEGIN
    -- Verificar se os campos foram adicionados
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'canais_monitorados'
        AND column_name = 'published_at'
    ) THEN
        RAISE NOTICE 'Migration 004 aplicada com sucesso!';
    ELSE
        RAISE EXCEPTION 'Erro ao aplicar migration 004';
    END IF;
END $$;