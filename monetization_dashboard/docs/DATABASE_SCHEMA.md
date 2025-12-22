# Schema do Banco de Dados - Monetization Dashboard

## Tabelas

### 1. yt_channels (já existe, vamos expandir)
```sql
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS monetization_start_date DATE;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS total_subscribers INTEGER;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS total_videos INTEGER;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
```

### 2. yt_daily_metrics (já existe, vamos expandir)
```sql
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS comments INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS shares INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS subscribers_gained INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS subscribers_lost INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS watch_time_minutes INTEGER DEFAULT 0;
ALTER TABLE yt_daily_metrics ADD COLUMN IF NOT EXISTS avg_view_duration DECIMAL(10,2) DEFAULT 0;
```

### 3. yt_country_metrics (NOVA)
```sql
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
```

### 4. yt_video_metrics (NOVA - opcional)
```sql
CREATE TABLE IF NOT EXISTS yt_video_metrics (
    id SERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    date DATE NOT NULL,
    title TEXT,
    views INTEGER DEFAULT 0,
    revenue DECIMAL(10,4) DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    avg_view_duration DECIMAL(10,2) DEFAULT 0,
    subscribers_gained INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(channel_id, video_id, date)
);
```

### 5. Views Úteis

```sql
-- Resumo diário da empresa (todos os canais)
CREATE OR REPLACE VIEW yt_company_daily AS
SELECT
    date,
    COUNT(DISTINCT channel_id) as channels_active,
    SUM(revenue) as total_revenue,
    SUM(views) as total_views,
    SUM(subscribers_gained - subscribers_lost) as net_subscribers,
    CASE WHEN SUM(views) > 0
         THEN SUM(revenue) / SUM(views) * 1000
         ELSE 0 END as avg_rpm
FROM yt_daily_metrics
GROUP BY date
ORDER BY date DESC;

-- Resumo por canal
CREATE OR REPLACE VIEW yt_channel_summary AS
SELECT
    c.channel_id,
    c.channel_name,
    c.monetization_start_date,
    COUNT(DISTINCT m.date) as days_monetized,
    SUM(m.revenue) as total_revenue,
    SUM(m.views) as total_views,
    AVG(m.revenue) as avg_daily_revenue,
    CASE WHEN SUM(m.views) > 0
         THEN SUM(m.revenue) / SUM(m.views) * 1000
         ELSE 0 END as avg_rpm
FROM yt_channels c
LEFT JOIN yt_daily_metrics m ON c.channel_id = m.channel_id AND m.revenue > 0
GROUP BY c.channel_id, c.channel_name, c.monetization_start_date;
```
