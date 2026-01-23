-- ========================================================
-- MATERIALIZED VIEW PARA DASHBOARD ULTRA-RÁPIDO
-- ========================================================
-- Esta MV consolida TODOS os dados necessários para o dashboard
-- em uma única tabela pré-calculada, eliminando JOINs e paginação.
--
-- PERFORMANCE ESPERADA:
-- Antes: ~3000ms (paginação de 10k+ registros)
-- Depois: < 100ms (query direta na MV)
-- Com cache: < 1ms (servido da memória)
-- ========================================================

-- PASSO 1: Dropar MV antiga se existir (para recriar limpa)
DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_completo CASCADE;

-- PASSO 2: Criar a Materialized View com TODOS os dados necessários
CREATE MATERIALIZED VIEW mv_dashboard_completo AS
WITH
-- Dados mais recentes de cada canal (hoje ou último disponível)
latest_data AS (
    SELECT DISTINCT ON (canal_id)
        canal_id,
        inscritos,
        views_totais,
        videos_publicados,
        data_coleta
    FROM dados_canais_historico
    WHERE data_coleta >= CURRENT_DATE - INTERVAL '7 days'
    ORDER BY canal_id, data_coleta DESC
),
-- Dados de ontem (para calcular diff diário)
yesterday_data AS (
    SELECT DISTINCT ON (canal_id)
        canal_id,
        inscritos as inscritos_ontem,
        views_totais as views_ontem
    FROM dados_canais_historico
    WHERE data_coleta = (
        SELECT MAX(data_coleta)
        FROM dados_canais_historico
        WHERE data_coleta < CURRENT_DATE
    )
    ORDER BY canal_id, data_coleta DESC
),
-- Dados de 7 dias atrás
week_ago_data AS (
    SELECT DISTINCT ON (canal_id)
        canal_id,
        inscritos as inscritos_7d,
        views_totais as views_7d
    FROM dados_canais_historico
    WHERE data_coleta >= CURRENT_DATE - INTERVAL '7 days'
        AND data_coleta <= CURRENT_DATE - INTERVAL '6 days'
    ORDER BY canal_id, data_coleta ASC
),
-- Dados de 30 dias atrás
month_ago_data AS (
    SELECT DISTINCT ON (canal_id)
        canal_id,
        inscritos as inscritos_30d,
        views_totais as views_30d
    FROM dados_canais_historico
    WHERE data_coleta >= CURRENT_DATE - INTERVAL '31 days'
        AND data_coleta <= CURRENT_DATE - INTERVAL '29 days'
    ORDER BY canal_id, data_coleta ASC
),
-- Dados de 35 dias atrás (para compatibilidade com código atual)
month35_ago_data AS (
    SELECT DISTINCT ON (canal_id)
        canal_id,
        inscritos as inscritos_35d,
        views_totais as views_35d
    FROM dados_canais_historico
    WHERE data_coleta >= CURRENT_DATE - INTERVAL '36 days'
        AND data_coleta <= CURRENT_DATE - INTERVAL '34 days'
    ORDER BY canal_id, data_coleta ASC
)
-- Query principal que junta TUDO
SELECT
    -- Informações básicas do canal
    c.id as canal_id,
    c.nome_canal,
    c.canal_handle,
    c.tipo,
    c.subnicho,
    c.lingua,
    c.pais,
    c.status,
    c.url_canal,
    c.thumbnail_url,
    c.descricao,
    c.data_adicao,
    c.ultima_verificacao,
    c.coleta_ativa,
    c.notificacoes_ativas,
    c.limite_notificacao,
    c.dias_notificacao,
    c.views_referencia,

    -- Métricas atuais (latest disponível)
    COALESCE(ld.inscritos, 0) as inscritos,
    COALESCE(ld.views_totais, 0) as views_totais,
    COALESCE(ld.videos_publicados, 0) as videos_publicados,
    ld.data_coleta as ultima_coleta,

    -- Diferenças calculadas (growth)
    COALESCE(ld.inscritos - yd.inscritos_ontem, 0) as inscritos_diff,
    COALESCE(ld.views_totais - yd.views_ontem, 0) as views_diff_24h,

    -- Growth de 7 dias
    COALESCE(ld.inscritos - wd.inscritos_7d, 0) as inscritos_diff_7d,
    COALESCE(ld.views_totais - wd.views_7d, 0) as views_diff_7d,
    CASE
        WHEN wd.views_7d > 0 THEN
            ROUND(((ld.views_totais - wd.views_7d)::NUMERIC / wd.views_7d * 100), 2)
        ELSE 0
    END as views_growth_7d,

    -- Growth de 30 dias
    COALESCE(ld.inscritos - md.inscritos_30d, 0) as inscritos_diff_30d,
    COALESCE(ld.views_totais - md.views_30d, 0) as views_diff_30d,
    CASE
        WHEN md.views_30d > 0 THEN
            ROUND(((ld.views_totais - md.views_30d)::NUMERIC / md.views_30d * 100), 2)
        ELSE 0
    END as views_growth_30d,

    -- Dados históricos para compatibilidade
    COALESCE(wd.inscritos_7d, 0) as inscritos_7d_atras,
    COALESCE(wd.views_7d, 0) as views_7d_atras,
    COALESCE(md.inscritos_30d, 0) as inscritos_30d_atras,
    COALESCE(md.views_30d, 0) as views_30d_atras,
    COALESCE(m35.inscritos_35d, 0) as inscritos_35d_atras,
    COALESCE(m35.views_35d, 0) as views_35d_atras,

    -- Estatísticas de vídeos (da MV existente)
    COALESCE(vs.total_videos, 0) as total_videos,
    COALESCE(vs.total_views, 0) as total_video_views,

    -- Timestamp de criação da MV (para debug/cache)
    NOW() as mv_updated_at

