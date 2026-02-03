-- Migration: Adicionar campos para sistema de monetização
-- Data: 2025-12-10
-- Descrição: Adiciona total_views e campos de estimativa/analytics

-- 1. Adicionar total_views em dados_canais_historico
-- Usado para calcular views diárias (total_hoje - total_ontem)
ALTER TABLE dados_canais_historico
ADD COLUMN IF NOT EXISTS total_views BIGINT;

COMMENT ON COLUMN dados_canais_historico.total_views IS
'Total de views do canal desde sempre. Usado para calcular views de 24h.';

-- 2. Adicionar campos em yt_daily_metrics
-- is_estimate: marca se revenue é estimado (TRUE) ou real (FALSE)
ALTER TABLE yt_daily_metrics
ADD COLUMN IF NOT EXISTS is_estimate BOOLEAN DEFAULT FALSE;

-- Campos de analytics (YouTube Analytics API)
ALTER TABLE yt_daily_metrics
ADD COLUMN IF NOT EXISTS avg_retention_pct DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS avg_view_duration_sec INTEGER,
ADD COLUMN IF NOT EXISTS ctr_approx DECIMAL(5,2);

-- Comentários
COMMENT ON COLUMN yt_daily_metrics.is_estimate IS
'TRUE = revenue estimado (RPM × views), FALSE = revenue real da API';

COMMENT ON COLUMN yt_daily_metrics.avg_retention_pct IS
'Porcentagem média de retenção dos vídeos (YouTube Analytics)';

COMMENT ON COLUMN yt_daily_metrics.avg_view_duration_sec IS
'Tempo médio de visualização em segundos (YouTube Analytics)';

COMMENT ON COLUMN yt_daily_metrics.ctr_approx IS
'CTR aproximado: (views / impressions) × 100 (YouTube Analytics)';

-- 3. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_yt_daily_metrics_estimate
ON yt_daily_metrics(channel_id, is_estimate);

CREATE INDEX IF NOT EXISTS idx_yt_daily_metrics_date_channel
ON yt_daily_metrics(date DESC, channel_id);

CREATE INDEX IF NOT EXISTS idx_dados_canais_historico_date
ON dados_canais_historico(data_coleta DESC, canal_id);

-- 4. Marcar todos os registros existentes como reais (não estimados)
UPDATE yt_daily_metrics
SET is_estimate = FALSE
WHERE is_estimate IS NULL;

-- Sucesso!
SELECT 'Migration concluída com sucesso!' as status;
