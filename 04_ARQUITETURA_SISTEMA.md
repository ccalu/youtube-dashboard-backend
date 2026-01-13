# 04 - Arquitetura do Sistema

## Índice
1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Fluxo de Dados](#fluxo-de-dados)
4. [Componentes Principais](#componentes-principais)
5. [Integrações Externas](#integrações-externas)
6. [Segurança e Autenticação](#segurança-e-autenticação)
7. [Escalabilidade](#escalabilidade)

---

## Visão Geral da Arquitetura

### Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Lovable)                       │
│                    React + TypeScript + Vite                    │
│              https://[project-name].lovable.app                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS (REST API)
                             │ CORS habilitado
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (Railway)                        │
│                   FastAPI + Python 3.11+                        │
│                   Port: 8000 (configurável)                     │
├─────────────────────────────────────────────────────────────────┤
│  Módulos:                                                       │
│  • main.py (1122 linhas) - API REST completa                   │
│  • collector.py (792 linhas) - YouTube data collector          │
│  • notifier.py (449 linhas) - Sistema de notificações          │
│  • monetization_collector.py (860 linhas) - OAuth revenue      │
│  • financeiro.py - Gestão financeira manual                    │
│  • yt_uploader/ - Sistema de upload automatizado               │
│  • database.py (1141 linhas) - Supabase client                 │
└────────────────────┬──────────────────┬─────────────────────────┘
                     │                  │
                     │                  │ OAuth 2.0 + API Keys
                     │                  ▼
                     │         ┌─────────────────────┐
                     │         │  Google APIs        │
                     │         ├─────────────────────┤
                     │         │ • YouTube Data v3   │
                     │         │ • YouTube Analytics │
                     │         │ • Google Sheets     │
                     │         │ • Google Drive      │
                     │         └─────────────────────┘
                     │
                     │ PostgreSQL (postgREST)
                     ▼
        ┌──────────────────────────┐
        │    SUPABASE (Database)   │
        ├──────────────────────────┤
        │ • PostgreSQL 15+         │
        │ • Row Level Security     │
        │ • Real-time subscriptions│
        │ • Storage (futuro)       │
        └──────────────────────────┘
```

### Modelo de Deployment

**Frontend (Lovable):**
- Deploy automático via Git push
- CDN global
- HTTPS certificado automaticamente
- Zero-downtime deployments

**Backend (Railway):**
- Deploy automático via GitHub
- Branch: `main`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health checks: `GET /health`
- Logs centralizados

**Database (Supabase):**
- Managed PostgreSQL
- Backups automáticos (diários)
- Connection pooling
- Replication (futuro)

---

## Stack Tecnológico

### Backend Stack

| Tecnologia | Versão | Uso | Arquivo |
|-----------|--------|-----|---------|
| **Python** | 3.11+ | Runtime principal | - |
| **FastAPI** | 0.115.0 | Framework web assíncrono | main.py |
| **Uvicorn** | 0.31.0 | ASGI server (production) | Railway start |
| **Supabase Python** | 2.9.1 | Client PostgreSQL | database.py |
| **aiohttp** | 3.10.11 | HTTP async requests | collector.py |
| **gspread** | 6.1.4 | Google Sheets integration | sheets.py |
| **google-api-python-client** | 2.116.0 | YouTube/Drive APIs | uploader.py |
| **google-auth-oauthlib** | 1.2.1 | OAuth 2.0 flow | oauth_manager.py |
| **httpx[socks]** | 0.26.0 | HTTP client com proxy support | monetization |
| **gdown** | 5.2.0 | Google Drive downloader | uploader.py |
| **requests** | 2.31.0 | HTTP client sync | financeiro.py |
| **python-dateutil** | 2.9.0 | Date parsing | utilities |
| **pydantic** | 2.9.2 | Data validation | models |
| **python-dotenv** | 1.0.0 | Env variables | .env |

**Ver:** `requirements.txt` para lista completa

### Frontend Stack (Lovable)

```typescript
// Stack principal (inferido dos arquivos frontend)
- React 18+
- TypeScript
- Vite (build tool)
- TailwindCSS
- Shadcn/ui (components)
- React Query (data fetching)
- Recharts (gráficos)
- Lucide React (ícones)
```

### Database Stack

**PostgreSQL 15+ (via Supabase)**
- PostgREST (API REST automática)
- pg_cron (scheduled jobs)
- pgvector (futuro: ML/AI)
- Row Level Security (RLS)
- Foreign key constraints
- JSON/JSONB support

---

## Fluxo de Dados

### 1. Coleta de Dados YouTube (Mining)

```
┌─────────────────────────────────────────────────────────────────┐
│                   COLETA AUTOMÁTICA (4x/dia)                    │
└─────────────────────────────────────────────────────────────────┘

[Frontend] → POST /api/force-collector
             ↓
[Backend] → collector.py inicializa
             ↓
1. database.py → Busca canais ativos (status="ativo")
             ↓
2. YouTubeCollector (collector.py):
   - Reset state (failed_canals, quota_units)
   - Rotação de 20 API keys (KEY_3 a KEY_10 + KEY_21 a KEY_32)
   - Rate limiter: 90 req/100s por key
   - Quota tracker: 10,000 units/key/dia
             ↓
3. Para cada canal:
   a) extract_channel_identifier() → Parse URL
   b) get_channel_id() → Resolve handle/@username (1-2 requisições)
   c) get_channel_info() → Inscritos, vídeos (1 requisição)
   d) get_channel_videos() → Últimos 30 dias (N requisições)
   e) get_video_details() → Batch de 50 vídeos (1 requisição/batch)
   f) calculate_views_by_period() → Calcula views_7d/15d/30d
             ↓
