-- Script para adicionar campo response_generated_at
-- Data: 03/02/2026
-- Necessário para rastrear quando as respostas foram geradas

-- Adicionar coluna response_generated_at se não existir
ALTER TABLE video_comments
ADD COLUMN IF NOT EXISTS response_generated_at TIMESTAMP WITH TIME ZONE;

-- Criar índice para melhor performance
CREATE INDEX IF NOT EXISTS idx_response_generated_at
ON video_comments(response_generated_at DESC)
WHERE response_generated_at IS NOT NULL;

-- Atualizar registros existentes que têm resposta mas não têm data
UPDATE video_comments
SET response_generated_at = updated_at
WHERE suggested_response IS NOT NULL
  AND response_generated_at IS NULL
  AND updated_at IS NOT NULL;

-- Para respostas antigas sem updated_at, usar data padrão
UPDATE video_comments
SET response_generated_at = '2026-01-27 00:00:00+00:00'
WHERE suggested_response IS NOT NULL
  AND response_generated_at IS NULL;