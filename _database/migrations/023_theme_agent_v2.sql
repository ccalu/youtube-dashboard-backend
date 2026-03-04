-- Migration 023: Theme Agent V2 (Temas + Motores Psicologicos)
-- Adiciona colunas para deteccao incremental, numeracao de relatorios e output da LLM TEMAS

ALTER TABLE theme_analysis_runs
  ADD COLUMN IF NOT EXISTS analyzed_video_data JSONB,
  ADD COLUMN IF NOT EXISTS run_number INTEGER DEFAULT 1,
  ADD COLUMN IF NOT EXISTS themes_json JSONB;

-- analyzed_video_data: snapshot de cada video analisado
--   {video_id: {views, ctr, tema, hipoteses: [{motor, explicacao}]}}
-- run_number: sequencial por canal (#1, #2, #3...)
-- themes_json: output raw da LLM TEMAS (JSON completo)
