-- =====================================================
-- ADICIONAR CAMPO coluna_id NA TABELA kanban_notes
-- Data: 29/01/2025
-- Propósito: Permitir que notas possam estar em qualquer coluna
-- =====================================================

-- Adicionar o campo coluna_id
ALTER TABLE kanban_notes
ADD COLUMN IF NOT EXISTS coluna_id VARCHAR(50);

-- Adicionar comentário explicativo
COMMENT ON COLUMN kanban_notes.coluna_id IS
'ID da coluna onde a nota está (em_teste_inicial, demonstrando_tracao, etc). Permite notas em diferentes colunas independente do status do canal.';

-- Verificar se a coluna foi adicionada
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_name = 'kanban_notes'
    AND column_name = 'coluna_id';

-- Mensagem de sucesso
SELECT 'Coluna coluna_id adicionada com sucesso na tabela kanban_notes' as resultado;