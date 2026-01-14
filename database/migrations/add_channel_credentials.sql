-- ============================================================
-- MIGRATION: Sistema de Credenciais OAuth por Canal
-- Data: 2025-12-22
-- Objetivo: Isolar credenciais OAuth por canal (1 canal = 1 Client ID/Secret)
-- ============================================================

-- ============================================================
-- PARTE 1: Criar tabela yt_channel_credentials
-- ============================================================

CREATE TABLE IF NOT EXISTS yt_channel_credentials (
  id SERIAL PRIMARY KEY,
  channel_id TEXT UNIQUE NOT NULL,
  client_id TEXT NOT NULL,
  client_secret TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Foreign key para garantir integridade
  CONSTRAINT fk_channel
    FOREIGN KEY (channel_id)
    REFERENCES yt_channels(channel_id)
    ON DELETE CASCADE
);

-- ============================================================
-- PARTE 2: Criar índices para performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_channel_credentials_channel_id
  ON yt_channel_credentials(channel_id);

-- ============================================================
-- PARTE 3: Migrar credenciais do Sans Limites (se existir)
-- ============================================================

DO $$
DECLARE
  sans_limites_channel_id TEXT := 'UCbB1WtTqBWYdSk3JE6iRNRw';
  proxy_exists BOOLEAN;
  creds_client_id TEXT;
  creds_client_secret TEXT;
BEGIN
  -- Verificar se proxy_c0000_1 existe
  SELECT EXISTS (
    SELECT 1 FROM yt_proxy_credentials
    WHERE proxy_name = 'proxy_c0000_1'
  ) INTO proxy_exists;

  IF proxy_exists THEN
    -- Buscar credenciais do proxy
    SELECT client_id, client_secret
    INTO creds_client_id, creds_client_secret
    FROM yt_proxy_credentials
    WHERE proxy_name = 'proxy_c0000_1';

    -- Inserir em yt_channel_credentials (se ainda não existe)
    INSERT INTO yt_channel_credentials (channel_id, client_id, client_secret)
    VALUES (sans_limites_channel_id, creds_client_id, creds_client_secret)
    ON CONFLICT (channel_id) DO NOTHING;

    RAISE NOTICE '[OK] Credenciais do Sans Limites migradas com sucesso';
  ELSE
    RAISE NOTICE '[AVISO] Proxy proxy_c0000_1 não encontrado - pular migração Sans Limites';
  END IF;
END $$;

-- ============================================================
-- PARTE 4: Validação
-- ============================================================

DO $$
BEGIN
    -- Validar tabela criada
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'yt_channel_credentials'
    ) THEN
        RAISE NOTICE '[OK] Tabela yt_channel_credentials criada com sucesso';
    ELSE
        RAISE WARNING '[ERRO] Falha ao criar tabela yt_channel_credentials';
    END IF;

    -- Validar foreign key
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'yt_channel_credentials'
        AND constraint_type = 'FOREIGN KEY'
    ) THEN
        RAISE NOTICE '[OK] Foreign key configurada corretamente';
    ELSE
        RAISE WARNING '[AVISO] Foreign key não foi criada';
    END IF;

    -- Validar índice
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'yt_channel_credentials'
        AND indexname = 'idx_channel_credentials_channel_id'
    ) THEN
        RAISE NOTICE '[OK] Índice criado com sucesso';
    ELSE
        RAISE WARNING '[AVISO] Índice não foi criado';
    END IF;

    -- Contar registros migrados
    DECLARE
      total_creds INTEGER;
    BEGIN
      SELECT COUNT(*) INTO total_creds FROM yt_channel_credentials;
      RAISE NOTICE '[OK] Total de credenciais: %', total_creds;
    END;
END $$;

-- ============================================================
-- ROLLBACK (comentado - descomentar se precisar reverter)
-- ============================================================

-- DROP TABLE IF EXISTS yt_channel_credentials CASCADE;
-- RAISE NOTICE '[ROLLBACK] Tabela yt_channel_credentials removida';

-- ============================================================
-- NOTAS IMPORTANTES
-- ============================================================

-- 1. Esta migration NÃO remove tabela yt_proxy_credentials
--    (mantém compatibilidade com código antigo)
--
-- 2. Foreign key CASCADE: se deletar canal em yt_channels,
--    credenciais são removidas automaticamente
--
-- 3. ON CONFLICT DO NOTHING: se rodar migration 2x, não dá erro
--
-- 4. Arquitetura nova:
--    - 1 canal = 1 linha em yt_channel_credentials
--    - Client ID/Secret únicos por canal
--    - Isolamento total entre canais
--
-- 5. Migration do Sans Limites:
--    - Apenas se proxy_c0000_1 existir
--    - Não falha se Sans Limites já tiver credenciais
