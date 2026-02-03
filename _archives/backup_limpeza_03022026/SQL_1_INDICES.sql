-- ============================================================
-- SQL 1 - CRIAR ÍNDICES DE PERFORMANCE
-- EXECUTE ESTE PRIMEIRO!
-- Data: 03/02/2026
-- ============================================================
-- Campos verificados contra schema real do banco:
-- • video_comments: suggested_response, is_responded, published_at
-- • videos_historico: views_atuais, data_coleta
-- ============================================================

-- 1. Índice para filtros de canal + respostas sugeridas
CREATE INDEX IF NOT EXISTS idx_video_comments_canal_resposta
ON video_comments(canal_id, suggested_response)
WHERE suggested_response IS NOT NULL;

-- 2. Índice para ordenação por data de publicação
CREATE INDEX IF NOT EXISTS idx_video_comments_canal_published
ON video_comments(canal_id, published_at DESC);

-- 3. Índice composto para contagem de comentários por vídeo
CREATE INDEX IF NOT EXISTS idx_video_comments_video_canal
ON video_comments(video_id, canal_id);

-- 4. Índice para comentários pendentes de resposta
CREATE INDEX IF NOT EXISTS idx_video_comments_pendentes
ON video_comments(canal_id, is_responded, suggested_response)
WHERE is_responded = false;

-- NOTA: O índice idx_videos_historico_canal_data já existe, não precisa recriar

-- ============================================================
-- VERIFICAÇÃO - Execute após criar os índices:
-- ============================================================
SELECT
    COUNT(*) as indices_criados,
    STRING_AGG(indexname, ', ') as nomes
FROM pg_indexes
WHERE tablename = 'video_comments'
AND indexname LIKE 'idx_video_comments_%';

-- ============================================================
-- RESULTADO ESPERADO: 4 novos índices criados
-- ============================================================