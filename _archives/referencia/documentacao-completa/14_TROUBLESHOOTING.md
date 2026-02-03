# 14 - Troubleshooting

**Guia completo de diagnóstico e solução de problemas comuns**

---

## Índice

1. [Problemas de Coleta](#problemas-de-coleta)
2. [Problemas de OAuth](#problemas-de-oauth)
3. [Problemas de Upload](#problemas-de-upload)
4. [Problemas de Database](#problemas-de-database)
5. [Diagnóstico Avançado](#diagnóstico-avançado)
6. [Scripts Úteis](#scripts-úteis)

---

## Problemas de Coleta

### 1. Quota Exceeded

**Sintomas:**
```
❌ Chave 2 esgotada (quotaExceeded)
⚠️  16/20 chaves esgotadas
```

**Causa:** Limite de 10,000 units/dia por API key excedido

**Diagnóstico:**
```bash
# Ver uso de quota
GET /api/stats

# Response:
{
  "total_keys": 20,
  "exhausted_keys": 16,
  "quota_units_used": 195230,
  "quota_available": 4770
}
```

**Soluções:**

**a) Aguardar reset (meia-noite UTC):**
```bash
# Quota reseta automaticamente às 00:00 UTC
# Sistema já detecta e reusa chaves no dia seguinte
```

**b) Adicionar mais API keys:**
```bash
# Google Cloud Console → Create API Key
# Railway → Add variable
YOUTUBE_API_KEY_33=AIzaSyAxxxxx
YOUTUBE_API_KEY_34=AIzaSyAxxxxx
```

**c) Reduzir frequência de coleta:**
```python
# main.py - Ajustar schedule
scheduler.add_job(
    run_collection,
    'cron',
    hour=5,  # Era: hour='*/6' (a cada 6h)
    minute=0
)
```

---

### 2. API Key Suspensa

**Sintomas:**
```
⚠️  Chave 5 suspensa temporariamente (badRequest)
```

**Causa:** Google detectou uso suspeito (muitas requests rápidas)

**Diagnóstico:**
```bash
# Verificar logs
Railway → Logs → Filter: "suspensa"

# Testar key manualmente
curl "https://www.googleapis.com/youtube/v3/channels?part=statistics&id=UCxxxxxx&key=AIzaSyAxxxxx"

# Response:
{
  "error": {
    "code": 400,
    "message": "Bad Request"
  }
}
```

**Soluções:**

**a) Reset de keys suspensas:**
```bash
# Endpoint manual
POST /api/reset-suspended-keys

# Ou aguardar (sistema tenta reativar após 1h)
```

**b) Reduzir rate limit:**
```python
# collector.py
class RateLimiter:
    def __init__(self):
        self.max_requests = 80  # Era: 90 (mais conservador)
```

---

### 3. Collection Fails (Nenhum Canal Coletado)

**Sintomas:**
```
✅ COLETA FINALIZADA - 0 vídeos coletados
```

**Diagnóstico:**
```python
# Verificar canais ativos
# Script: verificar_canais_ativos.py

from database import SupabaseClient

db = SupabaseClient()
response = db.supabase.table("canais_monitorados")\
    .select("*")\
    .eq("tipo", "minerado")\
    .execute()

print(f"Total canais: {len(response.data)}")

# Se retornar 0 → Problema!
```

**Causas:**
- Todos os canais desativados
- Filtro errado no código
- Database connection error

**Solução:**
```sql
-- Reativar canais
UPDATE canais_monitorados
SET ativo = TRUE
WHERE tipo = 'minerado';
```

---

### 4. Vídeos Não Aparecem no Dashboard

**Sintomas:**
- Coleta roda (logs OK)
- Vídeos não aparecem no frontend

**Diagnóstico:**
```sql
-- Verificar se vídeos foram salvos
SELECT COUNT(*) FROM videos_monitorados
WHERE published_at > NOW() - INTERVAL '7 days';

-- Se COUNT > 0: Vídeos existem
-- Se COUNT = 0: Coleta não salvou
```

**Causas:**

**a) Filtro de data no frontend:**
```typescript
// Frontend pede últimos 7 dias apenas
const response = await fetch('/api/videos?dias=7');

// Se vídeos são mais antigos, não aparecem
```

