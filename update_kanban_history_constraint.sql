-- =====================================================
-- ATUALIZAR CONSTRAINT NA TABELA kanban_history
-- Data: 29/01/2025
-- Propósito: Adicionar "note_moved" aos tipos de ação válidos
-- =====================================================

-- Primeiro, remover a constraint existente
ALTER TABLE kanban_history
DROP CONSTRAINT IF EXISTS valid_action;

-- Adicionar nova constraint com "note_moved" incluído
ALTER TABLE kanban_history
ADD CONSTRAINT valid_action
CHECK (action_type IN (
    'status_change',
    'note_added',
    'note_edited',
    'note_deleted',
    'note_moved',        -- NOVO: movimento de nota entre colunas
    'note_reordered',
    'note_archived'
));

-- Verificar se a constraint foi atualizada
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(c.oid) AS constraint_definition
FROM
    pg_constraint c
    JOIN pg_namespace n ON n.oid = c.connamespace
    JOIN pg_class t ON t.oid = c.conrelid
WHERE
    t.relname = 'kanban_history'
    AND conname = 'valid_action';

-- Mensagem de sucesso
SELECT 'Constraint valid_action atualizada com sucesso - note_moved adicionado' as resultado;