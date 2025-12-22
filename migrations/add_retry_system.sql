-- ============================================================
-- MIGRATION: Sistema de Retry Automático
-- Data: 2025-12-22
-- Objetivo: Adicionar colunas para retry de uploads falhados
-- ============================================================

-- Adicionar coluna retry_count
ALTER TABLE yt_upload_queue
  ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Adicionar coluna last_retry_at
ALTER TABLE yt_upload_queue
  ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMPTZ;

-- Criar índice para queries de retry
CREATE INDEX IF NOT EXISTS idx_upload_queue_retry
  ON yt_upload_queue(status, retry_count)
  WHERE status IN ('failed', 'pending');

-- Validação
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'yt_upload_queue'
        AND column_name = 'retry_count'
    ) THEN
        RAISE NOTICE '[OK] Coluna retry_count criada com sucesso';
    ELSE
        RAISE WARNING '[ERRO] Falha ao criar coluna retry_count';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'yt_upload_queue'
        AND column_name = 'last_retry_at'
    ) THEN
        RAISE NOTICE '[OK] Coluna last_retry_at criada com sucesso';
    ELSE
        RAISE WARNING '[ERRO] Falha ao criar coluna last_retry_at';
    END IF;
END $$;