**Solução:**
```typescript
// Aumentar período
const response = await fetch('/api/videos?dias=30');
```

**b) Cache do browser:**
```bash
# Hard refresh
Ctrl + Shift + R (Chrome)
Cmd + Shift + R (Mac)
```

---

## Problemas de OAuth

### 1. Invalid Grant

**Sintomas:**
```
❌ Erro OAuth: Invalid Grant
400 Bad Request
```

**Causa:** Refresh token revogado ou expirado

**Diagnóstico:**
```python
# verificar_tokens.py
from yt_uploader.database import get_oauth_tokens

tokens = get_oauth_tokens("UCxxxxxx")

if tokens:
    print(f"Access token: {tokens['access_token'][:20]}...")
    print(f"Refresh token: {tokens['refresh_token'][:20]}...")
    print(f"Expiry: {tokens.get('token_expiry')}")
else:
    print("❌ Sem tokens para este canal")
```

**Soluções:**

**a) Reautorizar canal:**
```bash
python reautorizar_canal.py UCxxxxxx
```

**b) Verificar revogação manual:**
```
https://myaccount.google.com/permissions
→ Verificar se app foi revogado
→ Se sim, reautorizar
```

---

### 2. Redirect URI Mismatch

**Sintomas:**
```
Error 400: redirect_uri_mismatch
```

**Causa:** Redirect URI não configurado no Google Cloud

**Diagnóstico:**
```bash
# Verificar erro completo
# "The redirect URI in the request: http://localhost:8000/oauth/callback
#  does not match the ones authorized for the OAuth client"
```

**Solução:**
```
Google Cloud Console → Credentials → Edit OAuth client
→ Authorized redirect URIs → Add:
  http://localhost:8000/oauth/callback
  https://youtube-dashboard-backend-production.up.railway.app/oauth/callback
```

---

### 3. Token Expira Muito Rápido

**Sintomas:**
- Erro "Token expired" a cada coleta
- Sistema não consegue renovar

**Diagnóstico:**
```python
# Verificar se refresh_token existe
tokens = get_oauth_tokens("UCxxxxxx")
print(f"Refresh token: {tokens.get('refresh_token')}")

# Se None ou vazio → Problema!
```

**Causa:** Autorização sem `prompt=consent`

**Solução:**
```python
# autorizar_canal.py
# SEMPRE usar prompt=consent para garantir refresh_token

flow.authorization_url(
    access_type='offline',
    prompt='consent',  # ← ESSENCIAL!
    include_granted_scopes='true'
)
```

---

### 4. Nenhuma Métrica Retornada (Analytics API)

**Sintomas:**
```
[Canal Exemplo] Métricas diárias: 0 dias salvos
```

**Diagnóstico:**
```python
# Test manual
import requests

headers = {"Authorization": f"Bearer {access_token}"}
params = {
    "ids": f"channel=={channel_id}",
    "startDate": "2024-01-01",
    "endDate": "2024-01-10",
    "metrics": "views"
}

resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params=params,
    headers=headers
)

print(resp.status_code)  # Deve ser 200
print(resp.json())
```

**Causas:**

**a) Canal não monetizado:**
```
# YouTube Analytics só retorna revenue se canal está no Partner Program
# Verificar: YouTube Studio → Monetização
```

**b) Delay de dados:**
```python
# YouTube tem delay de 2-3 dias para revenue
# Pedir dados de 3 dias atrás:
end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
```

**c) Período sem views:**
```
# Se canal teve 0 views no período, API não retorna dados
# Normal para canais novos ou inativos
```

---

## Problemas de Upload

### 1. Download Falha (Google Drive)

