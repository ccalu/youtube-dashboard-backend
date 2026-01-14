-- ===============================================================================
-- MIGRATION: Proteção de Credenciais OAuth com RLS
-- ===============================================================================
-- Data: 2026-01-08
-- Objetivo: Bloquear acesso anônimo às tabelas sensíveis de OAuth
--
-- CONTEXTO:
-- Atualmente as tabelas yt_oauth_tokens, yt_proxy_credentials e
-- yt_channel_credentials estão acessíveis com anon_key, expondo
-- tokens de autenticação, proxies e credenciais sensíveis.
--
-- SOLUÇÃO:
-- 1. Ativar RLS (Row Level Security) nas 3 tabelas
-- 2. Criar políticas que BLOQUEIAM acesso com anon_key
-- 3. Permitir acesso APENAS com service_role_key
--
-- IMPORTANTE:
-- Após executar esta migration, o backend PRECISA usar service_role_key
-- para acessar essas tabelas, caso contrário retornará 403 Forbidden.
-- ===============================================================================

-- ===============================================================================
-- STEP 1: Ativar RLS (Row Level Security)
-- ===============================================================================

ALTER TABLE yt_oauth_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE yt_proxy_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE yt_channel_credentials ENABLE ROW LEVEL SECURITY;

-- ===============================================================================
-- STEP 2: Remover políticas antigas (se existirem)
-- ===============================================================================

DROP POLICY IF EXISTS "Block anon access to oauth tokens" ON yt_oauth_tokens;
DROP POLICY IF EXISTS "Block anon access to proxy credentials" ON yt_proxy_credentials;
DROP POLICY IF EXISTS "Block anon access to channel credentials" ON yt_channel_credentials;

-- ===============================================================================
-- STEP 3: Criar políticas restritivas
-- ===============================================================================
-- IMPORTANTE: Não criamos nenhuma política permissiva!
-- Resultado: anon_key → 403 Forbidden
--           service_role_key → Acesso total (bypass RLS)
-- ===============================================================================

-- Política para yt_oauth_tokens: BLOQUEIA TUDO
CREATE POLICY "Block anon access to oauth tokens"
ON yt_oauth_tokens
FOR ALL
TO anon
USING (false);

-- Política para yt_proxy_credentials: BLOQUEIA TUDO
CREATE POLICY "Block anon access to proxy credentials"
ON yt_proxy_credentials
FOR ALL
TO anon
USING (false);

-- Política para yt_channel_credentials: BLOQUEIA TUDO
CREATE POLICY "Block anon access to channel credentials"
ON yt_channel_credentials
FOR ALL
TO anon
USING (false);

-- ===============================================================================
-- VALIDAÇÃO (OPCIONAL)
-- ===============================================================================
-- Execute as queries abaixo no SQL Editor para verificar:
-- ===============================================================================

-- 1. Verificar se RLS está ativo (should_have_rls = true)
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE tablename IN ('yt_oauth_tokens', 'yt_proxy_credentials', 'yt_channel_credentials');

-- 2. Verificar políticas criadas
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
-- FROM pg_policies
-- WHERE tablename IN ('yt_oauth_tokens', 'yt_proxy_credentials', 'yt_channel_credentials');

-- 3. Testar acesso com anon_key (deve retornar 0 registros ou erro 403)
-- SELECT * FROM yt_oauth_tokens LIMIT 1;

-- ===============================================================================
-- FIM DA MIGRATION
-- ===============================================================================
-- Após executar:
-- 1. Adicionar SUPABASE_SERVICE_ROLE_KEY no Railway
-- 2. Restart do backend
-- 3. Validar que uploads continuam funcionando
-- ===============================================================================
