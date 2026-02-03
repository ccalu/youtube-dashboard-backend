-- =====================================================
-- FIX 100% CORRETO - BASEADO NOS CAMPOS REAIS DO SUPABASE
-- Data: 26/01/2026
-- Versão: DEFINITIVA - Testado com campos reais
-- =====================================================

-- 1. DROPAR A MV EXISTENTE
DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_completo;

-- 2. CRIAR MV COM CAMPOS QUE REALMENTE EXISTEM
CREATE MATERIALIZED VIEW mv_dashboard_completo AS
WITH dados_hoje AS (
    -- Pegar dados de HOJE
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
    -- Pegar dados de ONTEM
    SELECT DISTINCT ON (canal_id)
        canal_id,
        inscritos as inscritos_ontem
    FROM dados_canais_historico
    WHERE data_coleta = (CURRENT_DATE - INTERVAL '1 day')::date
    ORDER BY canal_id
)
SELECT
    -- IDs
    c.id,
    c.id as canal_id,

    -- Informações do canal
    c.nome_canal,
    c.nome_canal as nome,  -- Alias para compatibilidade
    c.url_canal,
    c.custom_url,
    c.tipo,
    c.subnicho,
    c.lingua,
    c.nicho,
    c.status,

    -- Métricas principais
    COALESCE(dh.inscritos_hoje, 0) as inscritos,

    -- ⭐ CÁLCULO PRINCIPAL: inscritos_diff
    CASE
        WHEN dh.inscritos_hoje IS NOT NULL AND d_ontem.inscritos_ontem IS NOT NULL
        THEN dh.inscritos_hoje - d_ontem.inscritos_ontem
        ELSE NULL
    END as inscritos_diff,

    -- Views (todos os períodos)
    COALESCE(dh.views_60d, 0) as views_60d,
    COALESCE(dh.views_30d, 0) as views_30d,
    COALESCE(dh.views_15d, 0) as views_15d,
    COALESCE(dh.views_7d, 0) as views_7d,

    -- Outras métricas
    COALESCE(dh.videos_publicados_7d, 0) as videos_30d,  -- Alias para compatibilidade
    COALESCE(dh.videos_publicados_7d, 0) as videos_publicados_7d,
    COALESCE(dh.engagement_rate, 0.00) as engagement_rate,
    COALESCE(dh.total_views, 0) as total_views,
    COALESCE(dh.total_views, 0) as total_video_views,  -- Alias

    -- Informações de coleta
    c.ultima_coleta,
    c.coleta_falhas_consecutivas,
    c.coleta_ultimo_erro,
    c.coleta_ultimo_sucesso,
    dh.data_coleta as data_ultimo_historico,

    -- Análise de postagem
    c.melhor_dia_semana,
    c.melhor_hora,
    c.frequencia_semanal,

    -- Comentários
    c.ultimo_comentario_coletado,
    c.total_comentarios_coletados,

    -- Timestamps
    c.data_adicionado,
    c.data_adicionado as created_at,  -- Alias para compatibilidade
    c.published_at

FROM canais_monitorados c
LEFT JOIN dados_hoje dh ON c.id = dh.canal_id
LEFT JOIN dados_ontem d_ontem ON c.id = d_ontem.canal_id
WHERE c.status = 'ativo';

-- 3. CRIAR ÍNDICES
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_id ON mv_dashboard_completo(id);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_canal_id ON mv_dashboard_completo(canal_id);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_tipo ON mv_dashboard_completo(tipo);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_subnicho ON mv_dashboard_completo(subnicho);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_inscritos_diff ON mv_dashboard_completo(inscritos_diff DESC NULLS LAST);

-- 4. ATUALIZAR ESTATÍSTICAS
ANALYZE mv_dashboard_completo;

-- 5. VERIFICAÇÃO
SELECT
    'MV criada com sucesso!' as status,
    COUNT(*) as total_canais,
    COUNT(inscritos_diff) as canais_com_diff,
    COUNT(*) - COUNT(inscritos_diff) as canais_sem_diff
FROM mv_dashboard_completo;

-- 6. EXEMPLOS
SELECT
    nome_canal,
    tipo,
    inscritos,
    inscritos_diff,
    CASE
        WHEN inscritos_diff IS NULL THEN 'Sem dados'
        WHEN inscritos_diff > 0 THEN 'Ganhou'
        WHEN inscritos_diff < 0 THEN 'Perdeu'
        ELSE 'Manteve'
    END as status_diff,
    ultima_coleta
FROM mv_dashboard_completo
WHERE tipo = 'nosso'
ORDER BY
    CASE WHEN inscritos_diff IS NULL THEN 1 ELSE 0 END,
    ABS(inscritos_diff) DESC NULLS LAST
LIMIT 20;