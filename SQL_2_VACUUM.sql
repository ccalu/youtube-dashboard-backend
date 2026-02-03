-- ============================================================
-- SQL 2 - OTIMIZAÇÃO DE ARMAZENAMENTO
-- EXECUTE ESTE DEPOIS DOS ÍNDICES!
-- Data: 03/02/2026
-- ============================================================
-- IMPORTANTE: Execute este SQL SOZINHO, em separado
-- O VACUUM não pode ser executado junto com outros comandos
-- ============================================================

-- Otimizar a tabela video_comments
VACUUM ANALYZE video_comments;

-- Otimizar a tabela videos_historico
VACUUM ANALYZE videos_historico;

-- ============================================================
-- NOTA IMPORTANTE:
-- ============================================================
-- Este comando DEVE ser executado SOZINHO no SQL Editor
-- Não cole junto com outros comandos SQL
-- Execute apenas estes dois VACUUMs de uma vez
--
-- O que o VACUUM faz:
-- • Recupera espaço de registros deletados
-- • Atualiza estatísticas para o query planner
-- • Melhora performance das queries
-- ============================================================