4. Salvar dados:
   - database.save_canal_data() → dados_canais_historico
   - database.save_videos_data() → videos_historico
   - database.update_last_collection() → ultima_coleta timestamp
             ↓
5. Criar log:
   - database.create_coleta_log() → coletas_historico
   - Status: sucesso/erro
   - Métricas: canais, vídeos, requisições, duração
             ↓
[Frontend] ← Response 200 OK
             {"status": "success", "canais": 263, "videos": 8547}
```

**Custo de Quota:**
- Canal completo (30 dias): ~150-200 units
- 263 canais: ~40,000-50,000 units
- 20 chaves: 200,000 units/dia disponíveis
- **Margem:** 4x de sobra

### 2. Sistema de Notificações (Inteligente)

```
┌─────────────────────────────────────────────────────────────────┐
│              VERIFICAÇÃO AUTOMÁTICA (4x/dia)                    │
└─────────────────────────────────────────────────────────────────┘

[Backend Scheduler] → notifier.py
             ↓
1. NotificationChecker.check_and_create_notifications():
   - Busca regras ativas ordenadas (views_minimas ASC)
   - Hierarquia: 10k/24h → 50k/7d → 100k/30d
             ↓
2. Para cada regra:
   get_videos_that_hit_milestone():
   a) Query videos_historico JOIN canais_monitorados
   b) Filtros:
      - data_publicacao >= cutoff (período da regra)
      - views_atuais >= views_minimas
      - tipo_canal = regra.tipo_canal (se especificado)
      - subnicho IN regra.subnichos (se especificado)
   c) Agrupa por video_id (pega mais recente)
             ↓
3. Anti-duplicação:
   a) cleanup_duplicate_notifications() → Remove duplicatas não vistas
   b) get_unread_notification() → Busca notificação pendente
   c) video_already_seen() → Verifica se já viu marco maior/igual
             ↓
4. Lógica de elevação:
   SE notificação não vista existe:
      SE nova_regra.views > regra_anterior.views:
         → update_notification() (10k → 50k → 100k)
      SENÃO:
         → PULA (já notificou)
   SENÃO SE nunca viu marco maior/igual:
      → create_notification()
             ↓
