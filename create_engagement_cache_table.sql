-- ============================================================
-- TABELA DE CACHE PARA DADOS DE ENGAJAMENTO PRÉ-PROCESSADOS
-- Data: 29/01/2025
-- Descrição: Armazena dados de engajamento processados após coleta diária
-- ============================================================

-- Criar tabela de cache
CREATE TABLE IF NOT EXISTS engagement_cache (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,

    -- Dados processados em JSON
    data JSONB NOT NULL,

    -- Controle de tempo
    processed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Metadata
    total_comments INTEGER DEFAULT 0,
    total_videos INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Garantir apenas um cache por canal
    CONSTRAINT unique_canal_cache UNIQUE(canal_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_engagement_cache_canal ON engagement_cache(canal_id);
CREATE INDEX IF NOT EXISTS idx_engagement_cache_expires ON engagement_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_engagement_cache_processed ON engagement_cache(processed_at);

-- Comentário na tabela
COMMENT ON TABLE engagement_cache IS 'Cache de dados de engajamento pré-processados após coleta diária';
COMMENT ON COLUMN engagement_cache.data IS 'JSON com todos dados processados (summary, videos, comments)';
COMMENT ON COLUMN engagement_cache.expires_at IS 'Quando o cache expira (normalmente 24h após processamento)';

-- Função para limpar cache expirado
CREATE OR REPLACE FUNCTION delete_expired_engagement_cache()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM engagement_cache
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$;

-- Comentário na função
COMMENT ON FUNCTION delete_expired_engagement_cache() IS 'Remove registros de cache expirados';

-- Grant permissões necessárias (ajustar conforme seu usuário)
-- GRANT ALL ON engagement_cache TO authenticated;
-- GRANT EXECUTE ON FUNCTION delete_expired_engagement_cache() TO authenticated;

-- ============================================================
-- INSTRUÇÕES DE USO:
-- 1. Execute este script no Supabase SQL Editor
-- 2. Verifique se a tabela foi criada: SELECT * FROM engagement_cache;
-- 3. O cache será populado automaticamente após próxima coleta
-- ============================================================