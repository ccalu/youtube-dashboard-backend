-- ============================================================
-- FIX: Adicionar coluna created_at na tabela video_comments
-- Data: 29/01/2026
-- Problema: Campo created_at não existe, impedindo filtro de "novos hoje"
-- ============================================================

-- Adicionar coluna created_at se não existir
ALTER TABLE video_comments
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;

-- Preencher created_at com published_at para comentários existentes
UPDATE video_comments
SET created_at = published_at
WHERE created_at IS NULL AND published_at IS NOT NULL;

-- Para comentários sem published_at, usar updated_at
UPDATE video_comments
SET created_at = updated_at
WHERE created_at IS NULL AND updated_at IS NOT NULL;

-- Criar índice para melhorar performance
CREATE INDEX IF NOT EXISTS idx_video_comments_created_at
ON video_comments(created_at);

-- Verificar resultado
SELECT
    COUNT(*) as total_comentarios,
    COUNT(created_at) as com_created_at,
    COUNT(*) - COUNT(created_at) as sem_created_at
FROM video_comments;

-- ============================================================
-- INSTRUÇÕES:
-- 1. Execute este script no Supabase SQL Editor
-- 2. Verifique se a coluna foi criada
-- 3. Confirme que comentários existentes têm created_at preenchido
-- ============================================================