5. Salvar no banco:
   - notificacoes (vista=false)
   - Campos: video_id, canal_id, views_atingidas, periodo_dias, tipo_alerta
             ↓
[Frontend] ← Notificação aparece em real-time
             Badge contador atualiza
```

**Regras Padrão:**
- 10k views em 24h
- 50k views em 7d
- 100k views em 30d

**Filtros Suportados:**
- Por subnicho (ex: "História Antiga", "Biografias")
- Por tipo de canal (nosso/minerado/ambos)
- Por língua (via canais_monitorados)

### 3. Coleta de Monetização (OAuth)

```
┌─────────────────────────────────────────────────────────────────┐
│              COLETA AUTOMÁTICA (1x/dia às 5 AM)                 │
└─────────────────────────────────────────────────────────────────┘

[Railway Scheduler] → monetization_oauth_collector.py
             ↓
1. Buscar canais monetizados:
   - yt_channels WHERE is_monetized=true
   - Total: 16 canais (2025-01)
             ↓
2. Para cada canal:
   a) get_proxy_credentials() OU get_channel_credentials()
      → Busca client_id/client_secret (RLS protegido)
   b) get_tokens() → Busca refresh_token
   c) refresh_access_token() → OAuth refresh
   d) update_tokens() → Salva novo access_token
             ↓
3. Coletar métricas (YouTube Analytics API):

   MÉTRICAS DIÁRIAS (últimos 10 dias):
   - collect_daily_metrics():
     * estimatedRevenue (USD)
     * views, likes, comments, shares
     * subscribersGained/Lost
     * estimatedMinutesWatched
     * averageViewDuration/Percentage
     → Salva em yt_daily_metrics

   MÉTRICAS POR PAÍS (ontem):
   - collect_country_metrics():
     * views, revenue, watch_time por country_code
     → Salva em yt_country_metrics

   MÉTRICAS POR VÍDEO (últimos 10 dias):
   - collect_video_metrics():
     * revenue, views, likes, comments por video
     * Top 50 vídeos
     → Salva em yt_video_metrics + yt_video_daily

   ANALYTICS AVANÇADO (ontem):
   - collect_traffic_sources() → yt_traffic_summary
   - collect_search_terms() → yt_search_analytics
   - collect_suggested_videos() → yt_suggested_sources
   - collect_demographics() → yt_demographics
   - collect_device_metrics() → yt_device_metrics
             ↓
4. Conversão USD → BRL:
   - Frontend faz conversão em runtime
   - Taxa obtida de AwesomeAPI
   - Armazenado em USD no banco
             ↓
5. Log de coleta:
   - yt_collection_logs (status, message)
   - Status: success/error
             ↓
[Backend] ← Dados disponíveis para dashboard
```

**Importante:**
- YouTube Analytics tem **delay de 2-3 dias** para revenue
- Não sobrescrever revenue=0 se já tem revenue>0
- OAuth usa client_id/secret do proxy (protegido com RLS)
- Não usa YouTube Data API v3 (economiza quota)

### 4. Upload Automatizado de Vídeos

```
┌─────────────────────────────────────────────────────────────────┐
│          UPLOAD QUEUE SYSTEM (Processamento Contínuo)           │
└─────────────────────────────────────────────────────────────────┘

[Frontend] → POST /api/upload-queue/enqueue
             {"channel_id": "UCxxx", "spreadsheet_id": "1ABC..."}
             ↓
1. spreadsheet_scanner.py:
   - Conecta Google Sheets (service_account.json)
   - Lê linha com status="ready"
   - Extrai: video_url, titulo, descricao, lingua
   - Atualiza status="enqueued"
             ↓
2. Salva na fila:
   - INSERT INTO yt_upload_queue
   - status="pending"
   - position (ordem de chegada)
             ↓
