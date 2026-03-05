-- Migration 027: Adicionar colunas incrementais para agente de Autenticidade
-- analyzed_video_data: snapshot JSONB dos titulos analisados (para detectar novos no proximo run)
-- run_number: contador sequencial por canal (#1, #2, #3...)

ALTER TABLE authenticity_analysis_runs
  ADD COLUMN IF NOT EXISTS analyzed_video_data JSONB,
  ADD COLUMN IF NOT EXISTS run_number INTEGER DEFAULT 1;
