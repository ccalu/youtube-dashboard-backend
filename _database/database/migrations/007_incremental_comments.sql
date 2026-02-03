-- Migration: Adicionar campo para coleta incremental de comentários
-- Data: 2026-01-19
-- Objetivo: Rastrear último comentário coletado para buscar apenas novos

-- Adicionar campo para rastrear último comentário coletado
ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS ultimo_comentario_coletado TIMESTAMP WITH TIME ZONE;

-- Criar índice para performance
CREATE INDEX IF NOT EXISTS idx_canais_ultimo_comentario
ON canais_monitorados(ultimo_comentario_coletado);

-- Comentário explicativo
COMMENT ON COLUMN canais_monitorados.ultimo_comentario_coletado IS
'Timestamp do último comentário coletado. Usado para coleta incremental - só buscar comentários após esta data.';

-- Adicionar campo para contar total de comentários coletados historicamente
ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS total_comentarios_coletados INTEGER DEFAULT 0;

-- Adicionar campo na tabela de vídeos para rastrear último comentário
ALTER TABLE videos_historico
ADD COLUMN IF NOT EXISTS ultimo_comentario_coletado TIMESTAMP WITH TIME ZONE;

-- Índice para busca rápida
CREATE INDEX IF NOT EXISTS idx_videos_ultimo_comentario
ON videos_historico(ultimo_comentario_coletado);