3. queue_worker.py processa (asyncio):

   Semáforo: Max 3 uploads simultâneos
             ↓
   a) Atualiza status="processing"
   b) uploader.download_video():
      - gdown (Google Drive)
      - Bypass virus scan warning
      - Valida arquivo (tamanho > 100KB)

   c) uploader.upload_to_youtube():
      - oauth_manager.get_valid_credentials()
      - YouTube Data API v3 (upload)
      - Modo: privacyStatus="private" (RASCUNHO)
      - Adiciona à playlist (se configurado)

   d) Atualiza planilha:
      - status="uploaded"
      - video_id, upload_date

   e) Limpa arquivo temporário
             ↓
4. Atualiza fila:
   - status="completed"/"failed"
   - Retry: 3 tentativas automáticas
             ↓
[Frontend] ← GET /api/upload-queue
             Lista fila em tempo real
```

**Configuração:**
- Max 3 uploads paralelos (semáforo)
- Retry automático (3x)
- Timeout: 30min por upload
- Temp path: `/tmp/videos`

---

## Componentes Principais

### 1. API REST (main.py)

**Arquitetura:**
```python
# main.py (1122 linhas)

# FastAPI app
app = FastAPI(
    title="YouTube Dashboard API",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lovable frontend
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# Dependency injection
db_client = SupabaseClient()

# Routers (agrupados por funcionalidade)
# - /api/canais (GET, POST, DELETE)
# - /api/videos (GET)
# - /api/notificacoes (GET, PATCH, POST)
# - /api/coletas (POST, GET, DELETE)
# - /api/financeiro (GET, POST, PATCH, DELETE)
# - /api/upload-queue (GET, POST, PATCH)
# - /api/monetization (GET)
# - /health (GET)
```

**Endpoints Principais:**
- `GET /api/canais`: Lista canais com filtros avançados
- `GET /api/canais-tabela`: Nossos canais agrupados por subnicho
- `GET /api/videos`: Lista vídeos com filtros
- `POST /api/force-collector`: Inicia coleta manual
- `GET /api/notificacoes`: Lista notificações com filtros
- `POST /api/notificacoes/marcar-todas-vistas`: Marca como vistas
- `GET /api/subniche-trends`: Tendências por subnicho

**Ver:** `08_API_ENDPOINTS_COMPLETA.md` para referência completa

### 2. YouTube Collector (collector.py)

**Classe Principal:**
```python
class YouTubeCollector:
    """
    Coletor de dados YouTube com:
    - 20 API keys (rotação automática)
    - Rate limiter (90 req/100s)
    - Quota tracker (10k units/key/dia)
    - Channel ID cache (otimização)
    - Retry logic (exponential backoff)
    """

    def __init__(self):
        # Carrega 20 keys (KEY_3-10 + KEY_21-32)
        self.api_keys = [...]

        # Rate limiter por key
        self.rate_limiters = {i: RateLimiter() for i in range(20)}

        # Rastreamento
        self.exhausted_keys_date: Dict[int, date] = {}
        self.suspended_keys: Set[int] = set()
        self.total_quota_units = 0
        self.quota_units_per_key = {}

        # Cache (persistente entre coletas)
        self.channel_id_cache: Dict[str, str] = {}
```

**Fluxo de Requisição:**
```python
async def make_api_request(url, params, canal_name):
    # 1. Verifica se tem keys disponíveis
    if self.all_keys_exhausted():
        return None

    # 2. Pega key atual (pula exhausted/suspended)
    current_key = self.get_current_api_key()

    # 3. Rate limiter aguarda se necessário
    await self.rate_limiters[key_index].wait_if_needed()

    # 4. Faz requisição
    response = await session.get(url, params=params)

    # 5. Registra requisição
    self.rate_limiters[key_index].record_request()

    # 6. Incrementa quota counter
    cost = self.get_request_cost(url)  # search=100, outros=1
    self.increment_quota_counter(canal_name, cost)

    # 7. Trata erros
    if response.status == 403:
        if 'quota' in error:
            self.mark_key_as_exhausted()
            return await self.make_api_request(...)  # Retry com próxima key
        elif 'ratelimit' in error:
            await asyncio.sleep(exponential_backoff)
            return await self.make_api_request(...)  # Retry
        else:
            self.mark_key_as_suspended()
            return await self.make_api_request(...)  # Retry

    return data
```

**Rotação de Keys:**
```python
def rotate_to_next_key(self):
    # Circular rotation (0 → 1 → 2 → ... → 19 → 0)
    self.current_key_index = (self.current_key_index + 1) % 20

    # Pula exhausted + suspended
    while self.current_key_index in (exhausted | suspended):
        self.current_key_index = (self.current_key_index + 1) % 20
```

**Ver:** `06_YOUTUBE_COLLECTOR.md` para detalhes

### 3. Database Client (database.py)

**Classe Principal:**
```python
class SupabaseClient:
    def __init__(self):
        # Client principal (anon key)
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Client service_role (OAuth protegido)
        if SUPABASE_SERVICE_ROLE_KEY:
            self.supabase_service = create_client(URL, SERVICE_KEY)
```

**Métodos Principais:**
- `get_canais_for_collection()`: Busca canais ativos
- `save_canal_data()`: Salva histórico de canal
- `save_videos_data()`: Salva histórico de vídeos
- `get_canais_with_filters()`: Lista canais com filtros avançados
- `get_notificacoes_all()`: Lista notificações
- `marcar_todas_notificacoes_vistas()`: Marca como vistas
- `get_subniche_trends_snapshot()`: Tendências por subnicho

**Ver:** `05_DATABASE_SCHEMA.md` para todas as tabelas

### 4. Sistema de Upload (yt_uploader/)

**Componentes:**

```
yt_uploader/
├── uploader.py          # YouTubeUploader class
├── oauth_manager.py     # OAuthManager (credentials)
├── database.py          # get_channel(), get_queue()
├── sheets.py            # Google Sheets integration
├── queue_worker.py      # Worker assíncrono
└── spreadsheet_scanner.py  # Lê planilhas
```

**Fluxo:**
1. Frontend → enqueue job
2. spreadsheet_scanner → Lê planilha
3. queue_worker → Processa (max 3 simultâneos)
4. uploader.download_video() → gdown
5. uploader.upload_to_youtube() → OAuth + API
6. sheets.update_status() → Atualiza planilha

**Ver:** `11_YOUTUBE_UPLOADER.md`

---

## Integrações Externas

### 1. YouTube Data API v3

**Uso:** Coleta de dados de canais/vídeos

**Endpoints Usados:**
- `GET /youtube/v3/channels` - Info de canal (1 unit)
- `GET /youtube/v3/search` - Busca de vídeos (100 units!)
- `GET /youtube/v3/videos` - Detalhes de vídeos (1 unit)
- `POST /youtube/v3/videos` - Upload de vídeo (1600 units)
- `POST /youtube/v3/playlistItems` - Adicionar à playlist (50 units)

**Autenticação:**
- API Keys (20 keys rotacionadas)
- Quota: 10,000 units/dia por key
- **Total disponível:** 200,000 units/dia

**Configuração (Railway):**
```bash
YOUTUBE_API_KEY_3=AIzaSy...
YOUTUBE_API_KEY_4=AIzaSy...
# ... (20 keys)
YOUTUBE_API_KEY_32=AIzaSy...
```

### 2. YouTube Analytics API v2

**Uso:** Coleta de métricas de monetização

**Endpoints Usados:**
- `GET /v2/reports?metrics=estimatedRevenue,...` - Métricas diárias
- `GET /v2/reports?dimensions=country` - Métricas por país
- `GET /v2/reports?dimensions=video` - Métricas por vídeo
- `GET /v2/reports?dimensions=insightTrafficSourceType` - Fontes de tráfego
- `GET /v2/reports?dimensions=ageGroup,gender` - Demographics

**Autenticação:**
- OAuth 2.0 (por canal)
- Tokens armazenados em `yt_oauth_tokens` (RLS)
- Refresh automático via `monetization_oauth_collector.py`

**Dados Coletados:**
- Revenue (USD)
- Views, watch time
- Engagement (likes, comments, shares)
- Inscritos ganhos/perdidos
- Retenção (avg duration, %)
- RPM, CTR

### 3. Google Sheets API v4

**Uso:** Gerenciamento de upload queue

**Autenticação:**
- Service Account (`service_account.json`)
- Scopes: `spreadsheets`, `drive`

**Operações:**
- Ler planilha (status, video_url, titulo, descricao)
- Atualizar status (enqueued → processing → uploaded)
- Escrever video_id após upload

**Formato Esperado:**
```
| status | video_url | titulo | descricao | lingua | video_id | upload_date |
|--------|-----------|--------|-----------|--------|----------|-------------|
| ready  | https://... | ...   | ...       | pt     |          |             |
```

### 4. Google Drive API v3

**Uso:** Download de vídeos para upload

**Biblioteca:** `gdown` (wrapper não-oficial)
- Bypass automático de virus scan warning
- Progress tracking
- Resumable downloads

**Formato URL:**
```
https://drive.google.com/file/d/{FILE_ID}/view
https://drive.google.com/uc?id={FILE_ID}
```

**Requisitos:**
- Link de compartilhamento público
- "Anyone with the link" permission

### 5. Supabase REST API

**Uso:** Banco de dados PostgreSQL

**Endpoints (PostgREST):**
- `GET /rest/v1/table` - SELECT
- `POST /rest/v1/table` - INSERT
- `PATCH /rest/v1/table` - UPDATE
- `DELETE /rest/v1/table` - DELETE

**Autenticação:**
```python
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}
```

**Row Level Security (RLS):**
- Tabelas OAuth protegidas: `yt_oauth_tokens`, `yt_proxy_credentials`, `yt_channel_credentials`
- Requer `SUPABASE_SERVICE_ROLE_KEY` para acesso

### 6. AwesomeAPI (Taxa de Câmbio)

**Uso:** Conversão USD → BRL (sistema financeiro)

**Endpoint:**
```
GET https://economia.awesomeapi.com.br/last/USD-BRL
```

**Response:**
```json
{
  "USDBRL": {
    "bid": "5.52",
    "ask": "5.53",
    "create_date": "2025-01-12 15:35:03"
  }
}
```

**Fallback:** 5.50 (hardcoded)

---

## Segurança e Autenticação

### 1. Environment Variables

**Configuração (Railway):**

```bash
# Database
SUPABASE_URL=https://prvkmzstyedepvlbppyo.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # anon key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # service key

