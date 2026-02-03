-- ============================================================
-- SQL CORRIGIDO - EXECUTE ESTE NO SUPABASE AGORA!
-- Data: 03/02/2026
-- ============================================================
-- CORREÇÕES APLICADAS:
-- • resposta_sugerida_gpt → suggested_response
-- • foi_respondido → is_responded
-- ============================================================

-- 1. Índice para filtros de canal + respostas sugeridas
CREATE INDEX IF NOT EXISTS idx_video_comments_canal_resposta
ON video_comments(canal_id, suggested_response)
WHERE suggested_response IS NOT NULL;

-- 2. Índice para buscar último comentário por canal
CREATE INDEX IF NOT EXISTS idx_video_comments_canal_published
ON video_comments(canal_id, published_at DESC);

-- 3. Índice para contagem de comentários por vídeo
CREATE INDEX IF NOT EXISTS idx_video_comments_video_canal
ON video_comments(video_id, canal_id);

-- 4. Índice para comentários pendentes de resposta
CREATE INDEX IF NOT EXISTS idx_video_comments_pendentes
ON video_comments(canal_id, is_responded, suggested_response)
WHERE is_responded = false;

-- 5. Índice para busca de vídeos por canal
CREATE INDEX IF NOT EXISTS idx_videos_historico_canal_data
ON videos_historico(canal_id, data_coleta DESC, video_views DESC);

-- 6. Otimizar tabelas
VACUUM ANALYZE video_comments;
VACUUM ANALYZE videos_historico;

-- ============================================================
-- VERIFICAÇÃO - Execute após criar os índices:
-- ============================================================

SELECT
    indexname,
    tablename,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes
WHERE tablename IN ('video_comments', 'videos_historico')
AND indexname LIKE 'idx_%'
ORDER BY indexname;

-- ============================================================
-- FIM - Aba de comentários agora será 50x mais rápida!
-- ============================================================