-- Criar tabela para logs de coleta de comentários
CREATE TABLE IF NOT EXISTS comments_collection_logs (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    tipo TEXT NOT NULL, -- 'automatic' ou 'manual'
    canais_processados INTEGER DEFAULT 0,
    canais_com_sucesso INTEGER DEFAULT 0,
    canais_com_erro INTEGER DEFAULT 0,
    total_comentarios INTEGER DEFAULT 0,
    comentarios_analisados INTEGER DEFAULT 0,
    comentarios_nao_analisados INTEGER DEFAULT 0,
    detalhes_erros JSONB DEFAULT '[]'::jsonb,
    detalhes_sucesso JSONB DEFAULT '[]'::jsonb,
    tempo_execucao DECIMAL(10,2) DEFAULT 0,
    custo_gpt_estimado DECIMAL(10,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_comments_logs_timestamp ON comments_collection_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_comments_logs_tipo ON comments_collection_logs(tipo);
CREATE INDEX IF NOT EXISTS idx_comments_logs_created ON comments_collection_logs(created_at DESC);

-- Comentários sobre a estrutura
COMMENT ON TABLE comments_collection_logs IS 'Logs detalhados de cada coleta de comentários do YouTube';
COMMENT ON COLUMN comments_collection_logs.id IS 'UUID único da coleta';
COMMENT ON COLUMN comments_collection_logs.tipo IS 'Tipo de coleta: automatic (agendada) ou manual (forçada)';
COMMENT ON COLUMN comments_collection_logs.detalhes_erros IS 'Array JSON com detalhes dos canais que falharam';
COMMENT ON COLUMN comments_collection_logs.detalhes_sucesso IS 'Array JSON com detalhes dos canais processados com sucesso';
COMMENT ON COLUMN comments_collection_logs.tempo_execucao IS 'Tempo total de execução em segundos';
COMMENT ON COLUMN comments_collection_logs.custo_gpt_estimado IS 'Custo estimado de uso do GPT em USD';