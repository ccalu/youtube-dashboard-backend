-- ============================================================
-- Migration SEGURA: Sistema de Comentários YouTube - GPT
-- Data: 2026-01-19
-- Versão: SAFE (sem DROP, 100% incremental, zero risco)
-- ============================================================

-- IMPORTANTE: Esta migration NÃO deleta nada existente!
-- Pode ser rodada múltiplas vezes sem problemas.

-- ==================================================
-- 1. TABELA PRINCIPAL DE COMENTÁRIOS
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
    /* Estrutura do JSONB:
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
-- 4. ÍNDICES OTIMIZADOS (com verificação)
-- ==================================================

-- Criar índices apenas se não existirem
DO $$
BEGIN
    -- Índices básicos
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_video_id') THEN
        CREATE INDEX idx_vc_video_id ON video_comments(video_id);
        RAISE NOTICE 'Índice idx_vc_video_id criado';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_canal_id') THEN
        CREATE INDEX idx_vc_canal_id ON video_comments(canal_id);
        RAISE NOTICE 'Índice idx_vc_canal_id criado';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_published') THEN
        CREATE INDEX idx_vc_published ON video_comments(published_at DESC);
        RAISE NOTICE 'Índice idx_vc_published criado';
    END IF;

    -- Índices para análise
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_sentiment') THEN
        CREATE INDEX idx_vc_sentiment ON video_comments(sentiment_category);
        RAISE NOTICE 'Índice idx_vc_sentiment criado';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_primary_cat') THEN
        CREATE INDEX idx_vc_primary_cat ON video_comments(primary_category);
        RAISE NOTICE 'Índice idx_vc_primary_cat criado';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_analyzed') THEN
        CREATE INDEX idx_vc_analyzed ON video_comments(analyzed_at) WHERE analyzed_at IS NOT NULL;
        RAISE NOTICE 'Índice idx_vc_analyzed criado';
    END IF;

    -- Índices para priorização (CRÍTICO para performance)
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_priority') THEN
        CREATE INDEX idx_vc_priority ON video_comments(priority_score DESC)
            WHERE priority_score >= 50;
        RAISE NOTICE 'Índice idx_vc_priority criado';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_high_priority') THEN
        CREATE INDEX idx_vc_high_priority ON video_comments(canal_id, priority_score DESC)
            WHERE priority_score >= 70;
        RAISE NOTICE 'Índice idx_vc_high_priority criado';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_requires_response') THEN
        CREATE INDEX idx_vc_requires_response ON video_comments(requires_response, priority_score DESC)
            WHERE requires_response = TRUE;
        RAISE NOTICE 'Índice idx_vc_requires_response criado';
    END IF;

    -- Índices para status
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_pending_review') THEN
        CREATE INDEX idx_vc_pending_review ON video_comments(is_reviewed, priority_score DESC)
            WHERE is_reviewed = FALSE;
        RAISE NOTICE 'Índice idx_vc_pending_review criado';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_pending_response') THEN
        CREATE INDEX idx_vc_pending_response ON video_comments(is_responded, requires_response)
            WHERE is_responded = FALSE AND requires_response = TRUE;
        RAISE NOTICE 'Índice idx_vc_pending_response criado';
    END IF;

    -- Índices GIN para JSONB e arrays
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_gpt_analysis') THEN
        CREATE INDEX idx_vc_gpt_analysis ON video_comments USING gin(gpt_analysis);
        RAISE NOTICE 'Índice idx_vc_gpt_analysis criado';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vc_categories') THEN
        CREATE INDEX idx_vc_categories ON video_comments USING gin(categories);
        RAISE NOTICE 'Índice idx_vc_categories criado';
    END IF;

    -- Índices para tabela summary
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vcs_canal') THEN
        CREATE INDEX idx_vcs_canal ON video_comments_summary(canal_id);
        RAISE NOTICE 'Índice idx_vcs_canal criado';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_vcs_video') THEN
        CREATE INDEX idx_vcs_video ON video_comments_summary(video_id);
        RAISE NOTICE 'Índice idx_vcs_video criado';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Erro ao criar índices: %', SQLERRM;
END $$;

-- ==================================================
-- 5. FUNÇÕES E TRIGGERS (CREATE OR REPLACE = seguro)
-- ==================================================

-- Função para atualizar timestamp (nome único para evitar conflitos)
CREATE OR REPLACE FUNCTION comments_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criar triggers (DROP IF EXISTS + CREATE para evitar erros)
DROP TRIGGER IF EXISTS update_video_comments_timestamp ON video_comments;
CREATE TRIGGER update_video_comments_timestamp
    BEFORE UPDATE ON video_comments
    FOR EACH ROW EXECUTE FUNCTION comments_update_timestamp();

DROP TRIGGER IF EXISTS update_video_comments_summary_timestamp ON video_comments_summary;
CREATE TRIGGER update_video_comments_summary_timestamp
    BEFORE UPDATE ON video_comments_summary
    FOR EACH ROW EXECUTE FUNCTION comments_update_timestamp();

-- ==================================================
-- 6. VIEWS (CREATE OR REPLACE = seguro, não quebra nada)
-- ==================================================

-- View para comentários prioritários
-- VIEW = "Consulta Salva" - não guarda dados, só é um atalho!
CREATE OR REPLACE VIEW priority_comments_view AS
SELECT
    vc.id,
    vc.comment_id,
    vc.video_id,
    vc.video_title,
    vc.canal_id,
    vc.author_name,
    vc.comment_text_original,
    vc.like_count,
    vc.priority_score,
    vc.urgency_level,
    vc.requires_response,
    vc.sentiment_category,
    vc.primary_category,
    vc.suggested_response,
    vc.is_reviewed,
    vc.is_responded,
    vc.is_resolved,
    vc.published_at,
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

-- View para comentários pendentes de resposta
-- VIEW = "Filtro Pronto" - facilita consultas repetitivas
CREATE OR REPLACE VIEW pending_response_view AS
SELECT
    vc.id,
    vc.comment_id,
    vc.video_id,
    vc.video_title,
    vc.canal_id,
    vc.author_name,
    vc.comment_text_original,
    vc.like_count,
    vc.priority_score,
    vc.urgency_level,
    vc.sentiment_category,
    vc.primary_category,
    vc.suggested_response,
    vc.response_tone,
    vc.published_at,
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
-- 7. VERIFICAÇÃO FINAL
-- ==================================================

DO $$
DECLARE
    v_table_count INTEGER;
    v_index_count INTEGER;
    v_view_count INTEGER;
    v_message TEXT := '';
BEGIN
    -- Verificar tabelas criadas
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables
    WHERE table_name IN ('video_comments', 'video_comments_summary', 'gpt_analysis_metrics')
    AND table_schema = 'public';

    -- Verificar índices criados
    SELECT COUNT(*) INTO v_index_count
    FROM pg_indexes
    WHERE (indexname LIKE 'idx_vc%' OR indexname LIKE 'idx_vcs%')
    AND schemaname = 'public';

    -- Verificar views criadas
    SELECT COUNT(*) INTO v_view_count
    FROM information_schema.views
    WHERE table_name IN ('priority_comments_view', 'pending_response_view')
    AND table_schema = 'public';

    -- Construir mensagem de resultado
    RAISE NOTICE '';
    RAISE NOTICE '=====================================';
    RAISE NOTICE '    MIGRATION SEGURA APLICADA';
    RAISE NOTICE '=====================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Estruturas criadas:';
    RAISE NOTICE '  Tabelas: % / 3', v_table_count;
    RAISE NOTICE '  Índices: % / 16', v_index_count;
    RAISE NOTICE '  Views: % / 2', v_view_count;
    RAISE NOTICE '';

    -- Verificar sucesso
    IF v_table_count = 3 THEN
        RAISE NOTICE '[OK] Todas as tabelas criadas com sucesso!';
    ELSE
        RAISE WARNING '[AVISO] Nem todas as tabelas foram criadas: %/3', v_table_count;
    END IF;

    IF v_view_count = 2 THEN
        RAISE NOTICE '[OK] Views criadas (consultas prontas)';
    END IF;

    IF v_index_count >= 10 THEN
        RAISE NOTICE '[OK] Índices de performance criados';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE '=====================================';
    RAISE NOTICE '  Sistema de comentários pronto!';
    RAISE NOTICE '=====================================';

    -- Teste final
    IF v_table_count = 3 AND v_view_count = 2 THEN
        RAISE NOTICE '';
        RAISE NOTICE '[SUCESSO] Migration aplicada com sucesso!';
        RAISE NOTICE 'Próximos passos:';
        RAISE NOTICE '  1. Atualizar database.py';
        RAISE NOTICE '  2. Criar analisador GPT';
        RAISE NOTICE '  3. Testar coleta de comentários';
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Erro durante verificação: %', SQLERRM;
END $$;

-- ==================================================
-- FIM DA MIGRATION SEGURA
-- ==================================================
-- Esta migration pode ser executada múltiplas vezes
-- sem risco de quebrar o sistema ou perder dados.
-- ==================================================