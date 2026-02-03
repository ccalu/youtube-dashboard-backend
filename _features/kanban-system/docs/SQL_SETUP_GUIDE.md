# Guia de Configuração SQL - Sistema Kanban

## 📋 Pré-requisitos
- Acesso ao Supabase SQL Editor
- Permissões para criar tabelas e alterar schema

## 🚀 Passos para Configuração

### Passo 1: Adicionar Colunas na Tabela Existente

Execute no Supabase SQL Editor:

```sql
-- Adicionar campos kanban_status e kanban_status_since
ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS kanban_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS kanban_status_since TIMESTAMP WITH TIME ZONE;

-- Definir status padrão para canais não monetizados
UPDATE canais_monitorados
SET
    kanban_status = 'em_teste_inicial',
    kanban_status_since = CURRENT_TIMESTAMP
WHERE
    tipo = 'nosso'
    AND (monetizado = false OR monetizado IS NULL)
    AND kanban_status IS NULL;

-- Definir status padrão para canais monetizados
UPDATE canais_monitorados
SET
    kanban_status = 'canal_constante',
    kanban_status_since = CURRENT_TIMESTAMP
WHERE
    tipo = 'nosso'
    AND monetizado = true
    AND kanban_status IS NULL;
```

### Passo 2: Criar Tabela de Notas

```sql
-- Criar tabela kanban_notes
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
CREATE INDEX idx_kanban_notes_canal ON kanban_notes(canal_id);
CREATE INDEX idx_kanban_notes_position ON kanban_notes(canal_id, position);
```

### Passo 3: Criar Tabela de Histórico

```sql
-- Criar tabela kanban_history
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
CREATE INDEX idx_kanban_history_canal ON kanban_history(canal_id);
CREATE INDEX idx_kanban_history_date ON kanban_history(performed_at DESC);
CREATE INDEX idx_kanban_history_visible ON kanban_history(canal_id, is_deleted)
WHERE is_deleted = FALSE;
```

### Passo 4: Verificar Instalação

```sql
-- Verificar distribuição de status
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

-- Verificar tabelas criadas
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('kanban_notes', 'kanban_history');
```

## ✅ Resultado Esperado

Após executar todos os scripts, você deve ter:

1. **Campos adicionados em `canais_monitorados`:**
   - `kanban_status` - com valores padrão definidos
   - `kanban_status_since` - com timestamp atual

2. **Tabela `kanban_notes` criada** - para armazenar notas

3. **Tabela `kanban_history` criada** - para histórico de ações

4. **Todos os 63 canais nossos** com status inicial:
   - Não monetizados: `em_teste_inicial`
   - Monetizados: `canal_constante`

## 🔧 Troubleshooting

### Erro: "column already exists"
- Ignorar, significa que o campo já foi criado anteriormente

### Erro: "relation does not exist"
- Verificar se a tabela `canais_monitorados` existe
- Verificar se está conectado ao banco correto

### Erro: "permission denied"
- Verificar se tem permissões de DDL no Supabase
- Pode ser necessário usar o service_role_key

## 📝 Notas
- Os scripts são idempotentes (podem ser executados múltiplas vezes)
- Use `IF NOT EXISTS` para evitar erros em re-execuções
- Todos os timestamps são em UTC com timezone