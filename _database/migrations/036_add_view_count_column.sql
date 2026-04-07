-- Migration 036: Add view_count column to dados_canais_historico
-- Used to calculate views_7d/15d/30d as deltas (total views received in period)
-- Instead of the old calculation (sum of views of videos published in period)

ALTER TABLE dados_canais_historico
ADD COLUMN IF NOT EXISTS view_count BIGINT;

COMMENT ON COLUMN dados_canais_historico.view_count IS 'Total lifetime view count from YouTube API at time of collection. Used to calculate views_Nd deltas.';
