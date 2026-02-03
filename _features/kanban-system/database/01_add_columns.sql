-- Script 01: Adicionar campos na tabela canais_monitorados
-- Data: 28/01/2025
-- Objetivo: Adicionar campos para o sistema Kanban

-- Adicionar campo kanban_status
ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS kanban_status VARCHAR(50);

-- Adicionar campo kanban_status_since
ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS kanban_status_since TIMESTAMP WITH TIME ZONE;

-- Comentários sobre os campos
COMMENT ON COLUMN canais_monitorados.kanban_status IS
'Status do canal no Kanban. Valores possíveis:
- Para não monetizados: em_teste_inicial, demonstrando_tracao, em_andamento, monetizado
- Para monetizados: em_crescimento, em_testes_novos, canal_constante';

COMMENT ON COLUMN canais_monitorados.kanban_status_since IS
'Data/hora desde quando o canal está no status atual. Usado para calcular dias no status e futuros alertas.';

-- Definir status padrão para canais existentes
-- Canais não monetizados (tipo='nosso' AND monetizado=false)
UPDATE canais_monitorados
SET
    kanban_status = 'em_teste_inicial',
    kanban_status_since = CURRENT_TIMESTAMP
WHERE
    tipo = 'nosso'
    AND (monetizado = false OR monetizado IS NULL)
    AND kanban_status IS NULL;

-- Canais monetizados (tipo='nosso' AND monetizado=true)
UPDATE canais_monitorados
SET
    kanban_status = 'canal_constante',
    kanban_status_since = CURRENT_TIMESTAMP
WHERE
    tipo = 'nosso'
    AND monetizado = true
    AND kanban_status IS NULL;

-- Criar índice para melhor performance
CREATE INDEX IF NOT EXISTS idx_kanban_status ON canais_monitorados(tipo, kanban_status)
WHERE tipo = 'nosso';

-- Verificar resultado
SELECT
    COUNT(*) as total,
    monetizado,
    kanban_status,
    COUNT(*) as quantidade
FROM canais_monitorados
WHERE tipo = 'nosso'
GROUP BY monetizado, kanban_status
ORDER BY monetizado, kanban_status;