-- =====================================================
-- MONETIZATION DASHBOARD - EXPANSAO DO SCHEMA
-- Rodar no SQL Editor do Supabase
-- =====================================================

-- 1. Expandir tabela de canais
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS monetization_start_date DATE;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS total_subscribers INTEGER DEFAULT 0;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS total_videos INTEGER DEFAULT 0;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- 2. Expandir tabela de metricas diarias
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS comments INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS shares INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS subscribers_gained INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS subscribers_lost INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS watch_time_minutes INTEGER DEFAULT 0;

-- 3. Criar tabela de metricas por pais
CREATE TABLE IF NOT EXISTS yt_country_metrics (
    id SERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    date DATE NOT NULL,
    country_code TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    revenue DECIMAL(10,4) DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(channel_id, date, country_code)
);

-- 4. Criar tabela de metricas por video
CREATE TABLE IF NOT EXISTS yt_video_metrics (
    id SERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    title TEXT,
    views INTEGER DEFAULT 0,
    revenue DECIMAL(10,4) DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    subscribers_gained INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(channel_id, video_id)
);

-- 5. View: Resumo diario da empresa
CREATE OR REPLACE VIEW yt_company_daily AS
SELECT
    date,
    COUNT(DISTINCT channel_id) as channels_active,
    SUM(revenue) as total_revenue,
    SUM(views) as total_views,
    SUM(COALESCE(subscribers_gained, 0) - COALESCE(subscribers_lost, 0)) as net_subscribers,
    CASE WHEN SUM(views) > 0
         THEN ROUND((SUM(revenue) / SUM(views) * 1000)::numeric, 2)
         ELSE 0 END as avg_rpm
FROM yt_daily_metrics
GROUP BY date
ORDER BY date DESC;

-- 6. View: Resumo por canal
CREATE OR REPLACE VIEW yt_channel_summary AS
SELECT
    c.channel_id,
    c.channel_name,
    c.monetization_start_date,
    c.total_subscribers,
    COUNT(DISTINCT m.date) FILTER (WHERE m.revenue > 0) as days_monetized,
    COALESCE(SUM(m.revenue), 0) as total_revenue,
    COALESCE(SUM(m.views), 0) as total_views,
    CASE WHEN COUNT(DISTINCT m.date) FILTER (WHERE m.revenue > 0) > 0
         THEN ROUND((SUM(m.revenue) / COUNT(DISTINCT m.date) FILTER (WHERE m.revenue > 0))::numeric, 2)
         ELSE 0 END as avg_daily_revenue,
    CASE WHEN SUM(m.views) > 0
         THEN ROUND((SUM(m.revenue) / SUM(m.views) * 1000)::numeric, 2)
         ELSE 0 END as avg_rpm
FROM yt_channels c
LEFT JOIN yt_daily_metrics m ON c.channel_id = m.channel_id
GROUP BY c.channel_id, c.channel_name, c.monetization_start_date, c.total_subscribers;

-- 7. View: Metricas dos ultimos 7 dias
CREATE OR REPLACE VIEW yt_last_7_days AS
SELECT
    channel_id,
    SUM(revenue) as revenue_7d,
    SUM(views) as views_7d,
    SUM(COALESCE(subscribers_gained, 0) - COALESCE(subscribers_lost, 0)) as net_subs_7d,
    ROUND(AVG(revenue)::numeric, 2) as avg_daily_revenue,
    CASE WHEN SUM(views) > 0
         THEN ROUND((SUM(revenue) / SUM(views) * 1000)::numeric, 2)
         ELSE 0 END as rpm_7d
FROM yt_daily_metrics
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY channel_id;

-- 8. View: Projecao mensal por canal
CREATE OR REPLACE VIEW yt_monthly_projection AS
SELECT
    channel_id,
    avg_daily_revenue * 30 as projected_monthly_revenue,
    views_7d / 7 * 30 as projected_monthly_views
FROM yt_last_7_days;

-- 9. Habilitar RLS (Row Level Security) - opcional
-- ALTER TABLE yt_country_metrics ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE yt_video_metrics ENABLE ROW LEVEL SECURITY;

-- 10. Criar indices para performance
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON yt_daily_metrics(date);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_channel ON yt_daily_metrics(channel_id);
CREATE INDEX IF NOT EXISTS idx_country_metrics_date ON yt_country_metrics(date);
CREATE INDEX IF NOT EXISTS idx_video_metrics_channel ON yt_video_metrics(channel_id);

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
