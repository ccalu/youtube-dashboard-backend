-- Add per-note stage tracking for Kanban notes
ALTER TABLE public.kanban_notes
ADD COLUMN IF NOT EXISTS stage_id text;

-- Index for fast board rendering by channel + stage
CREATE INDEX IF NOT EXISTS idx_kanban_notes_canal_stage_pos
ON public.kanban_notes (canal_id, stage_id, position);

-- Backfill stage_id from the channel current Kanban status when available
UPDATE public.kanban_notes n
SET stage_id = cm.kanban_status
FROM public.canais_monitorados cm
WHERE n.stage_id IS NULL
  AND n.canal_id = cm.id
  AND cm.kanban_status IS NOT NULL;

-- Safety fallback for any remaining nulls
UPDATE public.kanban_notes
SET stage_id = 'em_teste_inicial'
WHERE stage_id IS NULL;