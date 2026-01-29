-- ============================================================
-- FIX: Adicionar coluna collected_at na tabela video_comments
-- Data: 29/01/2026
-- Problema: Campo created_at mostra data do YouTube, não data de coleta
-- Solução: Adicionar collected_at para rastrear quando foi coletado
-- ============================================================

-- 1. Adicionar coluna collected_at se não existir
ALTER TABLE video_comments
ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP WITH TIME ZONE;

-- 2. Preencher collected_at com updated_at para comentários existentes
-- (updated_at representa quando foi salvo/atualizado no banco)
UPDATE video_comments
SET collected_at = updated_at
WHERE collected_at IS NULL AND updated_at IS NOT NULL;

-- 3. Para registros sem updated_at, usar created_at
UPDATE video_comments
SET collected_at = created_at
WHERE collected_at IS NULL AND created_at IS NOT NULL;

-- 4. Para registros restantes, usar timestamp atual
UPDATE video_comments
SET collected_at = NOW()
WHERE collected_at IS NULL;

-- 5. Criar índice para melhorar performance de filtros por data de coleta
CREATE INDEX IF NOT EXISTS idx_video_comments_collected_at
ON video_comments(collected_at DESC);

-- 6. Verificar resultado
SELECT
    COUNT(*) as total_comentarios,
    COUNT(collected_at) as com_collected_at,
    COUNT(*) - COUNT(collected_at) as sem_collected_at,
    MIN(collected_at) as coleta_mais_antiga,
    MAX(collected_at) as coleta_mais_recente
FROM video_comments;

-- ============================================================
-- INSTRUÇÕES:
-- 1. Execute este script no Supabase SQL Editor
-- 2. Verifique se a coluna foi criada
-- 3. Confirme que comentários existentes têm collected_at preenchido
-- 4. Após execução, comentários "novos hoje" mostrarão coletados hoje
-- ============================================================