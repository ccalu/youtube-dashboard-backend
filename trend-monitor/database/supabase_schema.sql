-- =============================================
-- TREND MONITOR - TABELAS SUPABASE
-- =============================================
-- Execute este SQL no SQL Editor do Supabase
-- Dashboard: https://supabase.com/dashboard
-- =============================================

-- 1. TRENDS (Historico completo de coletas)
-- Guarda TODOS os trends coletados, 1 registro por trend/dia
CREATE TABLE IF NOT EXISTS trends (
    id BIGSERIAL PRIMARY KEY,

    -- Identificacao
    title TEXT NOT NULL,
    source TEXT NOT NULL,  -- youtube, google_trends, hackernews
    video_id TEXT,         -- ID unico do YouTube (se aplicavel)

    -- Localizacao
    country TEXT DEFAULT 'global',
    language TEXT DEFAULT 'en',

    -- Metricas
    volume INTEGER DEFAULT 0,           -- Views/buscas/upvotes
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,

    -- Qualidade (calculado)
    quality_score INTEGER DEFAULT 0,    -- 0-100
    engagement_ratio DECIMAL(5,4),      -- likes/views %

    -- URLs
    url TEXT,
    thumbnail TEXT,

    -- Metadados fonte
    channel_title TEXT,
    channel_id TEXT,
    category_id TEXT,
    author TEXT,

    -- Tipo de coleta
    collection_type TEXT,               -- trending, subnicho, discovery
    matched_subnicho TEXT,              -- Subnicho que deu match (se houver)

    -- Timestamps
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    collected_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Dados completos (backup)
    raw_data JSONB
);

