-- ============================================================
-- Migration: Sistema de Comentários YouTube - Análise 100% IA
-- Data: 2026-01-19
-- Autor: Cellibs
-- Descrição: Schema otimizado para análise completa via GPT
-- ============================================================

-- Dropar tabelas antigas se existirem (cuidado em produção!)
DROP TABLE IF EXISTS video_comments_summary CASCADE;
DROP TABLE IF EXISTS video_comments CASCADE;
DROP TABLE IF EXISTS comment_analysis_keywords CASCADE;
DROP TABLE IF EXISTS gpt_analysis_metrics CASCADE;

-- ==================================================
-- 1. TABELA PRINCIPAL DE COMENTÁRIOS (GPT-OPTIMIZED)
-- ==================================================

CREATE TABLE IF NOT EXISTS video_comments (
    id BIGSERIAL PRIMARY KEY,

    -- Identificação básica
    comment_id TEXT UNIQUE NOT NULL,
    video_id TEXT NOT NULL,
    video_title TEXT,
    canal_id INTEGER REFERENCES canais_monitorados(id) ON DELETE CASCADE,

    -- Dados do autor
    author_name TEXT,
    author_channel_id TEXT,

    -- Conteúdo do comentário
    comment_text_original TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    is_reply BOOLEAN DEFAULT FALSE,
    parent_comment_id TEXT,

    -- ===== ANÁLISE GPT COMPLETA =====
    gpt_analysis JSONB,
    /* Estrutura esperada do JSONB:
    {
        "sentiment": {
            "category": "positive|negative|neutral|mixed",
            "score": -1.0 a 1.0,
            "confidence": 0.0 a 1.0,
            "nuances": ["sarcasm", "irony", "genuine", "emotional"]
        },
        "categories": ["problem", "praise", "question", "suggestion", "feedback"],
        "primary_category": "problem",
        "subcategories": {
            "problem": ["audio", "video", "content", "technical"],
            "praise": ["content", "editing", "narration", "thumbnail"]
        },
        "topics": ["narração", "edição", "história", "música"],
        "key_points": ["Ponto principal 1", "Ponto 2"],
        "emotional_tone": "angry|happy|frustrated|excited|neutral|concerned",
        "intent": "criticize|compliment|ask|suggest|inform",
        "context_indicators": ["frequent_viewer", "first_time", "fan"],
        "language": "pt|en|es|other"
    }
    */

    -- Campos extraídos para queries rápidas
    sentiment_category TEXT,
    sentiment_score FLOAT,
    sentiment_confidence FLOAT,

    categories TEXT[],
    primary_category TEXT,
    emotional_tone TEXT,

    -- Priorização inteligente
    priority_score INTEGER DEFAULT 0, -- 0-100
    urgency_level TEXT CHECK (urgency_level IN ('high', 'medium', 'low', NULL)),
    requires_response BOOLEAN DEFAULT FALSE,

    -- Resposta sugerida
    suggested_response TEXT,
    response_tone TEXT,

    -- Insights principais
    insight_summary TEXT,
    actionable_items JSONB,

    -- Status de tratamento
    is_reviewed BOOLEAN DEFAULT FALSE,
    reviewed_at TIMESTAMP,
    is_responded BOOLEAN DEFAULT FALSE,
    responded_at TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,

    -- Timestamps
    published_at TIMESTAMP NOT NULL,
    collected_at TIMESTAMP DEFAULT NOW(),
    analyzed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==================================================
-- 2. TABELA DE RESUMO POR VÍDEO
-- ==================================================

CREATE TABLE IF NOT EXISTS video_comments_summary (
    id SERIAL PRIMARY KEY,
    video_id TEXT UNIQUE NOT NULL,
    video_title TEXT,
    canal_id INTEGER REFERENCES canais_monitorados(id) ON DELETE CASCADE,

    -- Métricas básicas
    total_comments INTEGER DEFAULT 0,
    analyzed_comments INTEGER DEFAULT 0,

    -- Distribuição de sentimento
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    mixed_count INTEGER DEFAULT 0,

    positive_percentage FLOAT DEFAULT 0,
    negative_percentage FLOAT DEFAULT 0,
    avg_sentiment_score FLOAT DEFAULT 0,
    avg_confidence FLOAT DEFAULT 0,

    -- Categorização
    problems_count INTEGER DEFAULT 0,
    praise_count INTEGER DEFAULT 0,
    questions_count INTEGER DEFAULT 0,
    suggestions_count INTEGER DEFAULT 0,

    -- Priorização
    high_priority_count INTEGER DEFAULT 0, -- >= 70
    medium_priority_count INTEGER DEFAULT 0, -- 40-69
    low_priority_count INTEGER DEFAULT 0, -- < 40

    requires_response_count INTEGER DEFAULT 0,

    -- Status
    reviewed_count INTEGER DEFAULT 0,
    responded_count INTEGER DEFAULT 0,
    resolved_count INTEGER DEFAULT 0,

    -- Análise agregada
    top_topics TEXT[],
    top_positive_insights JSONB DEFAULT '[]',
    top_negative_insights JSONB DEFAULT '[]',
    top_questions JSONB DEFAULT '[]',
    actionable_summary JSONB DEFAULT '[]',

    -- Timestamps
    first_comment_at TIMESTAMP,
    last_comment_at TIMESTAMP,
    last_analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==================================================
-- 3. TABELA DE MÉTRICAS GPT
-- ==================================================

CREATE TABLE IF NOT EXISTS gpt_analysis_metrics (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE UNIQUE,

    -- Volume
    total_analyzed INTEGER DEFAULT 0,
    total_tokens_input INTEGER DEFAULT 0,
    total_tokens_output INTEGER DEFAULT 0,

    -- Performance
    avg_response_time_ms INTEGER,
    success_rate FLOAT,
    errors_count INTEGER DEFAULT 0,

    -- Custos
    estimated_cost_usd FLOAT DEFAULT 0,

    -- Confiança
    high_confidence_count INTEGER DEFAULT 0, -- >= 0.8
    medium_confidence_count INTEGER DEFAULT 0, -- 0.5-0.8
    low_confidence_count INTEGER DEFAULT 0, -- < 0.5

    created_at TIMESTAMP DEFAULT NOW()
);

-- ==================================================
-- 4. ÍNDICES OTIMIZADOS
-- ==================================================

-- Índices básicos
CREATE INDEX idx_vc_video_id ON video_comments(video_id);
CREATE INDEX idx_vc_canal_id ON video_comments(canal_id);
CREATE INDEX idx_vc_published ON video_comments(published_at DESC);

-- Índices para análise
CREATE INDEX idx_vc_sentiment ON video_comments(sentiment_category);
CREATE INDEX idx_vc_primary_cat ON video_comments(primary_category);
CREATE INDEX idx_vc_analyzed ON video_comments(analyzed_at) WHERE analyzed_at IS NOT NULL;

-- Índices para priorização (CRÍTICO!)
CREATE INDEX idx_vc_priority ON video_comments(priority_score DESC)
    WHERE priority_score >= 50;
CREATE INDEX idx_vc_high_priority ON video_comments(canal_id, priority_score DESC)
    WHERE priority_score >= 70;
CREATE INDEX idx_vc_requires_response ON video_comments(requires_response, priority_score DESC)
    WHERE requires_response = TRUE;

-- Índices para status
CREATE INDEX idx_vc_pending_review ON video_comments(is_reviewed, priority_score DESC)
    WHERE is_reviewed = FALSE;
CREATE INDEX idx_vc_pending_response ON video_comments(is_responded, requires_response)
    WHERE is_responded = FALSE AND requires_response = TRUE;

-- Índices GIN para JSONB
CREATE INDEX idx_vc_gpt_analysis ON video_comments USING gin(gpt_analysis);
CREATE INDEX idx_vc_categories ON video_comments USING gin(categories);

-- Índices para summary
CREATE INDEX idx_vcs_canal ON video_comments_summary(canal_id);
CREATE INDEX idx_vcs_video ON video_comments_summary(video_id);

-- ==================================================
-- 5. FUNÇÕES E TRIGGERS
-- ==================================================

-- Função para atualizar timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER update_video_comments_timestamp
    BEFORE UPDATE ON video_comments
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_video_comments_summary_timestamp
    BEFORE UPDATE ON video_comments_summary
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==================================================
-- 6. VIEWS ÚTEIS
-- ==================================================

-- View para comentários prioritários
CREATE OR REPLACE VIEW priority_comments_view AS
SELECT
    vc.*,
    cm.nome_canal,
    cm.subnicho,
    CASE
        WHEN vc.priority_score >= 70 THEN 'high'
        WHEN vc.priority_score >= 40 THEN 'medium'
        ELSE 'low'
    END as priority_level
FROM video_comments vc
JOIN canais_monitorados cm ON vc.canal_id = cm.id
WHERE
    cm.tipo = 'nosso'
    AND vc.priority_score >= 50
    AND vc.is_resolved = FALSE
ORDER BY vc.priority_score DESC, vc.published_at DESC;

-- View para comentários pendentes
CREATE OR REPLACE VIEW pending_response_view AS
SELECT
    vc.*,
    cm.nome_canal,
    cm.subnicho
FROM video_comments vc
JOIN canais_monitorados cm ON vc.canal_id = cm.id
WHERE
    cm.tipo = 'nosso'
    AND vc.requires_response = TRUE
    AND vc.is_responded = FALSE
ORDER BY vc.priority_score DESC, vc.published_at DESC;

-- ==================================================
-- 7. VERIFICAÇÃO
-- ==================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'video_comments'
    ) THEN
        RAISE NOTICE '✅ Tabela video_comments criada com sucesso';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'video_comments'
        AND column_name = 'gpt_analysis'
    ) THEN
        RAISE NOTICE '✅ Campo gpt_analysis (JSONB) configurado';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'video_comments_summary'
    ) THEN
        RAISE NOTICE '✅ Tabela video_comments_summary criada';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'gpt_analysis_metrics'
    ) THEN
        RAISE NOTICE '✅ Tabela gpt_analysis_metrics criada';
    END IF;

    RAISE NOTICE '✅ Migration 006_comments_gpt_optimized aplicada com sucesso!';
END $$;

-- ==================================================
-- INSTRUÇÕES DE APLICAÇÃO:
-- ==================================================
-- 1. Copie todo este SQL
-- 2. Acesse o Supabase Dashboard
-- 3. Vá em SQL Editor
-- 4. Cole e execute
-- 5. Verifique se todas as tabelas foram criadas
-- ==================================================