-- ============================================
-- Script: Adicionar sistema de upload automático diário
-- Data: 02/02/2025
-- Descrição: Adiciona coluna e tabelas para controle de upload diário
-- ============================================

-- 1. ADICIONAR COLUNA upload_automatico NA TABELA yt_channels
-- Todos os canais novos terão TRUE por padrão
ALTER TABLE yt_channels
ADD COLUMN IF NOT EXISTS upload_automatico BOOLEAN DEFAULT TRUE;

-- Comentário descritivo
COMMENT ON COLUMN yt_channels.upload_automatico IS
'Se TRUE, canal participa do upload automático diário (1 vídeo/dia após coleta)';

-- Criar índice para buscar canais com upload automático rapidamente
CREATE INDEX IF NOT EXISTS idx_yt_channels_upload_automatico
ON yt_channels(upload_automatico)
WHERE upload_automatico = TRUE;

-- ============================================
-- 2. CRIAR TABELA DE LOGS DIÁRIOS
-- Registra o resumo de cada execução diária
-- ============================================
CREATE TABLE IF NOT EXISTS yt_upload_daily_logs (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    hora_inicio TIMESTAMP NOT NULL,
    hora_fim TIMESTAMP,
    tentativa_numero INTEGER DEFAULT 1, -- 1=primeira (após coleta), 2=retry 6:30, 3=retry 7:00
    total_canais INTEGER NOT NULL DEFAULT 0,
    total_elegiveis INTEGER NOT NULL DEFAULT 0, -- Canais com vídeo pronto
    total_sem_video INTEGER NOT NULL DEFAULT 0,
    total_sucesso INTEGER NOT NULL DEFAULT 0,
    total_erro INTEGER NOT NULL DEFAULT 0,
    total_pulado INTEGER NOT NULL DEFAULT 0, -- Já tinha feito upload hoje
    canais_sem_video TEXT[], -- Array com IDs dos canais
    canais_com_erro TEXT[], -- Array com IDs dos canais
    observacoes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para consultas rápidas
CREATE INDEX idx_daily_logs_data ON yt_upload_daily_logs(data DESC);
CREATE INDEX idx_daily_logs_tentativa ON yt_upload_daily_logs(tentativa_numero);

-- ============================================
-- 3. CRIAR TABELA DE CONTROLE POR CANAL/DIA
-- Um registro por canal por dia com detalhes do upload
-- ============================================
CREATE TABLE IF NOT EXISTS yt_canal_upload_diario (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    channel_name VARCHAR(255), -- Para facilitar leitura
    data DATE NOT NULL,
    upload_realizado BOOLEAN DEFAULT FALSE,
    upload_id INTEGER REFERENCES yt_upload_queue(id), -- Link para o upload na fila
    video_titulo TEXT, -- Título do vídeo para tracking
    video_url TEXT, -- URL do Google Drive
    status VARCHAR(20) NOT NULL DEFAULT 'pendente', -- pendente, sucesso, erro, sem_video, pulado
    erro_mensagem TEXT, -- Detalhes do erro se houver
    tentativa_numero INTEGER DEFAULT 1, -- Em qual tentativa conseguiu/falhou
    hora_processamento TIMESTAMP,
    sheets_row_number INTEGER, -- Linha da planilha
    youtube_video_id VARCHAR(20), -- ID do vídeo no YouTube após sucesso
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(channel_id, data) -- Garantir apenas 1 registro por canal por dia
);

-- Índices para performance
CREATE INDEX idx_canal_upload_diario_data ON yt_canal_upload_diario(data DESC);
CREATE INDEX idx_canal_upload_diario_channel ON yt_canal_upload_diario(channel_id);
CREATE INDEX idx_canal_upload_diario_status ON yt_canal_upload_diario(status);

-- ============================================
-- 4. VERIFICAR ALTERAÇÕES
-- ============================================
SELECT
    'yt_channels' as tabela,
    COUNT(*) as total_canais,
    COUNT(*) FILTER (WHERE upload_automatico = TRUE) as com_upload_automatico
FROM yt_channels

UNION ALL

SELECT
    'yt_upload_daily_logs' as tabela,
    COUNT(*) as total_registros,
    0 as placeholder
FROM yt_upload_daily_logs

UNION ALL

SELECT
    'yt_canal_upload_diario' as tabela,
    COUNT(*) as total_registros,
    0 as placeholder
FROM yt_canal_upload_diario;