**Sintomas:**
```
❌ Erro ao baixar do Google Drive: file too large
```

**Causa:** Google Drive virus scan warning (arquivos >25MB)

**Diagnóstico:**
```bash
# Testar URL manualmente
curl -L "https://drive.google.com/uc?id=FILE_ID" --output test.mp4

# Se retornar HTML ao invés de vídeo → Virus scan blocking
```

**Solução:**
```python
# ✅ CORRETO: Usar gdown (lida com virus scan)
import gdown
gdown.download(drive_url, output_path, fuzzy=True)  # fuzzy=True é essencial

# ❌ ERRADO: requests não funciona
import requests
requests.get(drive_url)  # Retorna HTML
```

**Verificar permissões:**
```
Google Drive → Arquivo → Compartilhar
→ "Anyone with the link" → Viewer
→ Copy link
```

---

### 2. Upload Timeout

**Sintomas:**
```
❌ Upload falhou: Timeout after 300s
```

**Causa:** Vídeo muito grande ou internet lenta

**Soluções:**

**a) Aumentar timeout:**
```python
# uploader.py
media = MediaFileUpload(
    video_path,
    chunksize=1024*1024*10,  # Era: 5MB → Agora: 10MB (chunks maiores)
    resumable=True
)
```

**b) Reduzir batch size:**
```bash
# Railway env var
UPLOAD_WORKER_BATCH_SIZE=2  # Era: 5
```

---

### 3. UTF-8 Encoding Error

**Sintomas:**
```
❌ Erro: invalid character in title
Title: "Batalla de Estalingrado � 1942"  # Caractere � quebrado
```

**Causa:** Caracteres especiais não sanitizados

**Solução:** Sistema já tem sanitização implementada
```python
# uploader.py - Já implementado
titulo_sanitized = unicodedata.normalize('NFC', titulo)
titulo_sanitized = titulo_sanitized.encode('utf-8', errors='ignore').decode('utf-8')
titulo_sanitized = titulo_sanitized.replace('\ufffd', 'O')
```

**Se ainda ocorrer:**
```python
# Debug: Ver caracteres problemáticos
print(repr(titulo))  # Mostra bytes exatos
```

---

### 4. Worker Não Processa Fila

**Sintomas:**
```
# Logs silenciosos (nenhuma mensagem de upload)
```

**Diagnóstico:**
```bash
# 1. Verificar se worker está habilitado
Railway → Variables → UPLOAD_WORKER_ENABLED=true

# 2. Verificar startup delay
# Logs: "Upload worker aguardando 180s"
# Aguardar 3 minutos

# 3. Verificar circuit breaker
# Logs: "🚨 WORKER DESATIVADO após 5 erros consecutivos"
```

**Soluções:**

**a) Worker desabilitado:**
```bash
Railway → Variables → UPLOAD_WORKER_ENABLED=true
Railway → Restart
```

**b) Circuit breaker ativado:**
```bash
# Redeployar Railway (reseta worker)
Railway → Deployments → Latest → Redeploy
```

**c) Fila vazia (não é erro):**
```sql
-- Verificar fila
SELECT * FROM yt_upload_queue WHERE status = 'pending';
```

---

## Problemas de Database

### 1. Connection Timeout

**Sintomas:**
```
Error: Connection timeout to Supabase
```

**Diagnóstico:**
```python
# Test connection
from database import SupabaseClient

try:
    db = SupabaseClient()
    response = db.supabase.table("canais_monitorados").select("count").execute()
    print(f"✅ Connection OK - {len(response.data)} canais")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

**Causas:**

**a) Supabase down:**
```
https://status.supabase.com
→ Verificar se há incidents
```

**b) Rate limit:**
```
Supabase free tier:
- 500MB database
- 2GB bandwidth/mês
- 50k requests/dia

