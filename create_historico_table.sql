-- Script para criar tabela de histórico de uploads
-- Esta tabela preserva TODOS os uploads, permitindo múltiplos registros por canal/dia
-- VERSÃO CORRIGIDA - Remove colunas inexistentes
-- Autor: Claude
-- Data: 10/02/2026

-- Criar a tabela de histórico
CREATE TABLE IF NOT EXISTS yt_canal_upload_historico (
  id BIGSERIAL PRIMARY KEY,
  channel_id TEXT NOT NULL,
  channel_name TEXT NOT NULL,
  data DATE NOT NULL,
  video_titulo TEXT,
  youtube_video_id TEXT,
  hora_processamento TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL,
  tentativa_numero INTEGER DEFAULT 1,
  erro_mensagem TEXT,
  upload_id INTEGER,  -- Link para yt_upload_queue
  video_url TEXT,     -- URL do Google Drive (origem)
  sheets_row_number INTEGER,  -- Linha na planilha
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_historico_channel
  ON yt_canal_upload_historico(channel_id, data DESC);

CREATE INDEX IF NOT EXISTS idx_historico_data
  ON yt_canal_upload_historico(data DESC);

CREATE INDEX IF NOT EXISTS idx_historico_status
  ON yt_canal_upload_historico(status);

-- Comentários explicativos
COMMENT ON TABLE yt_canal_upload_historico IS 'Histórico completo de todos os uploads realizados, preservando múltiplos uploads por dia';
COMMENT ON COLUMN yt_canal_upload_historico.tentativa_numero IS '1-3: tentativas automáticas, 99: upload manual forçado';
COMMENT ON COLUMN yt_canal_upload_historico.status IS 'sucesso, erro, sem_video, pendente';
COMMENT ON COLUMN yt_canal_upload_historico.video_url IS 'URL do vídeo no Google Drive (origem)';
COMMENT ON COLUMN yt_canal_upload_historico.sheets_row_number IS 'Número da linha na planilha Google Sheets';

-- Copiar dados existentes da tabela atual para o histórico
-- VERSÃO CORRIGIDA - Usa apenas colunas que existem
INSERT INTO yt_canal_upload_historico (
  channel_id,
  channel_name,
  data,
  video_titulo,
  youtube_video_id,
  hora_processamento,
  status,
  tentativa_numero,
  erro_mensagem,
  upload_id,
  video_url,
  sheets_row_number,
  created_at
)
SELECT
  channel_id,
  channel_name,
  data,
  video_titulo,
  youtube_video_id,
  COALESCE(hora_processamento, updated_at),
  COALESCE(
    CASE
      WHEN upload_realizado = true THEN 'sucesso'
      WHEN status IS NOT NULL THEN status
      WHEN erro_mensagem IS NOT NULL THEN 'erro'
      ELSE 'pendente'
    END,
    'pendente'
  ),
  COALESCE(tentativa_numero, 1),
  erro_mensagem,
  upload_id,
  video_url,
  sheets_row_number,
  created_at
FROM yt_canal_upload_diario
WHERE upload_realizado = true
  OR erro_mensagem IS NOT NULL
ON CONFLICT DO NOTHING;

-- Confirmação
SELECT COUNT(*) as registros_copiados FROM yt_canal_upload_historico;