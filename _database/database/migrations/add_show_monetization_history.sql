-- =====================================================
-- MIGRATION: Adicionar show_monetization_history
-- Data: 2026-01-07
-- Autor: Claude Code
-- Descrição: Permite mostrar canais desmonetizados no dashboard
--            mantendo coleta automática apenas para canais ativos
-- =====================================================

-- 1. Adicionar nova coluna
ALTER TABLE yt_channels
ADD COLUMN IF NOT EXISTS show_monetization_history BOOLEAN DEFAULT TRUE;

-- 2. Comentário explicativo
COMMENT ON COLUMN yt_channels.show_monetization_history IS
'Controla visibilidade no dashboard de monetização.
TRUE = canal aparece no dashboard (ativo ou com histórico).
FALSE = canal oculto do dashboard.
Collectors usam is_monetized, dashboard usa show_monetization_history.';

-- 3. Marcar TODOS os canais com dados de monetização como visíveis
UPDATE yt_channels
SET show_monetization_history = TRUE
WHERE EXISTS (
    SELECT 1 FROM yt_daily_metrics m
    WHERE m.channel_id = yt_channels.channel_id
);

-- 4. Criar índice para performance
CREATE INDEX IF NOT EXISTS idx_yt_channels_show_history
ON yt_channels(show_monetization_history)
WHERE show_monetization_history = TRUE;

-- 5. Verificar resultado
SELECT
    channel_name,
    is_monetized,
    show_monetization_history,
    CASE
        WHEN is_monetized = TRUE THEN '🟢 Ativo (coleta diária)'
        WHEN show_monetization_history = TRUE THEN '🟡 Desmonetizado (com histórico)'
        ELSE '⚫ Desmonetizado (oculto)'
    END as status
FROM yt_channels
WHERE show_monetization_history = TRUE
ORDER BY is_monetized DESC, channel_name;

-- ✅ Migration concluída!
