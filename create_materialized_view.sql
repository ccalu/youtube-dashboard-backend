-- ============================================
-- CRIAR MATERIALIZED VIEW PARA STATS DE VÍDEOS
-- ============================================
-- Este script cria uma Materialized View otimizada para calcular
-- total_videos e total_views de cada canal de forma INSTANTÂNEA
--
-- PERFORMANCE ESPERADA:
-- Antes: ~95 segundos (paginação de 368k registros)
-- Depois: < 100ms (query direta na MV)
-- ============================================

-- PASSO 1: Criar a Materialized View
-- Esta view pré-calcula os totais de vídeos e views para cada canal
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_canal_video_stats AS
WITH latest_videos AS (
    -- Pega apenas o registro mais recente de cada vídeo
    SELECT DISTINCT ON (canal_id, video_id)
        canal_id,
        video_id,
        views_atuais
    FROM videos_historico
    WHERE canal_id IS NOT NULL
        AND video_id IS NOT NULL
    ORDER BY canal_id, video_id, data_coleta DESC
)
SELECT
    canal_id,
    COUNT(DISTINCT video_id)::INTEGER as total_videos,
    COALESCE(SUM(views_atuais), 0)::BIGINT as total_views
FROM latest_videos
GROUP BY canal_id;

-- PASSO 2: Criar índice ÚNICO (necessário para refresh CONCURRENTLY)
-- Isso permite refresh sem travar leituras
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_canal_video_stats_canal_id
ON mv_canal_video_stats (canal_id);

-- PASSO 3: Criar função para refresh manual
CREATE OR REPLACE FUNCTION refresh_mv_canal_video_stats()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Refresh CONCURRENTLY = não trava leituras
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_canal_video_stats;

    -- Log do refresh (opcional)
    RAISE NOTICE 'Materialized View mv_canal_video_stats refreshed at %', NOW();
END;
$$;

-- PASSO 4: Fazer o primeiro refresh (pode demorar ~30 segundos)
-- Isso popula a MV com os dados atuais
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_canal_video_stats;

-- PASSO 5: Verificar se funcionou
SELECT
    COUNT(*) as total_canais,
    SUM(total_videos) as total_videos_geral,
    SUM(total_views) as total_views_geral
FROM mv_canal_video_stats;

-- ============================================
-- TESTE DE PERFORMANCE
-- ============================================
-- Execute este comando para ver a performance:
EXPLAIN ANALYZE
SELECT * FROM mv_canal_video_stats
WHERE canal_id IN (
    SELECT id FROM canais_monitorados
    WHERE status = 'ativo'
    LIMIT 10
);

-- Deve mostrar algo como:
-- Execution Time: 0.XXX ms (menos de 1ms!)

-- ============================================
-- COMO FAZER REFRESH MANUAL (quando necessário)
-- ============================================
-- Opção 1: Via função
-- SELECT refresh_mv_canal_video_stats();

-- Opção 2: Comando direto
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_canal_video_stats;

-- ============================================
-- ROLLBACK (se precisar reverter)
-- ============================================
-- DROP MATERIALIZED VIEW IF EXISTS mv_canal_video_stats CASCADE;
-- DROP FUNCTION IF EXISTS refresh_mv_canal_video_stats();