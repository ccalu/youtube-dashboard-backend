# 09 - Sistema de Monetização

**Sistema completo de coleta de revenue via YouTube Analytics API (OAuth 2.0)**

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura OAuth](#arquitetura-oauth)
3. [Coleta de Revenue](#coleta-de-revenue)
4. [Métricas Coletadas](#métricas-coletadas)
5. [Fluxo de Autorização](#fluxo-de-autorização)
6. [Troubleshooting OAuth](#troubleshooting-oauth)
7. [Conversão USD → BRL](#conversão-usd-brl)

---

## Visão Geral

**Objetivo:** Coletar dados reais de revenue dos 16 canais monetizados via YouTube Analytics API v3

**Arquivos principais:**
- `D:\ContentFactory\youtube-dashboard-backend\monetization_oauth_collector.py` (860 linhas)
- `D:\ContentFactory\youtube-dashboard-backend\monetization_collector.py` (311 linhas)

**Canais monetizados:** 16 canais
**Execução:** Automática às 5 AM UTC (APScheduler)
**Delay do YouTube:** Revenue tem delay de 2-3 dias

---

## Arquitetura OAuth

### 1. Tabelas Supabase

**yt_channels:**
```sql
CREATE TABLE yt_channels (
  channel_id TEXT PRIMARY KEY,
  channel_name TEXT,
  is_monetized BOOLEAN DEFAULT FALSE,
  monetization_start_date DATE,
  proxy_name TEXT,  -- DEPRECATED
  lingua TEXT,
  default_playlist_id TEXT,
  is_active BOOLEAN DEFAULT TRUE
);
```

**yt_oauth_tokens:**
```sql
CREATE TABLE yt_oauth_tokens (
  channel_id TEXT PRIMARY KEY REFERENCES yt_channels(channel_id),
  access_token TEXT NOT NULL,
  refresh_token TEXT NOT NULL,
  token_expiry TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**yt_channel_credentials:** (NOVA ARQUITETURA)
```sql
CREATE TABLE yt_channel_credentials (
  channel_id TEXT PRIMARY KEY REFERENCES yt_channels(channel_id),
  client_id TEXT NOT NULL,
  client_secret TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**yt_proxy_credentials:** (DEPRECATED - compatibilidade)
```sql
CREATE TABLE yt_proxy_credentials (
  proxy_name TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  client_secret TEXT NOT NULL
);
```

---

### 2. Nova Arquitetura: 1 Canal = 1 Client ID

**Antes (v1.0 - DEPRECATED):**
```
Proxy C0008 → 3 canais (compartilham Client ID/Secret)
├── Canal A
├── Canal B
└── Canal C
```

**Problema:** Risco de ban em massa (1 canal suspende → 3 canais afetados)

**Agora (v2.0 - ISOLADO):**
```
Canal A → Client ID 1 (isolado)
Canal B → Client ID 2 (isolado)
Canal C → Client ID 3 (isolado)
```

**Benefícios:**
- Isolamento total entre canais
- Ban de 1 canal não afeta outros
- Contingência máxima
- Rastreabilidade perfeita

---

### 3. Estrutura de Credenciais

**Localização:** `yt_channel_credentials` (Supabase)

**Exemplo:**
```json
{
  "channel_id": "UCxxxxxx",
  "client_id": "123456789-abc.apps.googleusercontent.com",
  "client_secret": "GOCSPX-xxxxxxxxxxxxxxxx"
}
```

**Como obter Client ID/Secret:**
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie novo projeto (1 projeto = 1 canal)
3. Ative YouTube Analytics API v3
4. Crie credenciais OAuth 2.0 Client ID
5. Tipo: Web Application
6. Redirect URIs: `http://localhost:8000/oauth/callback`
7. Salve Client ID e Secret no Supabase

---

## Coleta de Revenue

### 1. Fluxo Completo

```
[5 AM UTC] Scheduler dispara
    ↓
[monetization_oauth_collector.py] Busca canais monetizados
    ↓
Para cada canal:
  1. Busca credenciais (yt_channel_credentials ou proxy)
  2. Busca tokens OAuth (yt_oauth_tokens)
  3. Renova access_token (se expirado)
  4. Coleta métricas via YouTube Analytics API
  5. Salva em yt_daily_metrics, yt_country_metrics, etc.
    ↓
[monetization_collector.py] Calcula views_24h
    ↓
Gera estimativas (para dias sem revenue ainda)
    ↓
FIM
```

---

### 2. Collector OAuth (Arquivo Principal)

**Arquivo:** `monetization_oauth_collector.py`

**Função principal:**
```python
async def collect_oauth_metrics():
    """
    Coleta métricas OAuth dos canais monetizados
    Chamado automaticamente pelo scheduler às 5 AM
    """
    # Datas - Ajustado para delay do YouTube (2-3 dias)
    end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    # Buscar canais monetizados
    channels = get_channels()

    for channel in channels:
        # 1. Buscar credenciais
        credentials = get_channel_credentials(channel_id) or get_proxy_credentials(proxy_name)

        # 2. Buscar tokens
        tokens = get_tokens(channel_id)

        # 3. Renovar access_token
        access_token = refresh_access_token(
            tokens["refresh_token"],
            credentials["client_id"],
            credentials["client_secret"]
        )

        # 4. Coletar métricas
        daily_rows = collect_daily_metrics(channel_id, access_token, start_date, end_date)
        save_daily_metrics(channel_id, daily_rows)

        country_rows = collect_country_metrics(channel_id, access_token, yesterday, yesterday)
        save_country_metrics(channel_id, country_rows, yesterday)

        # ... outras métricas
```

---

### 3. Renovação de Tokens

**Lógica:**
```python
def refresh_access_token(refresh_token, client_id, client_secret):
    """Renova o access_token usando o refresh_token"""
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    })

    if resp.status_code == 200:
        return resp.json().get("access_token")

    # Erro: token inválido ou revogado
    return None
```

**Expiração:** Tokens expiram em ~1 hora
**Renovação automática:** Feita a cada coleta

---

### 4. Salvando Revenue

**Tabela:** `yt_daily_metrics`

**Estrutura:**
```sql
CREATE TABLE yt_daily_metrics (
  id SERIAL PRIMARY KEY,
  channel_id TEXT NOT NULL REFERENCES yt_channels(channel_id),
  date DATE NOT NULL,
  revenue DECIMAL(10,2),           -- USD
  views INTEGER,
  likes INTEGER,
  comments INTEGER,
  shares INTEGER,
  subscribers_gained INTEGER,
  subscribers_lost INTEGER,
  watch_time_minutes INTEGER,
  rpm DECIMAL(10,2),               -- Revenue / (views / 1000)
  avg_view_duration_sec DECIMAL(10,2),
  avg_retention_pct DECIMAL(5,2),
  is_estimate BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(channel_id, date)
);
```

**Lógica de salvamento:**
```python
def save_daily_metrics(channel_id, rows):
    """
    Salva métricas diárias - APENAS se revenue > 0 ou views > 0
    Delay do YouTube: 2-3 dias para revenue aparecer
    """
    for row in rows:
        date = row[0]
        revenue = float(row[1])
        views = int(row[2])

        # Se revenue = 0 e views = 0, ignorar (sem dados)
        if revenue == 0 and views == 0:
            continue

        # Se já existe revenue real > 0, não sobrescrever com 0
        existing = check_existing_revenue(channel_id, date)
        if existing and existing > 0 and revenue == 0:
            continue  # Manter revenue existente

        # Calcular RPM
        rpm = (revenue / views * 1000) if views > 0 else 0

        data = {
            "channel_id": channel_id,
            "date": date,
            "revenue": revenue,
            "views": views,
            "rpm": rpm,
            "is_estimate": False  # Dados reais do YouTube Analytics
        }

        # Upsert (insert ou update)
        upsert_daily_metrics(data)
```

**IMPORTANTE:**
- Revenue em USD (convertido para BRL no frontend/financeiro)
- `is_estimate=false` → dados reais do YouTube
- `is_estimate=true` → estimativas baseadas em RPM médio

---

## Métricas Coletadas

### 1. Daily Metrics (Diárias)

**API Endpoint:** `https://youtubeanalytics.googleapis.com/v2/reports`

**Request:**
```python
params = {
    "ids": f"channel=={channel_id}",
    "startDate": "2024-01-01",
    "endDate": "2024-01-10",
    "metrics": "estimatedRevenue,views,likes,comments,shares,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
    "dimensions": "day",
    "sort": "day"
}
```

**Response:**
```json
{
  "rows": [
    ["2024-01-01", 12.45, 5432, 234, 45, 12, 15, 2, 2340, 258.3, 45.2],
    ["2024-01-02", 15.67, 6234, 312, 67, 23, 18, 3, 3120, 301.2, 48.5]
  ]
}
```

**Campos:**
1. `date` - Data (YYYY-MM-DD)
2. `estimatedRevenue` - Revenue em USD
3. `views` - Views totais
4. `likes` - Likes
5. `comments` - Comentários
6. `shares` - Compartilhamentos
7. `subscribersGained` - Inscritos ganhos
8. `subscribersLost` - Inscritos perdidos
9. `estimatedMinutesWatched` - Watch time (minutos)
10. `averageViewDuration` - Duração média (segundos)
11. `averageViewPercentage` - Retenção média (%)

---

### 2. Country Metrics (Por País)

**Tabela:** `yt_country_metrics`

**Request:**
```python
params = {
    "metrics": "views,estimatedRevenue,estimatedMinutesWatched",
    "dimensions": "country",
    "sort": "-views",
    "maxResults": "25"
}
```

**Response:**
```json
{
  "rows": [
    ["US", 15000, 45.23, 7500],
    ["BR", 8500, 12.34, 4200],
    ["MX", 5200, 8.90, 2600]
  ]
}
```

**Uso:** Identificar países de maior revenue

---

### 3. Video Metrics (Por Vídeo)

**Tabela:** `yt_video_metrics`

**Request:**
```python
params = {
    "metrics": "estimatedRevenue,views,likes,comments,subscribersGained,averageViewDuration,averageViewPercentage",
    "dimensions": "video",
    "sort": "-views",
    "maxResults": "50"
}
```

**Uso:** Identificar vídeos mais lucrativos

---

### 4. Traffic Sources (Fontes de Tráfego)

**Tabela:** `yt_traffic_summary`

**Request:**
```python
params = {
    "metrics": "views,estimatedMinutesWatched",
    "dimensions": "insightTrafficSourceType",
    "sort": "-views"
}
```

**Response:**
```json
{
  "rows": [
    ["YT_SEARCH", 12000, 6000],
    ["YT_RELATED", 8500, 4250],
    ["NOTIFICATION", 3200, 1600],
    ["EXTERNAL", 1500, 750]
  ]
}
```

**Tipos comuns:**
- `YT_SEARCH` - Busca do YouTube
- `YT_RELATED` - Vídeos sugeridos
- `NOTIFICATION` - Notificações
- `EXTERNAL` - Sites externos
- `YT_CHANNEL` - Página do canal

---

### 5. Search Terms (Termos de Busca)

**Tabela:** `yt_search_analytics`

**Request:**
```python
params = {
    "metrics": "views",
    "dimensions": "insightTrafficSourceDetail",
    "filters": "insightTrafficSourceType==YT_SEARCH",
    "maxResults": "10",
    "sort": "-views"
}
```

**Uso:** Identificar palavras-chave que geram tráfego

---

### 6. Demographics (Idade e Gênero)

**Tabela:** `yt_demographics`

**Request:**
```python
params = {
    "metrics": "viewerPercentage",
    "dimensions": "ageGroup,gender",
    "sort": "-viewerPercentage"
}
```

**Response:**
```json
{
  "rows": [
    ["age25-34", "male", 32.5],
    ["age18-24", "male", 28.3],
    ["age25-34", "female", 15.2]
  ]
}
```

---

### 7. Device Metrics (Dispositivos)

**Tabela:** `yt_device_metrics`

**Request:**
```python
params = {
    "metrics": "views,estimatedMinutesWatched",
    "dimensions": "deviceType",
    "sort": "-views"
}
```

**Response:**
```json
{
  "rows": [
    ["MOBILE", 18000, 9000],
    ["DESKTOP", 7500, 3750],
    ["TABLET", 2500, 1250],
    ["TV", 1000, 500]
  ]
}
```

---

## Fluxo de Autorização

### 1. Setup Inicial (1x por canal)

**Passo 1: Criar projeto Google Cloud**

1. Acesse: https://console.cloud.google.com
2. Crie novo projeto: `canal-batalhas-historia`
3. Ative APIs:
   - YouTube Analytics API v3
   - YouTube Data API v3 (apenas para upload)

**Passo 2: Criar OAuth 2.0 Credentials**

1. APIs & Services → Credentials → Create Credentials
2. OAuth client ID → Web application
3. Name: `Canal Batalhas História - OAuth`
4. Authorized redirect URIs:
   ```
   http://localhost:8000/oauth/callback
   https://youtube-dashboard-backend-production.up.railway.app/oauth/callback
   ```
5. Salvar Client ID e Client Secret

**Passo 3: Salvar credenciais no Supabase**

```python
from yt_uploader.database import save_channel_credentials

save_channel_credentials(
    channel_id="UCxxxxxx",
    client_id="123456789-abc.apps.googleusercontent.com",
    client_secret="GOCSPX-xxxxxxxxxxxxxxxx"
)
```

---

### 2. Autorizar Canal (1x por canal)

**Script:** `autorizar_canal.py`

```python
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.upload"  # Se for fazer upload
]

def authorize_channel(channel_id):
    """Gera URL de autorização e salva tokens"""

    # 1. Buscar credenciais do canal
    credentials = get_channel_credentials(channel_id)

    # 2. Criar flow OAuth
    flow = InstalledAppFlow.from_client_config(
        {
            "web": {
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8000/oauth/callback"]
            }
        },
        scopes=SCOPES
    )

    # 3. Gerar URL de autorização
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Força prompt para garantir refresh_token
    )

    print(f"🔗 Abra esta URL no navegador:\n{auth_url}")

    # 4. Usuário autoriza → recebe código
    code = input("Cole o código de autorização aqui: ")

    # 5. Trocar código por tokens
    flow.fetch_token(code=code)

    credentials = flow.credentials

    # 6. Salvar tokens no Supabase
    save_oauth_tokens(
        channel_id=channel_id,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        token_expiry=credentials.expiry.isoformat()
    )

    print("✅ Autorização concluída!")
```

**Uso:**
```bash
python autorizar_canal.py UCxxxxxx
```

---

### 3. Reautorização (Se token expirar/revogar)

**Sintomas:**
- Erro 401 Unauthorized
- Erro 400 Invalid Grant
- `refresh_token` inválido

**Solução:**
```bash
# Rodar script de reautorização
python reautorizar_canal.py UCxxxxxx
```

**IMPORTANTE:** Use `prompt='consent'` para garantir novo `refresh_token`

---

## Troubleshooting OAuth

### 1. Erro: Invalid Grant

**Causa:** Refresh token revogado ou expirado

**Solução:**
```bash
# Reautorizar canal
python reautorizar_canal.py UCxxxxxx
```

**Prevenção:**
- Não revogar acesso manualmente em https://myaccount.google.com/permissions
- Não deletar projeto Google Cloud
- Manter `prompt='consent'` na autorização

---

### 2. Erro: Quota Exceeded

**Causa:** Muitas requisições à YouTube Analytics API

**Limites:**
- YouTube Analytics API: **50,000 queries/dia** por projeto
- Cada query de report = 1 unit

**Solução:**
```python
# Reduzir frequência de coleta
# OU
# Criar múltiplos projetos Google Cloud (1 por canal)
```

---

### 3. Erro: Access Not Configured

**Causa:** YouTube Analytics API não ativada no projeto

**Solução:**
1. Google Cloud Console → APIs & Services
2. Library → YouTube Analytics API
3. Enable

---

### 4. Erro: Redirect URI Mismatch

**Causa:** Redirect URI não configurado

**Solução:**
1. Google Cloud Console → Credentials
2. Editar OAuth 2.0 Client ID
3. Adicionar redirect URI exato:
   ```
   http://localhost:8000/oauth/callback
   ```

---

### 5. Token Expira Muito Rápido

**Causa:** Access token expira em ~1 hora (normal)

**Solução:**
- Sistema renova automaticamente usando `refresh_token`
- `refresh_token` não expira (até ser revogado)
- Verificar se salvou `refresh_token` corretamente

---

### 6. Nenhuma Métrica Retornada

**Causa:** Canal não monetizado OU dados ainda não disponíveis

**Verificações:**
```python
# 1. Canal está no Partner Program?
# Verificar em: YouTube Studio → Monetização

# 2. Revenue tem delay de 2-3 dias
# Pedir dados de 3 dias atrás:
end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

# 3. Canal tem views no período?
# YouTube não retorna dados se views = 0
```

---

## Conversão USD → BRL

### 1. Taxa de Câmbio

**API:** AwesomeAPI (Brasil)

**Endpoint:** `https://economia.awesomeapi.com.br/last/USD-BRL`

**Response:**
```json
{
  "USDBRL": {
    "code": "USD",
    "codein": "BRL",
    "name": "Dólar Americano/Real Brasileiro",
    "high": "5.5432",
    "low": "5.4987",
    "varBid": "0.0123",
    "pctChange": "0.22",
    "bid": "5.5234",   // ← Usar este (taxa de compra)
    "ask": "5.5298",
    "timestamp": "1704902103",
    "create_date": "2024-01-10 15:35:03"
  }
}
```

---

### 2. Função de Conversão

**Arquivo:** `financeiro.py`

```python
async def get_usd_brl_rate() -> Dict:
    """
    Retorna taxa de câmbio USD-BRL atualizada da AwesomeAPI

    Returns:
        Dict com:
        - taxa: float (ex: 5.52)
        - atualizado_em: str (ex: "2024-01-10 15:35:03")
    """
    url = "https://economia.awesomeapi.com.br/last/USD-BRL"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                usdbrl = data.get("USDBRL", {})

                # Usa o valor "bid" (compra) como padrão
                taxa = float(usdbrl.get("bid", 5.50))
                atualizado_em = usdbrl.get("create_date", "")

                return {
                    "taxa": round(taxa, 2),
                    "atualizado_em": atualizado_em
                }

    # Fallback: taxa padrão
    return {"taxa": 5.50, "atualizado_em": "fallback"}
```

---

### 3. Conversão no Sistema Financeiro

**Lógica:**
```python
async def get_youtube_revenue(periodo: str = "30d") -> float:
    """Consulta receita YouTube do período em BRL"""

    # 1. Buscar taxa de câmbio atual
    taxa_cambio = await get_usd_brl_rate()
    taxa = taxa_cambio['taxa']

    # 2. Buscar revenue em USD (apenas dados reais)
    response = db.supabase.table("yt_daily_metrics")\
        .select("revenue")\
        .eq("is_estimate", False)\
        .gte("date", data_inicio)\
        .lte("date", data_fim)\
        .execute()

    # 3. Somar USD
    total_usd = sum(float(item['revenue'] or 0) for item in response.data)

    # 4. Converter para BRL
    total_brl = total_usd * taxa

    return round(total_brl, 2)
```

**Exemplo:**
```
Revenue YouTube (30 dias): $2,500.00 USD
Taxa de câmbio: R$ 5.52
Receita em BRL: R$ 13,800.00
```

---

## Estimativas (quando revenue ainda não chegou)

### 1. Lógica de Estimativa

**Problema:** YouTube tem delay de 2-3 dias para revenue

**Solução:** Estimar revenue baseado em RPM médio do canal

```python
def calculate_channel_rpm(channel_id: str) -> float:
    """
    Calcula RPM médio do canal baseado APENAS em dados reais
    Últimos 30 dias com revenue confirmado
    """
    # Buscar últimos 30 dias com revenue real
    response = db.supabase.table("yt_daily_metrics")\
        .select("revenue, views")\
        .eq("channel_id", channel_id)\
        .eq("is_estimate", False)\
        .gte("date", thirty_days_ago)\
        .execute()

    total_revenue = sum(r['revenue'] for r in response.data)
    total_views = sum(r['views'] for r in response.data)

    # RPM = (Revenue / Views) × 1000
    rpm = (total_revenue / total_views) * 1000

    return round(rpm, 2)
```

---

### 2. Criar Estimativa

```python
def save_views_to_yt_daily_metrics(channel_id, date, views_24h):
    """
    Salva estimativa para dias sem revenue ainda
    """
    # 1. Calcular RPM médio do canal (últimos 30 dias)
    rpm_avg = calculate_channel_rpm(channel_id)

    if rpm_avg is None or rpm_avg == 0:
        return False  # Sem dados históricos

    # 2. Estimar revenue
    revenue_estimated = rpm_avg * (views_24h / 1000)

    # 3. Salvar estimativa
    data = {
        'channel_id': channel_id,
        'date': date,
        'views': views_24h,
        'revenue': round(revenue_estimated, 2),
        'is_estimate': True,  # ← MARCA COMO ESTIMATIVA
        'rpm': rpm_avg
    }

    db.supabase.table("yt_daily_metrics").insert(data).execute()

    return True
```

**Exemplo:**
```
RPM médio (30 dias): $8.50
Views ontem: 5,000
Revenue estimado: $8.50 × (5000 / 1000) = $42.50
```

---

### 3. Substituir Estimativa por Dado Real

**Lógica:** Quando revenue real chegar, atualizar registro

```python
# Na coleta OAuth, verificar se já existe estimativa
existing = db.supabase.table("yt_daily_metrics")\
    .select("revenue, is_estimate")\
    .eq("channel_id", channel_id)\
    .eq("date", date)\
    .execute()

if existing.data:
    # Se é estimativa, pode sobrescrever
    if existing.data[0]['is_estimate']:
        # Atualizar com dado real
        db.supabase.table("yt_daily_metrics")\
            .update({
                "revenue": revenue_real,
                "is_estimate": False
            })\
            .eq("channel_id", channel_id)\
            .eq("date", date)\
            .execute()
```

---

## Checklist de Setup Monetização

### Canal Novo (Setup Completo)

- [ ] Canal monetizado no YouTube Partner Program
- [ ] Criar projeto Google Cloud (1 projeto por canal)
- [ ] Ativar YouTube Analytics API v3
- [ ] Criar OAuth 2.0 Client ID (Web Application)
- [ ] Configurar Redirect URI: `http://localhost:8000/oauth/callback`
- [ ] Salvar credenciais em `yt_channel_credentials` (Supabase)
- [ ] Marcar canal como monetizado em `yt_channels` (`is_monetized=true`)
- [ ] Rodar `autorizar_canal.py` → salva tokens em `yt_oauth_tokens`
- [ ] Aguardar próxima coleta automática (5 AM UTC)
- [ ] Verificar logs: `logs/coleta_oauth.log`
- [ ] Verificar dados em `yt_daily_metrics`

---

## Scripts Úteis

### 1. Testar Coleta Manual

```bash
python monetization_oauth_collector.py
```

---

### 2. Verificar Tokens de um Canal

```python
from yt_uploader.database import get_oauth_tokens

tokens = get_oauth_tokens("UCxxxxxx")
print(f"Access token: {tokens['access_token'][:20]}...")
print(f"Refresh token: {tokens['refresh_token'][:20]}...")
print(f"Expiry: {tokens['token_expiry']}")
```

---

### 3. Diagnosticar Erro OAuth

```python
import requests

def test_oauth_token(channel_id, access_token):
    """Testa se access_token está válido"""

    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": "2024-01-01",
            "endDate": "2024-01-10",
            "metrics": "views"
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if resp.status_code == 200:
        print("✅ Token válido!")
        print(f"Views: {resp.json()}")
    elif resp.status_code == 401:
        print("❌ Token inválido/expirado - rodar reautorização")
    else:
        print(f"❌ Erro: {resp.status_code} - {resp.text[:200]}")
```

---

**Referências:**
- YouTube Analytics API: https://developers.google.com/youtube/analytics
- OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Supabase Docs: https://supabase.com/docs

---

**Última atualização:** 2024-01-12