FROM canais_monitorados c
LEFT JOIN latest_data ld ON c.id = ld.canal_id
LEFT JOIN yesterday_data yd ON c.id = yd.canal_id
LEFT JOIN week_ago_data wd ON c.id = wd.canal_id
LEFT JOIN month_ago_data md ON c.id = md.canal_id
LEFT JOIN month35_ago_data m35 ON c.id = m35.canal_id
LEFT JOIN mv_canal_video_stats vs ON c.id = vs.canal_id
WHERE c.status = 'ativo';

-- PASSO 3: Criar índice único para permitir CONCURRENT refresh
CREATE UNIQUE INDEX idx_mv_dashboard_canal_id
ON mv_dashboard_completo (canal_id);

-- Índices adicionais para filtros comuns
CREATE INDEX idx_mv_dashboard_tipo
ON mv_dashboard_completo (tipo);

CREATE INDEX idx_mv_dashboard_subnicho
ON mv_dashboard_completo (subnicho);

CREATE INDEX idx_mv_dashboard_lingua
ON mv_dashboard_completo (lingua);

CREATE INDEX idx_mv_dashboard_tipo_subnicho
ON mv_dashboard_completo (tipo, subnicho);

-- PASSO 4: Criar função para refresh das MVs após coleta
CREATE OR REPLACE FUNCTION refresh_all_dashboard_mvs()
RETURNS TABLE(
    mv_name TEXT,
    status TEXT,
    rows_affected INTEGER,
    execution_time INTERVAL
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    row_count INTEGER;
BEGIN
    -- Log início
    RAISE NOTICE 'Iniciando refresh das Materialized Views às %', NOW();

    -- Refresh MV de vídeos (já existente)
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_canal_video_stats;
    end_time := clock_timestamp();
    GET DIAGNOSTICS row_count = ROW_COUNT;

    RETURN QUERY
    SELECT
        'mv_canal_video_stats'::TEXT,
        'SUCCESS'::TEXT,
        row_count,
        (end_time - start_time);

    -- Refresh MV principal do dashboard
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;
    end_time := clock_timestamp();

    -- Contar linhas da MV
    SELECT COUNT(*)::INTEGER INTO row_count
    FROM mv_dashboard_completo;

    RETURN QUERY
    SELECT
        'mv_dashboard_completo'::TEXT,
        'SUCCESS'::TEXT,
        row_count,
        (end_time - start_time);

    -- Log conclusão
    RAISE NOTICE 'Refresh concluído com sucesso às %', NOW();

EXCEPTION WHEN OTHERS THEN
    -- Em caso de erro, registrar mas não falhar
    RAISE WARNING 'Erro no refresh: %', SQLERRM;
    RETURN QUERY
    SELECT
        'ERROR'::TEXT,
        SQLERRM::TEXT,
        0,
        INTERVAL '0';
END;
$$;

-- PASSO 5: Fazer o primeiro refresh (pode demorar ~30-60 segundos)
-- Comentado para você executar manualmente quando quiser
-- REFRESH MATERIALIZED VIEW mv_dashboard_completo;

-- PASSO 6: Verificar que funcionou
SELECT
    'Total de canais na MV' as metrica,
    COUNT(*) as valor
FROM mv_dashboard_completo
UNION ALL
SELECT
    'Canais tipo=nosso',
    COUNT(*)
FROM mv_dashboard_completo
WHERE tipo = 'nosso'
UNION ALL
SELECT
    'Canais tipo=minerado',
    COUNT(*)
FROM mv_dashboard_completo
WHERE tipo = 'minerado'
UNION ALL
SELECT
    'Total views acumuladas',
    SUM(views_totais)::BIGINT
FROM mv_dashboard_completo;

-- ========================================================
-- INSTRUÇÕES DE USO
-- ========================================================
-- 1. Execute TODO este SQL no Supabase SQL Editor
-- 2. O primeiro refresh pode demorar 30-60 segundos
-- 3. Depois disso, queries serão < 100ms
-- 4. Refresh automático após cada coleta (5h AM)
--
-- TESTE DE PERFORMANCE:
-- Execute: EXPLAIN ANALYZE SELECT * FROM mv_dashboard_completo LIMIT 10;
-- Deve mostrar: Execution Time < 1ms
-- ========================================================