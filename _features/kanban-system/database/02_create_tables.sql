-- Script 02: Criar tabelas para o sistema Kanban
-- Data: 28/01/2025
-- Objetivo: Criar tabelas kanban_notes e kanban_history

-- =====================================================
-- TABELA: kanban_notes
-- =====================================================
CREATE TABLE IF NOT EXISTS kanban_notes (
    id SERIAL PRIMARY KEY,

    -- Relacionamento
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,

    -- Conteúdo da nota
    note_text TEXT NOT NULL,
    note_color VARCHAR(20) DEFAULT 'yellow',

    -- Ordem e posicionamento
    position INTEGER DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_color CHECK (note_color IN ('yellow', 'green', 'blue', 'purple', 'red', 'orange'))
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_kanban_notes_canal ON kanban_notes(canal_id);
CREATE INDEX IF NOT EXISTS idx_kanban_notes_position ON kanban_notes(canal_id, position);

-- Comentários
COMMENT ON TABLE kanban_notes IS
'Notas do sistema Kanban para documentar estratégias e decisões sobre cada canal';

COMMENT ON COLUMN kanban_notes.note_color IS
'Cor da nota para organização visual: yellow, green, blue, purple, red, orange';

COMMENT ON COLUMN kanban_notes.position IS
'Ordem de exibição das notas (1 = primeira, 2 = segunda, etc). Permite drag & drop.';

-- =====================================================
-- TABELA: kanban_history
-- =====================================================
CREATE TABLE IF NOT EXISTS kanban_history (
    id SERIAL PRIMARY KEY,

    -- Relacionamento
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,

    -- Tipo de ação
    action_type VARCHAR(50) NOT NULL,

    -- Descrição da ação
    description TEXT NOT NULL,

    -- Detalhes adicionais (JSON para flexibilidade)
    details JSONB,

    -- Quando aconteceu
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Soft delete (permite remover do histórico)
    is_deleted BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT valid_action CHECK (action_type IN (
        'status_change',
        'note_added',
        'note_edited',
        'note_deleted',
        'note_reordered',
        'canal_created'
    ))
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_kanban_history_canal ON kanban_history(canal_id);
CREATE INDEX IF NOT EXISTS idx_kanban_history_date ON kanban_history(performed_at DESC);
CREATE INDEX IF NOT EXISTS idx_kanban_history_visible ON kanban_history(canal_id, is_deleted)
WHERE is_deleted = FALSE;

-- Comentários
COMMENT ON TABLE kanban_history IS
'Histórico de todas as ações realizadas no sistema Kanban, com soft delete';

COMMENT ON COLUMN kanban_history.action_type IS
'Tipo de ação: status_change, note_added, note_edited, note_deleted, note_reordered, canal_created';

COMMENT ON COLUMN kanban_history.details IS
'Detalhes em JSON. Ex: {"from": "em_teste", "to": "com_tracao"} ou {"note_id": 123, "color": "green"}';

COMMENT ON COLUMN kanban_history.is_deleted IS
'Soft delete - permite remover itens do histórico sem deletar fisicamente';

-- =====================================================
-- FUNÇÃO: Registrar no histórico automaticamente
-- =====================================================
CREATE OR REPLACE FUNCTION log_kanban_action(
    p_canal_id INTEGER,
    p_action_type VARCHAR(50),
    p_description TEXT,
    p_details JSONB DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_history_id INTEGER;
BEGIN
    INSERT INTO kanban_history (canal_id, action_type, description, details)
    VALUES (p_canal_id, p_action_type, p_description, p_details)
    RETURNING id INTO v_history_id;

    RETURN v_history_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_kanban_action IS
'Função helper para registrar ações no histórico do Kanban';

-- =====================================================
-- TRIGGER: Registrar mudanças de status automaticamente
-- =====================================================
CREATE OR REPLACE FUNCTION track_kanban_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Se o status mudou e é um canal nosso
    IF NEW.kanban_status IS DISTINCT FROM OLD.kanban_status
       AND NEW.tipo = 'nosso' THEN

        PERFORM log_kanban_action(
            NEW.id,
            'status_change',
            CONCAT('Status mudou de ',
                   COALESCE(OLD.kanban_status, 'indefinido'),
                   ' para ',
                   NEW.kanban_status),
            jsonb_build_object(
                'from_status', OLD.kanban_status,
                'to_status', NEW.kanban_status,
                'from_date', OLD.kanban_status_since,
                'to_date', NEW.kanban_status_since
            )
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criar trigger
DROP TRIGGER IF EXISTS trg_kanban_status_change ON canais_monitorados;

CREATE TRIGGER trg_kanban_status_change
    AFTER UPDATE ON canais_monitorados
    FOR EACH ROW
    WHEN (OLD.kanban_status IS DISTINCT FROM NEW.kanban_status)
    EXECUTE FUNCTION track_kanban_status_change();

-- =====================================================
-- VIEWS: Para facilitar queries
-- =====================================================

-- View para canais com informações do Kanban
CREATE OR REPLACE VIEW v_kanban_canais AS
SELECT
    c.id,
    c.nome,
    c.subnicho,
    c.lingua,
    c.monetizado,
    c.kanban_status,
    c.kanban_status_since,
    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - c.kanban_status_since))::INTEGER as dias_no_status,
    COUNT(n.id) as total_notas
FROM canais_monitorados c
LEFT JOIN kanban_notes n ON n.canal_id = c.id
WHERE c.tipo = 'nosso'
GROUP BY c.id;

COMMENT ON VIEW v_kanban_canais IS
'View com informações do Kanban para nossos canais, incluindo dias no status e total de notas';

-- Estatísticas do sistema
SELECT 'Tabelas criadas com sucesso!' as status;

-- Verificar estrutura
SELECT
    'kanban_notes' as tabela,
    COUNT(*) as registros
FROM kanban_notes
UNION ALL
SELECT
    'kanban_history' as tabela,
    COUNT(*) as registros
FROM kanban_history;