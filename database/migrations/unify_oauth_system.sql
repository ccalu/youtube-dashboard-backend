-- ============================================================
-- MIGRATION: Unificação Sistema OAuth Multi-Proxy
-- Data: 2025-12-22
-- Objetivo: Preparar sistema para upload multi-proxy
-- ============================================================

-- 1. UNIFICAR SCHEMA yt_channels
-- Adicionar colunas que faltam (sistema monetização + upload)
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS is_monetized BOOLEAN DEFAULT false;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS lingua TEXT DEFAULT 'en';
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS subnicho TEXT;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS default_playlist_id TEXT;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS monetization_start_date DATE;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS total_subscribers INTEGER;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS total_videos INTEGER;
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE yt_channels ADD COLUMN IF NOT EXISTS proxy_name TEXT;

-- Criar índice para performance
CREATE INDEX IF NOT EXISTS idx_channels_proxy ON yt_channels(proxy_name);
CREATE INDEX IF NOT EXISTS idx_channels_monetized ON yt_channels(is_monetized);

-- 2. CRIAR/ATUALIZAR PROXY SANS LIMITES
-- Credenciais OAuth do proxy C0008.1 (Sans Limites)
INSERT INTO yt_proxy_credentials (proxy_name, client_id, client_secret)
VALUES (
  'proxy_c0008_1',
  '645592918326-62kla99vhdvmr6nhkb2rr8a2vf51jlcf',
  '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'
)
ON CONFLICT (proxy_name) DO UPDATE
SET
  client_id = EXCLUDED.client_id,
  client_secret = EXCLUDED.client_secret;

-- 3. ATUALIZAR SANS LIMITES COM PROXY_NAME
UPDATE yt_channels
SET proxy_name = 'proxy_c0008_1'
WHERE channel_id = 'UCbB1WtTqBWYdSk3JE6iRNRw'
  AND (proxy_name IS NULL OR proxy_name = '');

-- 4. VALIDAÇÃO
-- Verificar se Sans Limites está configurado corretamente
DO $$
DECLARE
    canal_count INTEGER;
    proxy_count INTEGER;
BEGIN
    -- Verificar canal Sans Limites
    SELECT COUNT(*) INTO canal_count
    FROM yt_channels
    WHERE channel_id = 'UCbB1WtTqBWYdSk3JE6iRNRw'
      AND proxy_name = 'proxy_c0008_1';

    IF canal_count = 0 THEN
        RAISE WARNING 'Sans Limites não encontrado ou sem proxy_name configurado!';
    ELSE
        RAISE NOTICE 'Sans Limites configurado corretamente ✓';
    END IF;

    -- Verificar proxy
    SELECT COUNT(*) INTO proxy_count
    FROM yt_proxy_credentials
    WHERE proxy_name = 'proxy_c0008_1';

    IF proxy_count = 0 THEN
        RAISE WARNING 'Proxy proxy_c0008_1 não encontrado!';
    ELSE
        RAISE NOTICE 'Proxy proxy_c0008_1 cadastrado ✓';
    END IF;
END $$;
