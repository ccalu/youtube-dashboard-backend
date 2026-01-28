-- =====================================================
-- SCRIPT CORRIGIDO PARA CRIAR O SISTEMA KANBAN
-- Execute este arquivo no Supabase SQL Editor
-- Data: 28/01/2025
-- =====================================================

-- PASSO 1: Criar coluna monetizado (se não existir)
-- =====================================================

ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS monetizado BOOLEAN DEFAULT FALSE;

-- Marcar como TRUE os canais que atualmente têm subnicho='Monetizados'
UPDATE canais_monitorados
SET monetizado = TRUE
WHERE tipo = 'nosso'
  AND subnicho = 'Monetizados'
  AND monetizado = FALSE;

-- PASSO 2: Adicionar campos do Kanban
-- =====================================================

ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS kanban_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS kanban_status_since TIMESTAMP WITH TIME ZONE;

-- PASSO 3: Definir status padrão para canais existentes
-- =====================================================

-- Canais NÃO monetizados (tipo='nosso' E monetizado=false)
UPDATE canais_monitorados
SET
    kanban_status = 'em_teste_inicial',
    kanban_status_since = CURRENT_TIMESTAMP
WHERE
    tipo = 'nosso'
    AND monetizado = FALSE
    AND kanban_status IS NULL;

-- Canais MONETIZADOS (tipo='nosso' E monetizado=true)
UPDATE canais_monitorados
SET
    kanban_status = 'canal_constante',
    kanban_status_since = CURRENT_TIMESTAMP
WHERE
    tipo = 'nosso'
    AND monetizado = TRUE
    AND kanban_status IS NULL;

-- PASSO 4: Criar tabela kanban_notes
-- =====================================================

CREATE TABLE IF NOT EXISTS kanban_notes (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    note_color VARCHAR(20) DEFAULT 'yellow',
    position INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_color CHECK (note_color IN ('yellow', 'green', 'blue', 'purple', 'red', 'orange'))
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_kanban_notes_canal ON kanban_notes(canal_id);
CREATE INDEX IF NOT EXISTS idx_kanban_notes_position ON kanban_notes(canal_id, position);

-- PASSO 5: Criar tabela kanban_history
-- =====================================================

CREATE TABLE IF NOT EXISTS kanban_history (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    details JSONB,
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT valid_action CHECK (action_type IN (
        'status_change', 'note_added', 'note_edited',
        'note_deleted', 'note_reordered', 'canal_created'
    ))
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_kanban_history_canal ON kanban_history(canal_id);
CREATE INDEX IF NOT EXISTS idx_kanban_history_date ON kanban_history(performed_at DESC);
CREATE INDEX IF NOT EXISTS idx_kanban_history_visible ON kanban_history(canal_id, is_deleted)
WHERE is_deleted = FALSE;

-- PASSO 6: Verificar instalação
-- =====================================================

-- Ver quantos canais foram marcados como monetizados
SELECT
    'Canais monetizados marcados:' as info,
    COUNT(*) as total
FROM canais_monitorados
WHERE tipo = 'nosso' AND monetizado = TRUE;

-- Ver distribuição de status do Kanban
SELECT
    CASE
        WHEN monetizado THEN 'Monetizados'
        ELSE 'Não Monetizados'
    END as categoria,
    kanban_status,
    COUNT(*) as total
FROM canais_monitorados
WHERE tipo = 'nosso'
GROUP BY monetizado, kanban_status
ORDER BY monetizado DESC, kanban_status;

-- Verificar se as tabelas foram criadas
SELECT
    'kanban_notes' as tabela,
    COUNT(*) as registros
FROM kanban_notes
UNION ALL
SELECT
    'kanban_history' as tabela,
    COUNT(*) as registros
FROM kanban_history;

-- =====================================================
-- SUCESSO!
-- Se você executou até aqui sem erros:
-- 1. Coluna monetizado foi criada
-- 2. Canais com subnicho='Monetizados' foram marcados como TRUE
-- 3. Tabelas do Kanban foram criadas
-- 4. Sistema está 100% pronto para usar!
-- =====================================================