-- Indices para consultas rapidas
CREATE INDEX IF NOT EXISTS idx_trends_source ON trends(source);
CREATE INDEX IF NOT EXISTS idx_trends_country ON trends(country);
CREATE INDEX IF NOT EXISTS idx_trends_language ON trends(language);
CREATE INDEX IF NOT EXISTS idx_trends_date ON trends(collected_date);
CREATE INDEX IF NOT EXISTS idx_trends_quality ON trends(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_trends_volume ON trends(volume DESC);
CREATE INDEX IF NOT EXISTS idx_trends_subnicho ON trends(matched_subnicho);
CREATE INDEX IF NOT EXISTS idx_trends_video_id ON trends(video_id);


-- 2. TREND_PATTERNS (Analise de persistencia)
-- Detecta quais trends sao EVERGREEN (aparecem ha muitos dias)
CREATE TABLE IF NOT EXISTS trend_patterns (
    id BIGSERIAL PRIMARY KEY,

    -- Identificacao (normalizado)
    title_normalized TEXT NOT NULL UNIQUE,
    video_id TEXT,

    -- Periodo de atividade
    first_seen DATE NOT NULL,
    last_seen DATE NOT NULL,
    days_active INTEGER DEFAULT 1,

    -- Metricas agregadas
    total_volume BIGINT DEFAULT 0,
    avg_volume INTEGER DEFAULT 0,
    max_volume INTEGER DEFAULT 0,
    avg_quality_score INTEGER DEFAULT 0,

    -- Fontes e paises encontrados
    sources_found TEXT[],      -- Array: ['youtube', 'google_trends']
    countries_found TEXT[],    -- Array: ['US', 'BR', 'ES']

    -- Flags de deteccao
    is_evergreen BOOLEAN DEFAULT FALSE,  -- 7+ dias
    is_growing BOOLEAN DEFAULT FALSE,    -- 3+ dias e crescendo
    is_viral BOOLEAN DEFAULT FALSE,      -- crescimento > 50%

    -- Match com subnichos
    matched_subnichos TEXT[],  -- Array: ['terror', 'misterios']
    best_subnicho TEXT,
    subnicho_score INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patterns_evergreen ON trend_patterns(is_evergreen);
CREATE INDEX IF NOT EXISTS idx_patterns_growing ON trend_patterns(is_growing);
CREATE INDEX IF NOT EXISTS idx_patterns_days ON trend_patterns(days_active DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_subnicho ON trend_patterns(best_subnicho);


-- 3. COLLECTIONS (Log de coletas diarias)
-- Registra cada execucao do sistema
CREATE TABLE IF NOT EXISTS collections (
    id BIGSERIAL PRIMARY KEY,

    -- Data da coleta
    collected_date DATE UNIQUE NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Estatisticas
    total_trends INTEGER DEFAULT 0,
    total_youtube INTEGER DEFAULT 0,
    total_google INTEGER DEFAULT 0,
    total_hackernews INTEGER DEFAULT 0,

    -- Por tipo de coleta YouTube
    youtube_trending INTEGER DEFAULT 0,
    youtube_subnicho INTEGER DEFAULT 0,
    youtube_discovery INTEGER DEFAULT 0,

    -- Qualidade
    avg_quality_score INTEGER DEFAULT 0,
    trends_above_70 INTEGER DEFAULT 0,  -- Trends com score > 70
    trends_above_50 INTEGER DEFAULT 0,  -- Trends com score > 50

    -- Deduplicacao
    duplicates_removed INTEGER DEFAULT 0,
    filtered_count INTEGER DEFAULT 0,

    -- API Usage
    youtube_units_used INTEGER DEFAULT 0,

    -- Status
    status TEXT DEFAULT 'completed',
    error_message TEXT,

    -- Metadados
    sources_used JSONB,
    countries_collected JSONB,
    duration_seconds INTEGER DEFAULT 0
);


-- 4. SUBNICHO_MATCHES (Trends por subnicho)
-- Facilita consulta de trends relevantes por canal
CREATE TABLE IF NOT EXISTS subnicho_matches (
    id BIGSERIAL PRIMARY KEY,

    -- Referencias
    trend_id BIGINT REFERENCES trends(id) ON DELETE CASCADE,
    pattern_id BIGINT REFERENCES trend_patterns(id) ON DELETE SET NULL,

    -- Subnicho
    subnicho TEXT NOT NULL,  -- Ex: 'terror', 'misterios'

    -- Score do match
    match_score INTEGER DEFAULT 0,  -- 0-100
    matched_keywords TEXT[],        -- Keywords que deram match

    -- Data
    collected_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Evitar duplicatas
    UNIQUE(trend_id, subnicho)
);

CREATE INDEX IF NOT EXISTS idx_matches_subnicho ON subnicho_matches(subnicho);
CREATE INDEX IF NOT EXISTS idx_matches_score ON subnicho_matches(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_matches_date ON subnicho_matches(collected_date);


-- 5. VIEW: Top Trends por Subnicho (Consulta rapida)
CREATE OR REPLACE VIEW v_top_trends_by_subnicho AS
SELECT
    sm.subnicho,
    t.title,
    t.video_id,
    t.url,
    t.volume,
    t.quality_score,
    t.country,
    t.language,
    t.source,
    sm.match_score,
    tp.days_active,
    tp.is_evergreen,
    t.thumbnail,
    t.channel_title
FROM subnicho_matches sm
JOIN trends t ON sm.trend_id = t.id
LEFT JOIN trend_patterns tp ON t.video_id = tp.video_id
WHERE t.collected_date = CURRENT_DATE
ORDER BY sm.subnicho, sm.match_score DESC, t.quality_score DESC;


-- 6. VIEW: Descobertas (Trends novos de alta qualidade)
CREATE OR REPLACE VIEW v_discoveries AS
SELECT
    t.id,
    t.title,
    t.video_id,
    t.url,
    t.volume,
    t.quality_score,
    t.country,
    t.language,
    t.source,
    t.channel_title,
    t.thumbnail,
    tp.days_active,
    tp.is_growing,
    t.matched_subnicho
FROM trends t
LEFT JOIN trend_patterns tp ON t.video_id = tp.video_id
WHERE t.collected_date = CURRENT_DATE
  AND t.quality_score >= 70
  AND (tp.days_active IS NULL OR tp.days_active <= 3)  -- Novos
ORDER BY t.quality_score DESC, t.volume DESC
LIMIT 100;


-- 7. VIEW: Evergreen (Trends persistentes)
CREATE OR REPLACE VIEW v_evergreen AS
SELECT
    tp.title_normalized as title,
    tp.video_id,
    tp.days_active,
    tp.avg_volume,
    tp.max_volume,
    tp.avg_quality_score,
    tp.sources_found,
    tp.countries_found,
    tp.best_subnicho,
    tp.first_seen,
    tp.last_seen,
    t.url,
    t.thumbnail
FROM trend_patterns tp
LEFT JOIN LATERAL (
    SELECT url, thumbnail
    FROM trends
    WHERE video_id = tp.video_id
    ORDER BY collected_date DESC
    LIMIT 1
) t ON true
WHERE tp.is_evergreen = TRUE
ORDER BY tp.days_active DESC, tp.avg_quality_score DESC;


-- 8. VIEW: Bombando (3+ dias ativos)
CREATE OR REPLACE VIEW v_bombando AS
SELECT
    tp.title_normalized as title,
    tp.video_id,
    tp.days_active,
    tp.avg_volume,
    tp.avg_quality_score,
    tp.best_subnicho,
    tp.is_growing,
    t.url,
    t.thumbnail,
    t.source
FROM trend_patterns tp
LEFT JOIN LATERAL (
    SELECT url, thumbnail, source
    FROM trends
    WHERE video_id = tp.video_id
    ORDER BY collected_date DESC
    LIMIT 1
) t ON true
WHERE tp.days_active >= 3
  AND tp.days_active < 7
ORDER BY tp.avg_quality_score DESC, tp.days_active DESC;


-- 9. VIEW: Top por Lingua
CREATE OR REPLACE VIEW v_top_by_language AS
SELECT
    t.language,
    t.title,
    t.video_id,
    t.url,
    t.volume,
    t.quality_score,
    t.source,
    t.channel_title,
    t.thumbnail,
    t.matched_subnicho,
    ROW_NUMBER() OVER (PARTITION BY t.language ORDER BY t.quality_score DESC) as rank
FROM trends t
WHERE t.collected_date = CURRENT_DATE
  AND t.quality_score >= 50;


-- 10. Funcao para atualizar patterns
CREATE OR REPLACE FUNCTION update_trend_patterns()
RETURNS void AS $$
BEGIN
    -- Inserir ou atualizar patterns
    INSERT INTO trend_patterns (
        title_normalized,
        video_id,
        first_seen,
        last_seen,
        days_active,
        total_volume,
        avg_volume,
        max_volume,
        avg_quality_score,
        sources_found,
        countries_found,
        best_subnicho,
        updated_at
    )
    SELECT
        LOWER(TRIM(title)) as title_normalized,
        video_id,
        MIN(collected_date) as first_seen,
        MAX(collected_date) as last_seen,
        COUNT(DISTINCT collected_date) as days_active,
        SUM(volume) as total_volume,
        AVG(volume)::INTEGER as avg_volume,
        MAX(volume) as max_volume,
        AVG(quality_score)::INTEGER as avg_quality_score,
        ARRAY_AGG(DISTINCT source) as sources_found,
        ARRAY_AGG(DISTINCT country) as countries_found,
        MODE() WITHIN GROUP (ORDER BY matched_subnicho) as best_subnicho,
        NOW() as updated_at
    FROM trends
    WHERE video_id IS NOT NULL
    GROUP BY LOWER(TRIM(title)), video_id
    ON CONFLICT (title_normalized) DO UPDATE SET
        last_seen = EXCLUDED.last_seen,
        days_active = EXCLUDED.days_active,
        total_volume = EXCLUDED.total_volume,
        avg_volume = EXCLUDED.avg_volume,
        max_volume = EXCLUDED.max_volume,
        avg_quality_score = EXCLUDED.avg_quality_score,
        sources_found = EXCLUDED.sources_found,
        countries_found = EXCLUDED.countries_found,
        best_subnicho = EXCLUDED.best_subnicho,
        updated_at = NOW();

    -- Atualizar flags
    UPDATE trend_patterns SET
        is_evergreen = (days_active >= 7),
        is_growing = (days_active >= 3 AND days_active < 7);
END;
$$ LANGUAGE plpgsql;


-- =============================================
-- INSTRUCOES DE USO
-- =============================================
-- 1. Copie todo este SQL
-- 2. Acesse seu projeto Supabase
-- 3. Va em SQL Editor
-- 4. Cole e execute
-- 5. Verifique se todas as tabelas foram criadas
--
-- Para atualizar patterns apos coleta:
-- SELECT update_trend_patterns();
-- =============================================