Se exceder → Throttling
```

**Solução:**
```bash
# Upgrade Supabase plan
Supabase → Project → Settings → Billing
→ Pro plan ($25/mês)
```

---

### 2. RLS (Row Level Security) Bloqueando Queries

**Sintomas:**
```
Query OK, mas retorna dados vazios []
```

**Causa:** Políticas RLS bloqueando acesso

**Diagnóstico:**
```sql
-- Verificar políticas
SELECT * FROM pg_policies WHERE tablename = 'yt_oauth_tokens';

-- Se existir policy → Usar service_role_key
```

**Solução:**
```python
# Usar service_role_key para bypass RLS
from database import SupabaseClient

db = SupabaseClient()
# Supabase client já usa SUPABASE_KEY (anon)

# Para tables com RLS (como yt_oauth_tokens):
# Backend usa SUPABASE_SERVICE_ROLE_KEY automaticamente
```

---

### 3. Unique Constraint Violation

**Sintomas:**
```
Error: duplicate key value violates unique constraint
```

**Causa:** Tentando inserir registro duplicado

**Solução:**
```python
# ❌ ERRADO: Insert direto
db.supabase.table("yt_daily_metrics").insert({
    "channel_id": "UCxxxxxx",
    "date": "2024-01-10",
    "revenue": 12.45
}).execute()

# ✅ CORRETO: Upsert (insert ou update)
db.supabase.table("yt_daily_metrics").upsert({
    "channel_id": "UCxxxxxx",
    "date": "2024-01-10",
    "revenue": 12.45
}, on_conflict='channel_id,date').execute()
```

---

## Diagnóstico Avançado

### 1. Debug Mode

**Ativar logs detalhados:**
```python
# main.py (início do arquivo)
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Era: INFO
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
```

**Logs DEBUG incluem:**
- Todas as requisições HTTP
- SQL queries (Supabase)
- OAuth token refresh
- Rate limiter stats

---

### 2. Request Tracing

**Adicionar trace ID:**
```python
import uuid

# Gerar trace_id único por request
trace_id = str(uuid.uuid4())[:8]
logger.info(f"[{trace_id}] Processando upload {upload_id}")
```

**Benefício:** Rastrear requests específicos nos logs

---

### 3. Performance Profiling

**Medir tempo de operações:**
```python
import time

start = time.time()
# ... operação ...
elapsed = time.time() - start

logger.info(f"⏱️  Operação levou {elapsed:.2f}s")
```

**Identificar gargalos:**
```python
# Exemplo: Coleta de canais
start = time.time()
response = db.supabase.table("canais_monitorados").select("*").execute()
elapsed = time.time() - start

if elapsed > 5:
    logger.warning(f"⚠️  Query lenta: {elapsed:.2f}s (> 5s)")
```

---

### 4. Memory Profiling

**Instalar:**
```bash
pip install memory-profiler
```

**Usar:**
```python
from memory_profiler import profile

@profile
def collect_videos():
    # ... código ...
    pass

# Logs mostram uso de memória linha por linha
```

---

## Scripts Úteis

### 1. Scripts de Diagnóstico (100+ no repo)

**Localização:** `D:\ContentFactory\youtube-dashboard-backend\*.py`

**Principais:**

**a) Verificar canais:**
```bash
python verificar_canais_ativos.py
# Lista canais ativos/inativos

python listar_todos_subnichos_linguas.py
# Mostra subnichos e línguas configurados
```

**b) Verificar OAuth:**
```bash
python check_tokens_simple.py
# Verifica tokens de todos os canais

python diagnostico_oauth_alemao.py
# Diagnóstico específico de um canal
```

**c) Testar coleta:**
```bash
python rodar_coleta_oauth_manual.py
# Força coleta OAuth manualmente

python coleta_historico_AUTO_REFRESH.py
# Coleta histórico com auto-refresh de tokens
```

**d) Verificar monetização:**
```bash
python verificar_setup_monetizacao.py
# Verifica setup completo de monetização

python investigar_melhor_dia.py
# Análise de melhores dias de revenue
```

---

### 2. SQL Queries Úteis

**Verificar última coleta:**
```sql
SELECT
  canal_id,
  MAX(published_at) as ultimo_video