# YouTube Data API (20 keys)
YOUTUBE_API_KEY_3=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_4=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ... (16 mais)
YOUTUBE_API_KEY_32=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Service Account (JSON serializado)
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}

# Servidor de Transcrição (M5)
TRANSCRIPTION_SERVER_URL=https://transcription.2growai.com.br

# Logs
LOG_DIR=./logs
TEMP_VIDEO_PATH=/tmp/videos
```

**Segurança:**
- Nunca comitar `.env` (gitignore)
- Usar variáveis de ambiente no Railway
- Service role key apenas para tabelas RLS

### 2. OAuth 2.0 Flow (Monetização)

**Arquitetura:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    OAUTH FLOW (3-LEGGED)                        │
└─────────────────────────────────────────────────────────────────┘

1. AUTORIZAÇÃO INICIAL:

   [Backend Script] → gerar_url_oauth.py
   - client_id (do proxy)
   - redirect_uri
   - scopes: yt-analytics.readonly
   ↓
   [Browser] → Google OAuth consent screen
   ↓
   [User] → Aceita permissões
   ↓
   [Google] → Redirect com ?code=xyz
   ↓
   [Backend Script] → processar_oauth_callback.py
   - Troca code por access_token + refresh_token
   - Salva em yt_oauth_tokens (RLS)

2. REFRESH AUTOMÁTICO (diário):

   [Scheduler] → monetization_oauth_collector.py
   ↓
   - Lê refresh_token (yt_oauth_tokens)
   - POST oauth2.googleapis.com/token
     {grant_type: "refresh_token"}
   ↓
   - Recebe novo access_token
   - Atualiza yt_oauth_tokens
   ↓
   - Usa access_token para YouTube Analytics API
```

