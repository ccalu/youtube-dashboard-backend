-- =====================================================
-- Migration 030: Fix MV refresh - unique index + robust RPC
-- Data: 2026-03-10
-- Problema: REFRESH CONCURRENTLY falhava silenciosamente
--           por falta de unique index, congelando dados por dias
-- =====================================================

-- 1. Criar unique index (necessario para REFRESH CONCURRENTLY)
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dashboard_canal_id_unique
ON mv_dashboard_completo(canal_id);

-- 2. Refresh imediato
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;

-- 3. Atualizar function RPC com fallback robusto
CREATE OR REPLACE FUNCTION refresh_all_dashboard_mvs()
RETURNS SETOF json AS $$
DECLARE
    start_ts TIMESTAMPTZ;
    elapsed TEXT;
    row_count INT;
BEGIN
    -- mv_dashboard_completo
    start_ts := clock_timestamp();
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;
    EXCEPTION WHEN OTHERS THEN
        -- Fallback: refresh normal (bloqueia leituras ~2s mas SEMPRE funciona)
        REFRESH MATERIALIZED VIEW mv_dashboard_completo;
    END;
    elapsed := round(extract(epoch from clock_timestamp() - start_ts)::numeric, 2) || 's';
    SELECT COUNT(*) INTO row_count FROM mv_dashboard_completo;
    RETURN NEXT json_build_object(
        'mv_name', 'mv_dashboard_completo',
        'status', 'SUCCESS',
        'rows_affected', row_count,
        'execution_time', elapsed
    );

    -- mv_canal_video_stats (se existir)
    start_ts := clock_timestamp();
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_canal_video_stats;
    EXCEPTION WHEN OTHERS THEN
        BEGIN
            REFRESH MATERIALIZED VIEW mv_canal_video_stats;
        EXCEPTION WHEN OTHERS THEN
            RETURN NEXT json_build_object(
                'mv_name', 'mv_canal_video_stats',
                'status', 'SKIPPED',
                'rows_affected', 0,
                'execution_time', '0s'
            );
            RETURN;
        END;
    END;
    elapsed := round(extract(epoch from clock_timestamp() - start_ts)::numeric, 2) || 's';
    SELECT COUNT(*) INTO row_count FROM mv_canal_video_stats;
    RETURN NEXT json_build_object(
        'mv_name', 'mv_canal_video_stats',
        'status', 'SUCCESS',
        'rows_affected', row_count,
        'execution_time', elapsed
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Verificar
SELECT 'Migration 030 OK' as status,
       canal_id, inscritos, inscritos_diff
FROM mv_dashboard_completo
WHERE canal_id IN (993, 1029);