FROM videos_monitorados
GROUP BY canal_id
ORDER BY ultimo_video DESC;
```

**Verificar revenue:**
```sql
SELECT
  channel_id,
  SUM(revenue) as total_revenue,
  COUNT(*) as dias_com_dados
FROM yt_daily_metrics
WHERE date > NOW() - INTERVAL '30 days'
  AND is_estimate = FALSE
GROUP BY channel_id
ORDER BY total_revenue DESC;
```

**Verificar uploads pendentes:**
```sql
SELECT
  status,
  COUNT(*) as total
FROM yt_upload_queue
GROUP BY status;

-- Resultado:
-- pending:    5
-- downloading: 2
-- uploading:  1
-- completed:  234
-- failed:     3
```

**Verificar notificações:**
```sql
SELECT
  tipo,
  vista,
  COUNT(*) as total
FROM notificacoes
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY tipo, vista
ORDER BY total DESC;
```

---

### 3. Comandos Railway CLI

**Instalar:**
```bash
npm install -g @railway/cli
```

**Login:**
```bash
railway login
```

**Ver logs em tempo real:**
```bash
railway logs
```

**Executar comando:**
```bash
railway run python script.py
```

**Ver variáveis:**
```bash
railway variables
```

---

### 4. Ferramentas de Teste

**a) Test API endpoints:**
```bash
# Install HTTPie
pip install httpie

# Test
http GET localhost:8000/api/canais
http POST localhost:8000/api/add-canal url_canal="https://youtube.com/@exemplo"
```

**b) Test OAuth flow:**
```python
# test_oauth.py
from yt_uploader.oauth_manager import OAuthManager

try:
    credentials = OAuthManager.get_valid_credentials("UCxxxxxx")
    print("✅ OAuth OK")
    print(f"Token: {credentials.token[:20]}...")
except Exception as e:
    print(f"❌ OAuth failed: {e}")
```

**c) Test upload completo:**
```bash
python test_wizard_final.py
# Wizard interativo para testar upload end-to-end
```

---

## Checklist de Diagnóstico

### Quando algo não funciona:

1. **Verificar logs:**
   - [ ] Railway → Logs → Últimos 100 logs
   - [ ] Procurar por ERROR ou ❌
   - [ ] Anotar trace ID se tiver

2. **Verificar environment:**
   - [ ] Railway → Variables → Todas configuradas?
   - [ ] Env vars sensíveis (API keys, secrets)
   - [ ] Service_role_key para OAuth

3. **Verificar serviços externos:**
   - [ ] Supabase: https://status.supabase.com
   - [ ] Google APIs: https://status.cloud.google.com
   - [ ] Railway: https://status.railway.app

4. **Testar componente isolado:**
   - [ ] Database connection
   - [ ] OAuth tokens
   - [ ] API keys
   - [ ] Google Drive access

5. **Verificar dados:**
   - [ ] Tabela tem registros?
   - [ ] Registros estão corretos?
   - [ ] Foreign keys válidas?

6. **Tentar solução simples primeiro:**
   - [ ] Restart Railway
   - [ ] Limpar cache browser
   - [ ] Hard refresh (Ctrl+Shift+R)
   - [ ] Aguardar (delays, rate limits)

7. **Se continuar:**
   - [ ] Deploy rollback (último working)
   - [ ] Desabilitar feature com problema
   - [ ] Pedir ajuda (logs + contexto)

---

## Contatos de Emergência

**Supabase Support:**
- Dashboard: https://app.supabase.com
- Docs: https://supabase.com/docs
- Discord: https://discord.supabase.com

**Railway Support:**
- Dashboard: https://railway.app
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

**Google Cloud Support:**
- Console: https://console.cloud.google.com
- Docs: https://cloud.google.com/docs
- Support: https://cloud.google.com/support

---

**Última atualização:** 2024-01-12
