-- =====================================================
-- Migration 021: Add video_count to canais_monitorados
-- Data: 2026-03-02
-- Objetivo: Salvar total de videos do canal (YouTube API videoCount)
--           para exibir no Mission Control e Dashboard
-- =====================================================

-- 1. Adicionar coluna video_count
ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS video_count INTEGER DEFAULT 0;

-- 2. Comentario na coluna
COMMENT ON COLUMN canais_monitorados.video_count IS 'Total de videos no canal (YouTube API statistics.videoCount)';

-- 3. Recriar MV com video_count
DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_completo;

CREATE MATERIALIZED VIEW mv_dashboard_completo AS
WITH dados_hoje AS (
    SELECT DISTINCT ON (canal_id)
        canal_id,
        inscritos as inscritos_hoje,
        views_60d,
        views_30d,
        views_15d,
        views_7d,
        videos_publicados_7d,
        engagement_rate,
        total_views,
        data_coleta
    FROM dados_canais_historico
    WHERE data_coleta = CURRENT_DATE
    ORDER BY canal_id
),
dados_ontem AS (
    SELECT DISTINCT ON (canal_id)
        canal_id,
        inscritos as inscritos_ontem
    FROM dados_canais_historico
    WHERE data_coleta = (CURRENT_DATE - INTERVAL '1 day')::date
    ORDER BY canal_id
)
SELECT
    c.id,
    c.id as canal_id,
    c.nome_canal,
    c.nome_canal as nome,
    c.url_canal,
    c.custom_url,
    c.tipo,
    c.subnicho,
    c.lingua,
    c.nicho,
    c.status,
    COALESCE(dh.inscritos_hoje, 0) as inscritos,
    CASE
        WHEN dh.inscritos_hoje IS NOT NULL AND d_ontem.inscritos_ontem IS NOT NULL
        THEN dh.inscritos_hoje - d_ontem.inscritos_ontem
        ELSE NULL
    END as inscritos_diff,
    COALESCE(dh.views_60d, 0) as views_60d,
    COALESCE(dh.views_30d, 0) as views_30d,
    COALESCE(dh.views_15d, 0) as views_15d,
    COALESCE(dh.views_7d, 0) as views_7d,
    COALESCE(c.video_count, 0) as videos_30d,  -- Total de videos do canal (YouTube API)
    COALESCE(dh.videos_publicados_7d, 0) as videos_publicados_7d,
    COALESCE(dh.engagement_rate, 0.00) as engagement_rate,
    COALESCE(dh.total_views, 0) as total_views,
    COALESCE(dh.total_views, 0) as total_video_views,
    c.ultima_coleta,
    c.coleta_falhas_consecutivas,
    c.coleta_ultimo_erro,
    c.coleta_ultimo_sucesso,
    dh.data_coleta as data_ultimo_historico,
    c.melhor_dia_semana,
    c.melhor_hora,
    c.frequencia_semanal,
    c.ultimo_comentario_coletado,
    c.total_comentarios_coletados,
    c.data_adicionado,
    c.data_adicionado as created_at,
    c.published_at
FROM canais_monitorados c
LEFT JOIN dados_hoje dh ON c.id = dh.canal_id
LEFT JOIN dados_ontem d_ontem ON c.id = d_ontem.canal_id
WHERE c.status = 'ativo';

-- 4. Indices
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_id ON mv_dashboard_completo(id);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_canal_id ON mv_dashboard_completo(canal_id);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_tipo ON mv_dashboard_completo(tipo);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_subnicho ON mv_dashboard_completo(subnicho);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_inscritos_diff ON mv_dashboard_completo(inscritos_diff DESC NULLS LAST);

-- 5. Refresh
REFRESH MATERIALIZED VIEW mv_dashboard_completo;
ANALYZE mv_dashboard_completo;

-- 6. Verificacao
SELECT 'Migration 021 OK' as status, COUNT(*) as canais FROM mv_dashboard_completo;
