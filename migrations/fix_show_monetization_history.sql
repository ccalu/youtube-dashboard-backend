-- =====================================================
-- MIGRATION: Corrigir show_monetization_history
-- Data: 2026-01-07
-- Descrição: Mostrar apenas canais monetizados + 3 desmonetizados
--            Total: 18 canais (15 ativos + 3 desmonetizados)
-- =====================================================

-- 1. Marcar TODOS como FALSE primeiro
UPDATE yt_channels
SET show_monetization_history = FALSE;

-- 2. Marcar como TRUE apenas:
--    - Canais ativos (is_monetized=TRUE) - 15 canais
--    - 3 canais que FORAM desmonetizados (com histórico)
UPDATE yt_channels
SET show_monetization_history = TRUE
WHERE
    -- Canais ativos (15 canais)
    is_monetized = TRUE
    OR
    -- 3 canais desmonetizados (com histórico de monetização)
    channel_id IN (
        'UCpWl6TezIQFXod8H2q3uw-w',  -- Chroniques Anciennes
        'UCV9aMsA0swcuExud2tZSlUg',  -- Reis Perversos
        'UCD9mEdIqxsDqkn0Vw2UC91A'   -- Contes Sinistres
    );

-- 3. Verificar resultado
SELECT
    channel_name,
    is_monetized,
    show_monetization_history,
    CASE
        WHEN is_monetized = TRUE THEN '🟢 Ativo (coleta diária)'
        WHEN show_monetization_history = TRUE THEN '🟡 Desmonetizado (com histórico)'
        ELSE '⚫ Nunca monetizado (oculto)'
    END as status
FROM yt_channels
ORDER BY
    is_monetized DESC,
    show_monetization_history DESC,
    channel_name;

-- 4. Contagem final
SELECT
    '✅ Total visível no dashboard' as metrica,
    COUNT(*) as quantidade
FROM yt_channels
WHERE show_monetization_history = TRUE

UNION ALL

SELECT
    '🟢 Canais ativos (coleta diária)' as metrica,
    COUNT(*) as quantidade
FROM yt_channels
WHERE is_monetized = TRUE

UNION ALL

SELECT
    '🟡 Canais desmonetizados (com histórico)' as metrica,
    COUNT(*) as quantidade
FROM yt_channels
WHERE is_monetized = FALSE AND show_monetization_history = TRUE

UNION ALL

SELECT
    '⚫ Canais nunca monetizados (ocultos)' as metrica,
    COUNT(*) as quantidade
FROM yt_channels
WHERE is_monetized = FALSE AND show_monetization_history = FALSE;

-- ✅ Migration concluída!
-- Resultado esperado:
--   ✅ Total visível: 18 canais
--   🟢 Ativos: 15 canais
--   🟡 Desmonetizados: 3 canais
--   ⚫ Ocultos: 34 canais
