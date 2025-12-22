-- SQL para corrigir os tipos de colunas no Supabase
-- Execute este script no SQL Editor do Supabase

-- Alterar colunas para aceitar valores decimais (FLOAT8)
ALTER TABLE yt_daily_metrics
ALTER COLUMN avg_view_duration_sec TYPE FLOAT8 USING avg_view_duration_sec::float8;

ALTER TABLE yt_daily_metrics
ALTER COLUMN avg_retention_pct TYPE FLOAT8 USING avg_retention_pct::float8;

ALTER TABLE yt_daily_metrics
ALTER COLUMN ctr_approx TYPE FLOAT8 USING ctr_approx::float8;

-- Verificar a estrutura após alteração
SELECT
    column_name,
    data_type,
    is_nullable
FROM
    information_schema.columns
WHERE
    table_name = 'yt_daily_metrics'
    AND column_name IN ('avg_view_duration_sec', 'avg_retention_pct', 'ctr_approx')
ORDER BY
    column_name;