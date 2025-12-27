-- Migration: Adicionar coluna spreadsheet_id em yt_channels
-- Data: 2025-12-27
-- Propósito: Armazenar ID das planilhas Google Sheets para varredura automática

-- Adiciona coluna se não existir (idempotente - pode rodar múltiplas vezes)
ALTER TABLE yt_channels
ADD COLUMN IF NOT EXISTS spreadsheet_id TEXT;

-- Adiciona comentário descritivo
COMMENT ON COLUMN yt_channels.spreadsheet_id
IS 'ID da planilha Google Sheets do canal (formato: 1abc...xyz)';

-- Índice para performance (opcional, mas recomendado)
CREATE INDEX IF NOT EXISTS idx_yt_channels_spreadsheet_id
ON yt_channels(spreadsheet_id)
WHERE spreadsheet_id IS NOT NULL;

-- Verifica resultado
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'yt_channels'
  AND column_name = 'spreadsheet_id';
