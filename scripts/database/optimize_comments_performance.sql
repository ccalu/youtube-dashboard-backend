-- OTIMIZAÇÃO CRÍTICA DE PERFORMANCE - ABA COMENTÁRIOS
-- Data: 03/02/2026
-- Objetivo: Reduzir tempo de carregamento de 3-5 segundos para <200ms

-- ============================================
-- ÍNDICES PARA QUERIES DE COMENTÁRIOS
-- ============================================

-- 1. Índice composto para filtros de canal + status de resposta
CREATE INDEX IF NOT EXISTS idx_video_comments_canal_resposta
ON video_comments(canal_id, resposta_sugerida_gpt)
WHERE resposta_sugerida_gpt IS NOT NULL;

-- 2. Índice para ordenação por data de publicação (último comentário)
CREATE INDEX IF NOT EXISTS idx_video_comments_canal_published
ON video_comments(canal_id, published_at DESC);

-- 3. Índice composto para contagem de comentários por vídeo
CREATE INDEX IF NOT EXISTS idx_video_comments_video_canal
ON video_comments(video_id, canal_id);

-- 4. Índice para filtro de comentários pendentes
CREATE INDEX IF NOT EXISTS idx_video_comments_pendentes
ON video_comments(canal_id, foi_respondido, resposta_sugerida_gpt)
WHERE foi_respondido = false;

-- 5. Índice para busca rápida de vídeos por canal
CREATE INDEX IF NOT EXISTS idx_videos_historico_canal_data
ON videos_historico(canal_id, data_coleta DESC, video_views DESC);

-- ============================================
-- ESTATÍSTICAS PARA VERIFICAR MELHORIA
-- ============================================

-- Antes de aplicar os índices, execute:
EXPLAIN ANALYZE
SELECT canal_id, COUNT(*)
FROM video_comments
WHERE canal_id IN (875, 918, 919, 932, 936, 947)
GROUP BY canal_id;

-- Depois de aplicar, execute novamente para comparar

-- ============================================
-- VACUUM E ANÁLISE
-- ============================================

-- Otimiza o armazenamento e atualiza estatísticas
VACUUM ANALYZE video_comments;
VACUUM ANALYZE videos_historico;

-- ============================================
-- VERIFICAÇÃO DOS ÍNDICES CRIADOS
-- ============================================

SELECT indexname, tablename, indexdef
FROM pg_indexes
WHERE tablename IN ('video_comments', 'videos_historico')
AND indexname LIKE 'idx_video_comments%'
ORDER BY indexname;