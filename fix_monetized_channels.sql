-- ============================================================
-- FIX: Adicionar campo is_monetized e marcar canais monetizados
-- Data: 30/01/2026
-- Problema: Sistema precisa identificar claramente canais monetizados
-- Solução: Adicionar campo is_monetized e marcar os 10 canais
-- ============================================================

-- 1. Adicionar campo is_monetized se não existir
ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS is_monetized BOOLEAN DEFAULT FALSE;

-- 2. Marcar canais com subnicho='Monetizados' como monetizados
UPDATE canais_monitorados
SET is_monetized = TRUE
WHERE subnicho = 'Monetizados'
  AND tipo = 'nosso';

-- 3. Verificar resultado
SELECT
    subnicho,
    COUNT(*) as total,
    SUM(CASE WHEN is_monetized THEN 1 ELSE 0 END) as monetizados
FROM canais_monitorados
WHERE tipo = 'nosso'
GROUP BY subnicho
ORDER BY subnicho;

-- 4. Listar canais monetizados para confirmação
SELECT
    id,
    nome_canal,
    subnicho,
    is_monetized,
    status
FROM canais_monitorados
WHERE is_monetized = TRUE
ORDER BY nome_canal;

-- ============================================================
-- RESULTADO ESPERADO:
-- - 10 canais com is_monetized=TRUE
-- - Todos com subnicho='Monetizados'
-- - Sistema poderá identificar facilmente para gerar respostas
-- ============================================================

-- IMPORTANTE: Execute este script no Supabase SQL Editor!