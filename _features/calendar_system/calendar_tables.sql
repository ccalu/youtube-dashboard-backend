-- ========================================
-- SISTEMA DE CALENDÁRIO EMPRESARIAL
-- Banco de Dados para Dashboard Lovable
-- ========================================
-- Criado em: 11/02/2026
-- Por: Cellibs & Claude
-- ========================================

-- 1️⃣ TABELA DE EVENTOS
CREATE TABLE IF NOT EXISTS calendar_events (
    id SERIAL PRIMARY KEY,

    -- Dados básicos do evento
    title VARCHAR(500) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,

    -- Identificação do autor
    created_by VARCHAR(50) NOT NULL, -- cellibs, arthur, lucca, joao

    -- Categorização
    category VARCHAR(50), -- geral, desenvolvimento, financeiro, urgente
    event_type VARCHAR(50) DEFAULT 'normal', -- normal, monetization, demonetization

    -- Soft delete com lixeira
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Validações
    CONSTRAINT valid_author CHECK (created_by IN ('cellibs', 'arthur', 'lucca', 'joao')),
    CONSTRAINT valid_category CHECK (category IN ('geral', 'desenvolvimento', 'financeiro', 'urgente') OR category IS NULL),
    CONSTRAINT valid_event_type CHECK (event_type IN ('normal', 'monetization', 'demonetization'))
);

-- 2️⃣ TABELA DE CONFIGURAÇÃO DOS SÓCIOS
CREATE TABLE IF NOT EXISTS calendar_config (
    id SERIAL PRIMARY KEY,
    socio_key VARCHAR(50) UNIQUE NOT NULL,
    socio_name VARCHAR(100) NOT NULL,
    socio_emoji VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3️⃣ INSERIR DADOS DOS 4 SÓCIOS
INSERT INTO calendar_config (socio_key, socio_name, socio_emoji) VALUES
('cellibs', 'Cellibs', '🎯'),
('arthur', 'Arthur', '📝'),
('lucca', 'Lucca', '🎬'),
('joao', 'João', '🎨')
ON CONFLICT (socio_key) DO NOTHING;

-- 4️⃣ CRIAR ÍNDICES PARA PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_calendar_date ON calendar_events(event_date) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_calendar_author ON calendar_events(created_by) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_calendar_type ON calendar_events(event_type) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_calendar_deleted ON calendar_events(deleted_at) WHERE is_deleted = TRUE;

-- 5️⃣ FUNÇÃO PARA AUTO-LIMPEZA (30 DIAS)
CREATE OR REPLACE FUNCTION clean_old_deleted_events()
RETURNS void AS $$
BEGIN
    DELETE FROM calendar_events
    WHERE is_deleted = TRUE
    AND deleted_at < (CURRENT_TIMESTAMP - INTERVAL '30 days');
END;
$$ LANGUAGE plpgsql;

-- 6️⃣ TRIGGER PARA ATUALIZAR updated_at
CREATE OR REPLACE FUNCTION update_calendar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS calendar_events_updated_at ON calendar_events;
CREATE TRIGGER calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_calendar_updated_at();

-- ========================================
-- COMENTÁRIOS E DOCUMENTAÇÃO
-- ========================================

COMMENT ON TABLE calendar_events IS 'Tabela principal de eventos do calendário empresarial';
COMMENT ON TABLE calendar_config IS 'Configuração dos 4 sócios da empresa';

COMMENT ON COLUMN calendar_events.event_type IS 'Tipo: normal, monetization, demonetization';
COMMENT ON COLUMN calendar_events.created_by IS 'Sócio: cellibs, arthur, lucca, joao';
COMMENT ON COLUMN calendar_events.category IS 'Categoria: geral, desenvolvimento, financeiro, urgente';