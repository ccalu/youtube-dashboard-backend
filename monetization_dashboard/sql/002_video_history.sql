-- =====================================================
-- HISTORICO DIARIO POR VIDEO
-- Rodar no SQL Editor do Supabase
-- =====================================================

-- 1. Criar nova tabela para historico de videos
CREATE TABLE IF NOT EXISTS yt_video_daily (
    id SERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    date DATE NOT NULL,
    title TEXT,
    views INTEGER DEFAULT 0,
    revenue DECIMAL(10,4) DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    subscribers_gained INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(channel_id, video_id, date)
);

-- 2. Criar indice para performance
CREATE INDEX IF NOT EXISTS idx_video_daily_date ON yt_video_daily(date);
CREATE INDEX IF NOT EXISTS idx_video_daily_video ON yt_video_daily(video_id);
CREATE INDEX IF NOT EXISTS idx_video_daily_channel ON yt_video_daily(channel_id);

-- 3. View: Crescimento de um video nos ultimos 7 dias
CREATE OR REPLACE VIEW yt_video_growth AS
SELECT
    video_id,
    title,
    channel_id,
    MIN(date) as first_date,
    MAX(date) as last_date,
    MAX(views) - MIN(views) as views_growth,
    MAX(revenue) - MIN(revenue) as revenue_growth,
    COUNT(*) as days_tracked
FROM yt_video_daily
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY video_id, title, channel_id;

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