**Tabelas Protegidas (RLS):**

```sql
-- yt_oauth_tokens
CREATE TABLE yt_oauth_tokens (
    channel_id TEXT PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- RLS Policy (apenas service_role)
ALTER TABLE yt_oauth_tokens ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role only" ON yt_oauth_tokens
    FOR ALL USING (auth.role() = 'service_role');

-- yt_proxy_credentials (client_id/secret)
-- yt_channel_credentials (credenciais isoladas)
```

**Ver:** `09_MONETIZACAO_SISTEMA.md`

### 3. CORS (Cross-Origin)

**Configuração (main.py):**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Lovable frontend (qualquer subdomínio)
        "http://localhost:5173",  # Dev local
    ],
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PATCH, DELETE
    allow_headers=["*"],  # Content-Type, Authorization
)
```

### 4. API Rate Limiting

**YouTube API:**
- Rate limiter: 90 req/100s por key
- Quota: 10,000 units/dia por key
- Auto-rotation quando exhausted

**Backend API:**
- Sem rate limit (trusted frontend)
- Railway tem DDoS protection automático

### 5. Data Validation

**Pydantic Models:**

```python
from pydantic import BaseModel, Field

class CanalCreate(BaseModel):
    nome_canal: str = Field(..., min_length=1, max_length=200)
    url_canal: HttpUrl
    subnicho: str = Field(..., min_length=1)
    lingua: str = Field(default="English")
    tipo: str = Field(default="minerado")
    status: str = Field(default="ativo")
