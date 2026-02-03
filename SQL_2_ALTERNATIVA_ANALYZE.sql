-- ============================================================
-- SQL 2 ALTERNATIVA - ANALYZE SEM VACUUM
-- USE ESTE NO SUPABASE SQL EDITOR!
-- Data: 03/02/2026
-- ============================================================
-- Como o Supabase não permite VACUUM pelo SQL Editor,
-- vamos usar apenas ANALYZE que é permitido
-- ============================================================

-- Atualizar estatísticas da tabela video_comments
ANALYZE video_comments;

-- Atualizar estatísticas da tabela videos_historico
ANALYZE videos_historico;

-- ============================================================
-- VERIFICAR ESTATÍSTICAS ATUALIZADAS
-- ============================================================
SELECT
    schemaname,
    tablename,
    n_live_tup as linhas_vivas,
    n_dead_tup as linhas_mortas,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE tablename IN ('video_comments', 'videos_historico');

-- ============================================================
-- NOTA SOBRE O VACUUM:
-- ============================================================
-- O VACUUM completo não pode ser executado pelo SQL Editor
-- do Supabase pois ele sempre roda em uma transação.
--
-- ALTERNATIVAS:
-- 1. O Supabase faz AUTOVACUUM automaticamente
-- 2. Use ANALYZE (acima) para atualizar estatísticas
-- 3. O VACUUM pode ser executado via CLI do PostgreSQL
--    se você tiver acesso direto ao banco
--
-- O ANALYZE sozinho já melhora muito a performance!
-- ============================================================