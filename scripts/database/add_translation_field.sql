-- =====================================================
-- ADICIONAR CAMPO DE TRADUÇÃO PARA COMENTÁRIOS
-- Data: 26/01/2026
-- Objetivo: Adicionar campo comment_text_pt para tradução dos comentários
-- =====================================================

-- 1. Adicionar coluna para tradução em português
ALTER TABLE video_comments
ADD COLUMN IF NOT EXISTS comment_text_pt TEXT;

-- 2. Adicionar flag indicando se foi traduzido
ALTER TABLE video_comments
ADD COLUMN IF NOT EXISTS is_translated BOOLEAN DEFAULT FALSE;

-- 3. Criar índice para buscar comentários não traduzidos rapidamente
CREATE INDEX IF NOT EXISTS idx_vc_not_translated
ON video_comments(is_translated)
WHERE is_translated = FALSE;

-- 4. Criar índice para buscar comentários por canal com tradução
CREATE INDEX IF NOT EXISTS idx_vc_canal_translated
ON video_comments(canal_id, is_translated);

-- 5. Verificar estrutura após mudanças
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'video_comments'
AND column_name IN ('comment_text_pt', 'is_translated')
ORDER BY ordinal_position;

-- 6. Contar quantos comentários precisam de tradução
SELECT
    COUNT(*) as total_comments,
    COUNT(comment_text_pt) as already_translated,
    COUNT(*) - COUNT(comment_text_pt) as needs_translation
FROM video_comments;

-- 7. Ver amostra de comentários que precisam tradução
SELECT
    comment_id,
    author_name,
    LEFT(comment_text_original, 100) as text_preview,
    sentiment_category,
    language
FROM video_comments
WHERE comment_text_pt IS NULL
LIMIT 10;