```

**Validação:**
- Tipos corretos
- Constraints (min/max length)
- URL validation
- Enum validation

---

## Escalabilidade

### 1. Capacidade Atual (2025-01)

**Métricas:**
- **Canais:** 263 ativos (209 minerados + 54 nossos)
- **Vídeos:** ~8,500 novos/dia (30 dias tracking)
- **Coletas:** 4x/dia (6h, 12h, 18h, 0h)
- **Quota YouTube:** 200k units/dia (20 keys)
- **Uploads:** Max 3 simultâneos

**Performance:**
- Coleta completa: 60-80 minutos (263 canais)
- Notificações: ~5-10 segundos (verificação completa)
- Monetização: ~15-20 minutos (16 canais)
- Upload: ~10-15 min/vídeo (dependendo tamanho)

### 2. Gargalos Conhecidos

**1. YouTube API Quota:**
- **Limite:** 10k units/key/dia
- **Uso médio:** 2-2.5k units/coleta (263 canais)
- **Margem:** 4x de sobra
- **Solução:** Adicionar mais keys se necessário

**2. Coleta Duration:**
- **Tempo:** 60-80 min para 263 canais
- **Causa:** Rate limiter (90 req/100s)
- **Solução:**
  - Aumentar rate limit para 95 req/100s
  - Processar canais em paralelo (asyncio)

**3. Upload Semaphore:**
- **Limite:** 3 uploads simultâneos
- **Causa:** YouTube API quota (1600 units/upload)
- **Solução:**
  - Aumentar para 5 simultâneos
  - Usar keys dedicadas para upload

**4. Database Connections:**
- **Supabase:** Connection pooling automático
- **Max connections:** 25 (plano gratuito)
- **Uso médio:** 5-10 conexões
- **Solução:** Upgrade para plano Pro (100 connections)

### 3. Plano de Escalabilidade

**Fase 1: 500 Canais (Q1 2025)**
- Adicionar 10 API keys (total: 30 keys)
- Quota: 300k units/dia
- Coleta paralela (10 workers)
- Tempo estimado: 40-50 min/coleta

**Fase 2: 1000 Canais (Q2 2025)**
- Adicionar 20 API keys (total: 50 keys)
- Quota: 500k units/dia
- Supabase Pro (100 connections)
- Tempo estimado: 60-70 min/coleta

**Fase 3: 2000+ Canais (Q3 2025)**
- Migrar para Google Cloud (quotas maiores)
- Database read replicas
- Caching layer (Redis)
- Horizontal scaling (múltiplos workers)

### 4. Monitoring e Observabilidade

**Logs (Railway):**
```bash
# Ver logs em tempo real
railway logs

