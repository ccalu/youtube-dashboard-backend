-- =====================================================
-- Migration 035: Fix MV inscritos - Solucao Definitiva
-- Data: 2026-03-19
-- Problema: MV usava WHERE data_coleta = CURRENT_DATE
--           que congela no momento do refresh. Se refresh
--           acontece antes da coleta, em hora errada, ou
--           falha — inscritos fica zerado ou desatualizado.
-- Solucao: Usar ROW_NUMBER() para pegar SEMPRE os dados
--          mais recentes por canal + usar inscritos_diff
--          pre-calculado pelo collector.
-- =====================================================

-- 1. Recriar MV com logica resiliente
DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_completo;

CREATE MATERIALIZED VIEW mv_dashboard_completo AS
WITH ranked AS (
    SELECT
        canal_id,
        inscritos,
        inscritos_diff,
        views_60d,
        views_30d,
        views_15d,
        views_7d,
        videos_publicados_7d,
        engagement_rate,
        total_views,
        data_coleta,
        ROW_NUMBER() OVER (PARTITION BY canal_id ORDER BY data_coleta DESC) as rn
    FROM dados_canais_historico
),
dados_latest AS (
    SELECT * FROM ranked WHERE rn = 1
),
dados_previous AS (
    SELECT canal_id, inscritos as inscritos_prev FROM ranked WHERE rn = 2
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
    COALESCE(dl.inscritos, 0) as inscritos,
    -- Prioridade: inscritos_diff pre-calculado pelo collector (nosso channels)
    -- Fallback: calculo manual latest vs previous (minerado channels)
    COALESCE(
        dl.inscritos_diff,
        CASE WHEN dl.inscritos IS NOT NULL AND dp.inscritos_prev IS NOT NULL
             THEN dl.inscritos - dp.inscritos_prev
             ELSE NULL
        END
    ) as inscritos_diff,
    COALESCE(dl.views_60d, 0) as views_60d,
    COALESCE(dl.views_30d, 0) as views_30d,
    COALESCE(dl.views_15d, 0) as views_15d,
    COALESCE(dl.views_7d, 0) as views_7d,
    COALESCE(c.video_count, 0) as videos_30d,
    COALESCE(dl.videos_publicados_7d, 0) as videos_publicados_7d,
    COALESCE(dl.engagement_rate, 0.00) as engagement_rate,
    COALESCE(dl.total_views, 0) as total_views,
    COALESCE(dl.total_views, 0) as total_video_views,
    c.ultima_coleta,
    c.coleta_falhas_consecutivas,
    c.coleta_ultimo_erro,
    c.coleta_ultimo_sucesso,
    dl.data_coleta as data_ultimo_historico,
    c.melhor_dia_semana,
    c.melhor_hora,
    c.frequencia_semanal,
    c.ultimo_comentario_coletado,
    c.total_comentarios_coletados,
    c.data_adicionado,
    c.data_adicionado as created_at,
    c.published_at
FROM canais_monitorados c
LEFT JOIN dados_latest dl ON c.id = dl.canal_id
LEFT JOIN dados_previous dp ON c.id = dp.canal_id
WHERE c.status = 'ativo';

-- 2. Indices (mesmos da migration 021 + unique para CONCURRENTLY da 030)
CREATE UNIQUE INDEX idx_mv_dashboard_canal_id_unique ON mv_dashboard_completo(canal_id);
CREATE INDEX idx_mv_dashboard_id ON mv_dashboard_completo(id);
CREATE INDEX idx_mv_dashboard_tipo ON mv_dashboard_completo(tipo);
CREATE INDEX idx_mv_dashboard_subnicho ON mv_dashboard_completo(subnicho);
CREATE INDEX idx_mv_dashboard_inscritos_diff ON mv_dashboard_completo(inscritos_diff DESC NULLS LAST);

-- 3. Refresh inicial
REFRESH MATERIALIZED VIEW mv_dashboard_completo;
ANALYZE mv_dashboard_completo;

-- 4. Verificacao
SELECT 'Migration 035 OK' as status,
       COUNT(*) as total_canais,
       COUNT(inscritos_diff) as canais_com_diff,
       SUM(CASE WHEN inscritos > 0 THEN 1 ELSE 0 END) as canais_com_inscritos
FROM mv_dashboard_completo;
