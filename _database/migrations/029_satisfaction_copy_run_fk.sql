-- Migration 029: Adicionar copy_run_id FK em satisfaction_analysis_runs
-- Mesmo padrao do motor_analysis_runs.theme_run_id

ALTER TABLE satisfaction_analysis_runs
ADD COLUMN IF NOT EXISTS copy_run_id INTEGER REFERENCES copy_analysis_runs(id);

CREATE INDEX IF NOT EXISTS idx_satisfaction_runs_copy_run_id
    ON satisfaction_analysis_runs(copy_run_id);