# Filtrar por nível
railway logs --filter "ERROR"

# Últimas 100 linhas
railway logs --tail 100
```

**Métricas Importantes:**
- Quota units usados/dia
- Tempo de coleta
- Taxa de erro por canal
- Notificações criadas/dia
- Uploads completados/dia

**Alertas (futuro):**
- Quota > 80% usado
- Coleta > 2h de duração
- Taxa de erro > 10%
- Disk space > 80%

---

## Diagrama de Deployment

```
┌────────────────────────────────────────────────────────────────────┐
│                            PRODUCTION                              │
└────────────────────────────────────────────────────────────────────┘

GitHub (main branch)
    │
    │ Push
    ▼
Railway (Backend)
    ├─ Auto-deploy on push
    ├─ Build: pip install -r requirements.txt
    ├─ Start: uvicorn main:app --host 0.0.0.0 --port $PORT
    ├─ Health check: GET /health
    └─ Logs: railway logs
    │
    │ HTTPS
    ▼
Lovable (Frontend)
    ├─ Auto-deploy on Git sync
    ├─ CDN global
    ├─ HTTPS certificate
    └─ Environment: production
    │
    │ API calls
    ▼
Supabase (Database)
    ├─ PostgreSQL 15+
    ├─ Backup: diário
    ├─ RLS enabled
    └─ Connection pooling

External APIs:
    ├─ YouTube Data API v3 (20 keys)
    ├─ YouTube Analytics API v2 (OAuth)
    ├─ Google Sheets API (service account)
    ├─ Google Drive API (gdown)
    └─ AwesomeAPI (câmbio)
```

---

## Próximos Passos

### Melhorias Planejadas

1. **Caching Layer:**
   - Redis para cache de queries frequentes
   - Invalidação automática após coleta

2. **Real-time Updates:**
   - WebSocket para notificações
   - Server-Sent Events para progress

3. **Advanced Analytics:**
   - ML para predição de performance
   - Clustering de canais similares
   - Keyword extraction automático

4. **Multi-tenancy:**
   - Suporte para múltiplos usuários
   - Permissões granulares
   - Workspace isolation

### Refactoring Futuro

1. **Modularização:**
   - Separar main.py em routers
   - Extrair business logic para services
   - Criar domain models

2. **Testing:**
   - Unit tests (pytest)
   - Integration tests
   - E2E tests (Playwright)

3. **CI/CD:**
   - GitHub Actions
   - Automated tests
   - Linting (ruff, mypy)

---

## Referências

- **FastAPI:** https://fastapi.tiangolo.com/
- **Supabase:** https://supabase.com/docs
- **YouTube APIs:** https://developers.google.com/youtube
- **Railway:** https://docs.railway.app/
- **Lovable:** https://lovable.dev/docs

**Documentos Relacionados:**
- `05_DATABASE_SCHEMA.md` - Todas as tabelas
- `06_YOUTUBE_COLLECTOR.md` - Detalhes do coletor
- `08_API_ENDPOINTS_COMPLETA.md` - Referência de API
- `13_DEPLOY_RAILWAY.md` - Deploy e configuração
