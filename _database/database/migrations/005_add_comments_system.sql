-- Migration: Sistema Completo de Comentários YouTube
-- Data: 19/01/2026
-- Autor: cellibs-escritorio
-- Descrição: Adiciona coleta e análise de comentários para nossos canais

-- ==================================================
-- 1. CRIAR TABELA PRINCIPAL DE COMENTÁRIOS
-- ==================================================

CREATE TABLE IF NOT EXISTS video_comments (
    id BIGSERIAL PRIMARY KEY,

    -- Identificação
    comment_id TEXT UNIQUE NOT NULL,
    video_id TEXT NOT NULL,
    video_title TEXT,
    canal_id INTEGER REFERENCES canais_monitorados(id) ON DELETE CASCADE,

    -- Dados do comentário
    author_name TEXT,
    author_channel_id TEXT,
    comment_text_original TEXT NOT NULL,
    comment_text_pt TEXT, -- Traduzido para PT-BR
    original_language TEXT DEFAULT 'pt',
    is_translated BOOLEAN DEFAULT FALSE,
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    is_reply BOOLEAN DEFAULT FALSE,
    parent_comment_id TEXT,

    -- Análise de sentimento
    sentiment_score FLOAT, -- -1.0 a 1.0
    sentiment_category TEXT CHECK (sentiment_category IN ('positive', 'negative', 'neutral')),

    -- Categorização de problemas
    has_problem BOOLEAN DEFAULT FALSE,
    problem_type TEXT CHECK (problem_type IN ('audio', 'video', 'content', 'technical', 'other', NULL)),
    problem_description TEXT,

    -- Categorização de elogios
    has_praise BOOLEAN DEFAULT FALSE,
    praise_type TEXT CHECK (praise_type IN ('content', 'editing', 'narration', 'thumbnail', 'general', NULL)),

    -- Insights e ações
    insight_text TEXT,
    action_required BOOLEAN DEFAULT FALSE,
    suggested_action TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,

    -- Timestamps
    published_at TIMESTAMP NOT NULL,
    collected_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==================================================
-- 2. CRIAR TABELA DE RESUMO POR VÍDEO (CACHE)
-- ==================================================

CREATE TABLE IF NOT EXISTS video_comments_summary (
    id SERIAL PRIMARY KEY,
    video_id TEXT UNIQUE NOT NULL,
    video_title TEXT,
    canal_id INTEGER REFERENCES canais_monitorados(id) ON DELETE CASCADE,

    -- Métricas gerais
    total_comments INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,

    -- Percentuais
    positive_percentage FLOAT DEFAULT 0,
    negative_percentage FLOAT DEFAULT 0,
    sentiment_score FLOAT DEFAULT 0, -- Score geral do vídeo

    -- Problemas e elogios
    problems_count INTEGER DEFAULT 0,
    praise_count INTEGER DEFAULT 0,
    actionable_count INTEGER DEFAULT 0,
    resolved_count INTEGER DEFAULT 0,

    -- Top insights (JSON)
    top_positive_insights JSONB DEFAULT '[]',
    top_negative_insights JSONB DEFAULT '[]',
    problem_categories JSONB DEFAULT '{}', -- {"audio": 3, "video": 1, ...}
    praise_categories JSONB DEFAULT '{}', -- {"content": 10, "editing": 5, ...}

    -- Timestamps
    first_comment_at TIMESTAMP,
    last_comment_at TIMESTAMP,
    last_analyzed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ==================================================
-- 3. CRIAR TABELA DE PALAVRAS-CHAVE PARA ANÁLISE
-- ==================================================

CREATE TABLE IF NOT EXISTS comment_analysis_keywords (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    keyword_pt TEXT, -- Versão em português
    category TEXT NOT NULL, -- 'problem', 'praise', 'neutral'
    subcategory TEXT, -- 'audio', 'video', 'content', etc.
    weight FLOAT DEFAULT 1.0, -- Peso para análise de sentimento
    language TEXT DEFAULT 'pt',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Inserir palavras-chave padrão para análise
INSERT INTO comment_analysis_keywords (keyword, keyword_pt, category, subcategory, weight) VALUES
-- Problemas de áudio
('áudio ruim', 'áudio ruim', 'problem', 'audio', -0.8),
('som baixo', 'som baixo', 'problem', 'audio', -0.7),
('não escuto', 'não escuto', 'problem', 'audio', -0.9),
('muito barulho', 'muito barulho', 'problem', 'audio', -0.7),
('chiado', 'chiado', 'problem', 'audio', -0.6),
('eco', 'eco', 'problem', 'audio', -0.6),
('audio bad', 'áudio ruim', 'problem', 'audio', -0.8),
('can''t hear', 'não escuto', 'problem', 'audio', -0.9),

-- Problemas de vídeo
('vídeo travando', 'vídeo travando', 'problem', 'video', -0.8),
('qualidade ruim', 'qualidade ruim', 'problem', 'video', -0.7),
('pixelado', 'pixelado', 'problem', 'video', -0.6),
('borrado', 'borrado', 'problem', 'video', -0.6),
('laggy', 'travando', 'problem', 'video', -0.7),
('blurry', 'borrado', 'problem', 'video', -0.6),

-- Problemas de conteúdo
('erro', 'erro', 'problem', 'content', -0.7),
('informação errada', 'informação errada', 'problem', 'content', -0.9),
('confuso', 'confuso', 'problem', 'content', -0.5),
('não entendi', 'não entendi', 'problem', 'content', -0.4),
('mistake', 'erro', 'problem', 'content', -0.7),
('wrong info', 'informação errada', 'problem', 'content', -0.9),

-- Elogios ao conteúdo
('ótimo', 'ótimo', 'praise', 'content', 0.8),
('excelente', 'excelente', 'praise', 'content', 0.9),
('muito bom', 'muito bom', 'praise', 'content', 0.7),
('adorei', 'adorei', 'praise', 'content', 0.9),
('perfeito', 'perfeito', 'praise', 'content', 1.0),
('incrível', 'incrível', 'praise', 'content', 0.9),
('awesome', 'incrível', 'praise', 'content', 0.9),
('amazing', 'incrível', 'praise', 'content', 0.9),
('great', 'ótimo', 'praise', 'content', 0.8),

-- Elogios à edição
('edição top', 'edição top', 'praise', 'editing', 0.8),
('bem editado', 'bem editado', 'praise', 'editing', 0.7),
('edição perfeita', 'edição perfeita', 'praise', 'editing', 0.9),
('great editing', 'ótima edição', 'praise', 'editing', 0.8),
('well edited', 'bem editado', 'praise', 'editing', 0.7);

-- ==================================================
-- 4. CRIAR ÍNDICES PARA PERFORMANCE
-- ==================================================

-- Índices principais
CREATE INDEX idx_video_comments_video_id ON video_comments(video_id);
CREATE INDEX idx_video_comments_canal_id ON video_comments(canal_id);
CREATE INDEX idx_video_comments_sentiment ON video_comments(sentiment_category);
CREATE INDEX idx_video_comments_problems ON video_comments(has_problem) WHERE has_problem = TRUE;
CREATE INDEX idx_video_comments_actionable ON video_comments(action_required) WHERE action_required = TRUE;
CREATE INDEX idx_video_comments_published ON video_comments(published_at DESC);

-- Índices para busca
CREATE INDEX idx_video_comments_text_pt ON video_comments USING gin(to_tsvector('portuguese', comment_text_pt));
CREATE INDEX idx_video_comments_author ON video_comments(author_name);

-- Índices para o resumo
CREATE INDEX idx_video_comments_summary_canal ON video_comments_summary(canal_id);
CREATE INDEX idx_video_comments_summary_video ON video_comments_summary(video_id);

-- ==================================================
-- 5. CRIAR FUNÇÕES AUXILIARES
-- ==================================================

-- Função para atualizar timestamp automaticamente
CREATE OR REPLACE FUNCTION update_comment_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar timestamp
CREATE TRIGGER update_video_comments_updated_at
BEFORE UPDATE ON video_comments
FOR EACH ROW
EXECUTE FUNCTION update_comment_timestamp();

-- Função para calcular resumo do vídeo
CREATE OR REPLACE FUNCTION update_video_comment_summary(p_video_id TEXT)
RETURNS VOID AS $$
BEGIN
    INSERT INTO video_comments_summary (
        video_id,
        total_comments,
        positive_count,
        negative_count,
        neutral_count,
        positive_percentage,
        negative_percentage,
        sentiment_score,
        problems_count,
        praise_count,
        actionable_count
    )
    SELECT
        p_video_id,
        COUNT(*),
        COUNT(*) FILTER (WHERE sentiment_category = 'positive'),
        COUNT(*) FILTER (WHERE sentiment_category = 'negative'),
        COUNT(*) FILTER (WHERE sentiment_category = 'neutral'),
        ROUND(COUNT(*) FILTER (WHERE sentiment_category = 'positive')::FLOAT / COUNT(*) * 100, 1),
        ROUND(COUNT(*) FILTER (WHERE sentiment_category = 'negative')::FLOAT / COUNT(*) * 100, 1),
        ROUND(AVG(sentiment_score), 2),
        COUNT(*) FILTER (WHERE has_problem = TRUE),
        COUNT(*) FILTER (WHERE has_praise = TRUE),
        COUNT(*) FILTER (WHERE action_required = TRUE)
    FROM video_comments
    WHERE video_id = p_video_id
    ON CONFLICT (video_id) DO UPDATE SET
        total_comments = EXCLUDED.total_comments,
        positive_count = EXCLUDED.positive_count,
        negative_count = EXCLUDED.negative_count,
        neutral_count = EXCLUDED.neutral_count,
        positive_percentage = EXCLUDED.positive_percentage,
        negative_percentage = EXCLUDED.negative_percentage,
        sentiment_score = EXCLUDED.sentiment_score,
        problems_count = EXCLUDED.problems_count,
        praise_count = EXCLUDED.praise_count,
        actionable_count = EXCLUDED.actionable_count,
        last_analyzed_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ==================================================
-- 6. CRIAR VIEW PARA FACILITAR QUERIES
-- ==================================================

CREATE OR REPLACE VIEW video_comments_analysis AS
SELECT
    vc.*,
    cm.nome as canal_nome,
    cm.subnicho as canal_subnicho,
    cm.tipo as canal_tipo,
    CASE
        WHEN vc.published_at > NOW() - INTERVAL '24 hours' THEN 'hoje'
        WHEN vc.published_at > NOW() - INTERVAL '7 days' THEN 'esta_semana'
        WHEN vc.published_at > NOW() - INTERVAL '30 days' THEN 'este_mes'
        ELSE 'antigo'
    END as periodo
FROM video_comments vc
LEFT JOIN canais_monitorados cm ON vc.canal_id = cm.id
WHERE cm.tipo = 'nosso'; -- Apenas nossos canais

-- ==================================================
-- 7. VERIFICAR SE MIGRATION FOI APLICADA
-- ==================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'video_comments'
    ) THEN
        RAISE NOTICE 'Migration 005 - Sistema de Comentários aplicada com sucesso!';
    ELSE
        RAISE EXCEPTION 'Erro ao aplicar migration 005';
    END IF;
END $$;