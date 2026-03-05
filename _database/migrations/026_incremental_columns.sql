-- Migration 026: Adicionar colunas incrementais para agentes Copy e Satisfacao
-- analyzed_video_data: snapshot JSONB dos videos analisados (para detectar novos no proximo run)
-- run_number: contador sequencial por canal (#1, #2, #3...)

ALTER TABLE copy_analysis_runs
  ADD COLUMN IF NOT EXISTS analyzed_video_data JSONB,
  ADD COLUMN IF NOT EXISTS run_number INTEGER DEFAULT 1;

ALTER TABLE satisfaction_analysis_runs
  ADD COLUMN IF NOT EXISTS analyzed_video_data JSONB,
  ADD COLUMN IF NOT EXISTS run_number INTEGER DEFAULT 1;
