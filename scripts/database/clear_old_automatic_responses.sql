-- Script para limpar respostas automáticas antigas
-- Data: 03/02/2026
-- Objetivo: Remover 1.860 respostas geradas automaticamente pelo sistema antigo

-- Backup count antes de limpar
SELECT COUNT(*) as total_responses_before
FROM video_comments
WHERE suggested_response IS NOT NULL;

-- Limpar todas as respostas automáticas antigas
UPDATE video_comments
SET
    suggested_response = NULL,
    response_generated_at = NULL,
    response_tone = NULL
WHERE suggested_response IS NOT NULL;

-- Verificar limpeza
SELECT COUNT(*) as total_responses_after
FROM video_comments
WHERE suggested_response IS NOT NULL;

-- Estatísticas finais
SELECT
    COUNT(*) as total_comments,
    COUNT(CASE WHEN suggested_response IS NOT NULL THEN 1 END) as with_response,
    COUNT(CASE WHEN is_responded = true THEN 1 END) as responded
FROM video_comments;

-- Mensagem de conclusão
-- IMPORTANTE: Após executar, as respostas serão geradas sob demanda via dashboard