-- ============================================================================
-- CORREÇÃO COMPLETA - 12 CANAIS COM ERRO
-- Data: 2025-12-18
-- Executar via Supabase SQL Editor ou psql
-- ============================================================================

-- BACKUP: Criar snapshot antes de executar
-- SELECT * FROM canais_monitorados WHERE id IN (16, 167, 222, 376, 715, 751, 757, 836, 837, 860, 863, 866);

BEGIN;

-- ============================================================================
-- 1. MARCAR CANAL QUE NÃO EXISTE COMO INATIVO (1 canal)
-- ============================================================================

UPDATE canais_monitorados
SET
    status = 'inativo',
    observacoes = 'Canal nao encontrado - URL invalida ou canal deletado (2025-12-18)'
WHERE id = 757;

-- ============================================================================
-- 2. CORRIGIR URLs DOS CANAIS QUE MUDARAM DE CHANNEL ID (2 canais)
-- ============================================================================

-- Legado de Lujo (ID 715)
UPDATE canais_monitorados
SET url_canal = 'https://www.youtube.com/channel/UCRr3CryY1tsiEZ4jfvshSbA'
WHERE id = 715;

-- Alan Watts Way (ID 837)
UPDATE canais_monitorados
SET url_canal = 'https://www.youtube.com/channel/UCMG8Yd66gZLXcrKMU2OMwJw'
WHERE id = 837;

-- ============================================================================
-- 3. CORRIGIR URLs DOS CANAIS QUE NUNCA COLETARAM (5 canais)
-- ============================================================================

-- Dusunen InsanX (ID 751) - 92k inscritos!
UPDATE canais_monitorados
SET url_canal = 'https://www.youtube.com/channel/UC-cfrvf_0RADvGM5UQTU7-g'
WHERE id = 751;

-- Al-Asatir Al-Muharrama (ID 836) - NOSSO CANAL
UPDATE canais_monitorados
SET url_canal = 'https://www.youtube.com/channel/UCw609uQ15kHcmAXh-wBhajw'
WHERE id = 836;

-- Financial Dynasties (ID 860) - NOSSO CANAL
UPDATE canais_monitorados
SET url_canal = 'https://www.youtube.com/channel/UCXb7D1wL1cCU8OUMltP9oDA'
WHERE id = 860;

-- Dynasties Financières (ID 863) - NOSSO CANAL
UPDATE canais_monitorados
SET url_canal = 'https://www.youtube.com/channel/UCdNsmU5wcXG1d313tXdu3Ug'
WHERE id = 863;

-- Нераскрытые Тайны (ID 866) - NOSSO CANAL
UPDATE canais_monitorados
SET url_canal = 'https://www.youtube.com/channel/UC2X74_c3YXEIuJp4Lr22MoA'
WHERE id = 866;

-- ============================================================================
-- 4. VALIDAÇÃO - CONTAR QUANTOS FORAM ATUALIZADOS
-- ============================================================================

-- Deve retornar 8 linhas atualizadas (1 inativo + 7 URLs corrigidas)
SELECT
    'Total de canais corrigidos' as operacao,
    COUNT(*) as quantidade
FROM canais_monitorados
WHERE id IN (715, 751, 757, 836, 837, 860, 863, 866);

-- Verificar status após update
SELECT
    id,
    nome_canal,
    url_canal,
    status,
    observacoes
FROM canais_monitorados
WHERE id IN (715, 751, 757, 836, 837, 860, 863, 866)
ORDER BY id;

COMMIT;

-- ============================================================================
-- RESULTADO ESPERADO:
-- - 1 canal marcado como 'inativo' (ID 757)
-- - 7 canais com URLs atualizadas (715, 751, 836, 837, 860, 863, 866)
-- - Próxima coleta deve ter ~99% de sucesso (em vez de 97%)
-- ============================================================================
