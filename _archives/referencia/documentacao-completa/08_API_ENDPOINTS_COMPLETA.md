# 08 - API Endpoints Completa

**Referência técnica completa de todos os endpoints do Dashboard de Mineração YouTube**

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Canais](#canais-endpoints)
3. [Vídeos](#vídeos-endpoints)
4. [Notificações](#notificações-endpoints)
5. [Análises](#análises-endpoints)
6. [Coleta de Dados](#coleta-endpoints)
7. [Sistema Financeiro](#sistema-financeiro-endpoints)
8. [Upload YouTube](#upload-youtube-endpoints)
9. [Transcrições](#transcrições-endpoints)
10. [Modelos Pydantic](#modelos-pydantic)

---

## Visão Geral

**Arquivo principal:** `D:\ContentFactory\youtube-dashboard-backend\main.py` (1122 linhas)

**Base URL:**
- Local: `http://localhost:8000`
- Produção: `https://youtube-dashboard-backend-production.up.railway.app`

**Tecnologias:**
- FastAPI (async)
- Supabase (PostgreSQL)
- YouTube Data API v3 (20 keys)
- YouTube Analytics API v3 (OAuth)

**Autenticação:**
- Headers: `apikey` e `Authorization: Bearer {SUPABASE_KEY}`
- Endpoints públicos: `/health`, `/`

---

## Canais Endpoints

### 1. GET /api/canais

**Descrição:** Lista canais minerados com filtros avançados

**Query Parameters:**
```typescript
{
  tipo?: "minerado" | "nosso" | "favorito"  // Filtro por tipo
  subnicho?: string                          // Filtro por subnicho
  limit?: number                             // Máximo de resultados (padrão: 50)
  offset?: number                            // Paginação
  search?: string                            // Busca por nome
  sort?: "inscritos" | "videos" | "nome"    // Ordenação
}
```

**Response:**
```json
{
  "canais": [
    {
      "id": 123,
      "nome_canal": "Canal Exemplo",
      "channel_id": "UCxxxxxxx",
      "tipo": "minerado",
      "subnicho": "Guerras Mundiais",
      "inscritos": 150000,
      "videos_count": 234,
      "url_canal": "https://youtube.com/@exemplo",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

**Código:**
```python
@app.get("/api/canais")
async def get_canais(
    tipo: Optional[str] = None,
    subnicho: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None
):
    query = db.supabase.table("canais_monitorados").select("*")

    if tipo:
        query = query.eq("tipo", tipo)
    if subnicho:
        query = query.eq("subnicho", subnicho)
    if search:
        query = query.ilike("nome_canal", f"%{search}%")

    response = query.range(offset, offset + limit - 1).execute()
    return {"canais": response.data, "total": len(response.data)}
```

---

### 2. GET /api/canais-tabela

**Descrição:** Retorna nossos canais agrupados por subnicho (para aba Tabela)

**Features:**
- Ordenação inteligente: positivos → negativos → zero → null
- Cálculo de `inscritos_diff` (ganho D-1 → hoje)
- Mobile-first response

**Query Parameters:**
```typescript
{
  subnicho?: string  // Filtro opcional por subnicho
}
```

**Response:**
```json
{
  "subnichos": [
    {
      "subnicho": "Guerras Mundiais",
      "total_canais": 5,
      "total_inscritos": 750000,
      "canais": [
        {
          "id": 1,
          "nome_canal": "Batalhas da História",
          "inscritos": 150000,
          "inscritos_diff": 250,        // +250 inscritos ontem
          "ultima_coleta": "2024-01-10T08:00:00Z",
          "channel_id": "UCxxxxxx"
        }
      ]
    }
  ]
}
```

**Lógica de Ordenação:**
```python
# Categoria 0: Positivos (melhor no topo)
+250, +100, +50, +10, +2

# Categoria 1: Negativos (perdas)
-5, -10, -50

# Categoria 2: Zero (sem mudança)
0, 0, 0

# Categoria 3: Null (sem dados, sempre no final)
null, null
```

**Código:**
```python
@app.get("/api/canais-tabela")
async def get_canais_tabela(subnicho: Optional[str] = None):
    # Busca nossos canais
    query = db.supabase.table("canais_monitorados")\
        .select("*, dados_canais_historico(inscritos, data_coleta)")\
        .eq("tipo", "nosso")

    if subnicho:
        query = query.ilike("subnicho", f"%{subnicho}%")

    # Calcula inscritos_diff (ontem → hoje)
    # Ordena por categoria + valor
    # Agrupa por subnicho

    return {"subnichos": grouped_data}
```

**Documentação:** `INTEGRACAO_ABA_TABELA.md`

---

### 3. POST /api/add-canal

**Descrição:** Adiciona novo canal para mineração

**Request Body:**
```json
{
  "url_canal": "https://youtube.com/@exemplo",
  "tipo": "minerado",
  "subnicho": "Guerras Mundiais"
}
```

**Response:**
```json
{
  "success": true,
  "canal": {
    "id": 456,
    "nome_canal": "Canal Exemplo",
    "channel_id": "UCxxxxxxx",
    "inscritos": 150000
  }
}
```

**Validações:**
- URL válida do YouTube
- Canal não duplicado
- Channel ID extraído via YouTube Data API

---

### 4. PUT /api/canais/{canal_id}

**Descrição:** Atualiza configuração de um canal

**Request Body:**
```json
{
  "tipo": "favorito",
  "subnicho": "Guerras Mundiais",
  "notas": "Canal de referência"
}
```

---

### 5. DELETE /api/canais/{canal_id}

**Descrição:** Remove canal do monitoramento

**Response:**
```json
{
  "success": true,
  "message": "Canal removido com sucesso"
}
```

---

### 6. PATCH /api/canais/{channel_id}/monetizacao

**Descrição:** Atualiza status de monetização de um canal

**Request Body:**
```json
{
  "is_monetized": true,
  "monetization_start_date": "2024-01-01"
}
```

**Uso:** Após autorização OAuth completa

---

## Vídeos Endpoints

### 1. GET /api/videos

**Descrição:** Lista vídeos minerados com filtros

**Query Parameters:**
```typescript
{
  canal_id?: number              // Filtro por canal
  subnicho?: string              // Filtro por subnicho
  min_views?: number             // Views mínimas (ex: 10000)
  dias?: number                  // Últimos N dias (padrão: 7)
  limit?: number                 // Máximo de resultados (padrão: 50)
  offset?: number                // Paginação
  sort?: "views" | "data"        // Ordenação
}
```

**Response:**
```json
{
  "videos": [
    {
      "id": 789,
      "video_id": "dQw4w9WgXcQ",
      "titulo": "Batalha de Stalingrado",
      "canal_id": 123,
      "canal_nome": "Canal História",
      "views": 45000,
      "likes": 2300,
      "comments": 450,
      "published_at": "2024-01-01T10:00:00Z",
      "thumbnail": "https://i.ytimg.com/...",
      "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
      "transcricao": null
    }
  ],
  "total": 234
}
```

**Código:**
```python
@app.get("/api/videos")
async def get_videos(
    canal_id: Optional[int] = None,
    min_views: Optional[int] = None,
    dias: int = 7,
    limit: int = 50
):
    cutoff_date = datetime.now() - timedelta(days=dias)

    query = db.supabase.table("videos_monitorados")\
        .select("*, canais_monitorados(nome_canal)")\
        .gte("published_at", cutoff_date.isoformat())

    if canal_id:
        query = query.eq("canal_id", canal_id)
    if min_views:
        query = query.gte("views", min_views)

    response = query.order("views", desc=True).limit(limit).execute()
    return {"videos": response.data}
```

---

### 2. GET /api/videos/{video_id}

**Descrição:** Busca detalhes de um vídeo específico

**Response:**
```json
{
  "video": {
    "id": 789,
    "video_id": "dQw4w9WgXcQ",
    "titulo": "Batalha de Stalingrado",
    "descricao": "Descrição completa...",
    "views": 45000,
    "transcricao": "Texto completo da transcrição..."
  }
}
```

---

## Notificações Endpoints

### 1. GET /api/notificacoes

**Descrição:** Lista notificações não vistas

**Query Parameters:**
```typescript
{
  tipo_canal?: "minerado" | "nosso"  // Filtro por tipo
  subnicho?: string                  // Filtro por subnicho
  limit?: number                     // Máximo de resultados (padrão: 50)
}
```

**Response:**
```json
{
  "notificacoes": [
    {
      "id": 1,
      "tipo": "views_spike",
      "titulo": "Vídeo viral detectado",
      "mensagem": "Batalha de Stalingrado atingiu 10k views em 24h",
      "canal_id": 123,
      "video_id": 789,
      "vista": false,
      "created_at": "2024-01-10T08:00:00Z",
      "metadata": {
        "views_24h": 10500,
        "threshold": 10000
      }
    }
  ],
  "total": 15,
  "nao_vistas": 15
}
```

---

### 2. POST /api/force-notifier

**Descrição:** Força execução manual do sistema de notificações

**Response:**
```json
{
  "success": true,
  "notificacoes_criadas": 12,
  "execution_time": 2.34
}
```

**Uso:** Desenvolvimento e testes

---

### 3. PATCH /api/notificacoes/{notif_id}/marcar-vista

**Descrição:** Marca notificação como vista

**Response:**
```json
{
  "success": true,
  "notificacao": {
    "id": 1,
    "vista": true
  }
}
```

---

### 4. POST /api/notificacoes/marcar-todas-vistas

**Descrição:** Marca todas as notificações como vistas

**Request Body:**
```json
{
  "tipo_canal": "minerado",  // Opcional
  "subnicho": "Guerras"      // Opcional
}
```

**Response:**
```json
{
  "success": true,
  "marcadas": 23
}
```

---

### 5. GET /api/regras-notificacoes

**Descrição:** Lista regras de notificação configuradas

**Response:**
```json
{
  "regras": [
    {
      "id": 1,
      "nome_regra": "Vídeo viral 10k",
      "views_minimas": 10000,
      "periodo_dias": 1,
      "tipo_canal": "minerado",
      "subnichos": ["Guerras Mundiais", "Histórias Obscuras"],
      "ativo": true
    }
  ]
}
```

---

### 6. POST /api/regras-notificacoes

**Descrição:** Cria nova regra de notificação

**Request Body (Pydantic Model):**
```python
class RegraNotificacaoCreate(BaseModel):
    nome_regra: str
    views_minimas: int
    periodo_dias: int
    tipo_canal: str = "ambos"  # "minerado" | "nosso" | "ambos"
    subnichos: Optional[List[str]] = None
```

**Exemplo:**
```json
{
  "nome_regra": "Vídeo viral 50k",
  "views_minimas": 50000,
  "periodo_dias": 7,
  "tipo_canal": "minerado",
  "subnichos": ["Guerras Mundiais"]
}
```

---

## Análises Endpoints

### 1. GET /api/analysis/subniche-trends

**Descrição:** Análise de tendências por subnicho

**Query Parameters:**
```typescript
{
  periodo?: number  // Dias (padrão: 30)
}
```

**Response:**
```json
{
  "trends": [
    {
      "subnicho": "Guerras Mundiais",
      "total_videos": 45,
      "avg_views": 12500,
      "top_keywords": ["batalha", "segunda guerra", "hitler"],
      "growth_rate": 15.5,
      "total_canais": 8
    }
  ]
}
```

---

### 2. GET /api/system-stats

**Descrição:** Estatísticas gerais do sistema

**Response:**
```json
{
  "stats": {
    "total_canais": 150,
    "total_videos": 3450,
    "canais_ativos": 142,
    "ultima_coleta": "2024-01-10T05:00:00Z",
    "proxima_coleta": "2024-01-11T05:00:00Z",
    "quota_usage": {
      "units_today": 145230,
      "units_available": 200000,
      "keys_active": 20
    }
  }
}
```

---

### 3. GET /api/analysis/top-channels

**Descrição:** Top 10 canais por views/crescimento

**Query Parameters:**
```typescript
{
  periodo?: number        // Dias (padrão: 30)
  metric?: "views" | "growth"  // Métrica (padrão: views)
}
```

---

## Coleta Endpoints

### 1. POST /api/collect-data

**Descrição:** Inicia coleta manual de dados

**Response:**
```json
{
  "success": true,
  "message": "Coleta iniciada",
  "collection_id": "col_20240110_050000"
}
```

**Nota:** Coleta automática roda às 5 AM UTC via APScheduler

---

### 2. GET /api/coletas/historico

**Descrição:** Histórico de coletas executadas

**Query Parameters:**
```typescript
{
  limit?: number     // Máximo de resultados (padrão: 50)
  status?: string    // Filtro por status
}
```

**Response:**
```json
{
  "coletas": [
    {
      "id": 1,
      "started_at": "2024-01-10T05:00:00Z",
      "completed_at": "2024-01-10T05:15:34Z",
      "status": "completed",
      "canais_coletados": 150,
      "videos_coletados": 234,
      "quota_used": 145230,
      "errors": 2
    }
  ]
}
```

---

### 3. GET /api/stats

**Descrição:** Estatísticas do collector em tempo real

**Response:**
```json
{
  "total_keys": 20,
  "active_keys": 18,
  "exhausted_keys": 2,
  "quota_units_used": 145230,
  "quota_available": 54770,
  "requests_per_key": [
    {"key": 2, "units": 9842},
    {"key": 3, "units": 9654}
  ]
}
```

---

## Sistema Financeiro Endpoints

### 1. GET /api/financeiro/overview

**Descrição:** Overview financeiro completo

**Query Parameters:**
```typescript
{
  periodo?: string  // "7d" | "30d" | "90d" | "YYYY-MM-DD,YYYY-MM-DD"
}
```

**Response:**
```json
{
  "receita_bruta": 15432.50,
  "receita_variacao": 12.5,
  "despesas_totais": 4200.00,
  "despesas_fixas": 3500.00,
  "despesas_unicas": 700.00,
  "despesas_variacao": -5.2,
  "taxas_totais": 462.98,
  "lucro_liquido": 10769.52,
  "lucro_variacao": 18.7,
  "periodo": "30d"
}
```

---

### 2. GET /api/financeiro/youtube-revenue

**Descrição:** Receita YouTube no período (apenas dados reais)

**Query Parameters:**
```typescript
{
  periodo?: string  // "30d" padrão
}
```

**Response:**
```json
{
  "revenue_brl": 12450.00,
  "revenue_usd": 2254.55,
  "taxa_cambio": 5.52,
  "periodo": "30d",
  "data_inicio": "2023-12-11",
  "data_fim": "2024-01-10"
}
```

**Conversão:** USD → BRL usando AwesomeAPI (taxa atual)

---

### 3. POST /api/financeiro/sync-youtube

**Descrição:** Sincroniza receita YouTube criando lançamentos automáticos

**Query Parameters:**
```typescript
{
  periodo?: string  // "90d" padrão
}
```

**Response:**
```json
{
  "sincronizados": 3,
  "periodo": "90d",
  "meses": 3,
  "taxa_cambio": 5.52,
  "taxa_atualizada_em": "2024-01-10 15:35:03"
}
```

**Lógica:**
- Agrupa revenue por mês (apenas dados reais, `is_estimate=false`)
- Converte USD → BRL usando taxa atual
- Cria lançamento na categoria "YouTube AdSense"
- Evita duplicação (verifica lançamentos existentes)

---

### 4. GET /api/financeiro/projecao-mes

**Descrição:** Projeção de receita para o mês atual

**Response:**
```json
{
  "mes": "2024-01",
  "mes_nome": "January 2024",
  "total_ate_hoje": 4532.00,
  "projecao_mes": 14500.00,
  "media_diaria": 453.20,
  "dias_decorridos": 10,
  "dias_restantes": 21,
  "dias_total": 31,
  "taxa_cambio": 5.52
}
```

**Cálculo:** Média diária × dias totais do mês

---

### 5. GET /api/financeiro/categorias

**Descrição:** Lista categorias financeiras

**Response:**
```json
{
  "categorias": [
    {
      "id": 1,
      "nome": "YouTube AdSense",
      "tipo": "receita",
      "cor": "#00FF00",
      "icon": "youtube",
      "ativo": true
    }
  ]
}
```

---

### 6. POST /api/financeiro/lancamentos

**Descrição:** Cria novo lançamento financeiro

**Request Body:**
```json
{
  "categoria_id": 1,
  "valor": 450.00,
  "data": "2024-01-10",
  "descricao": "Publicidade Instagram",
  "tipo": "despesa",
  "recorrencia": "unica",
  "usuario": "Cellibs"
}
```

**Validações:**
- `recorrencia` só para despesas (`"fixa"` | `"unica"`)
- Receitas sempre `recorrencia=null`

---

### 7. GET /api/financeiro/taxa-cambio

**Descrição:** Taxa de câmbio USD-BRL atualizada

**Response:**
```json
{
  "taxa": 5.52,
  "atualizado_em": "2024-01-10 15:35:03",
  "fonte": "AwesomeAPI"
}
```

**API:** `https://economia.awesomeapi.com.br/last/USD-BRL`

---

## Upload YouTube Endpoints

### 1. POST /api/yt-upload/webhook

**Descrição:** Webhook para receber uploads do Google Sheets

**Request Body (Pydantic Model):**
```python
class WebhookUploadRequest(BaseModel):
    video_url: str          # Google Drive URL
    titulo: str             # EXATO da planilha
    descricao: str          # COM hashtags
    channel_id: str         # UCxxxxxxx
    subnicho: str           # Opcional
    spreadsheet_id: str     # ID da planilha
    row_number: int         # Número da linha
```

**Exemplo:**
```json
{
  "video_url": "https://drive.google.com/file/d/1abc123/view",
  "titulo": "Batalha de Stalingrado",
  "descricao": "História completa #historia #guerra",
  "channel_id": "UCxxxxxx",
  "subnicho": "Guerras Mundiais",
  "spreadsheet_id": "1abc123xyz",
  "row_number": 15
}
```

**Response:**
```json
{
  "success": true,
  "upload_id": 456,
  "status": "pending",
  "message": "Upload adicionado à fila"
}
```

**Fluxo:**
1. Valida dados
2. Insere em `yt_upload_queue` (status: `pending`)
3. Worker processa upload (background)
4. Atualiza Google Sheets (coluna O: "done")

---

### 2. GET /api/yt-upload/status/{upload_id}

**Descrição:** Verifica status de um upload

**Response:**
```json
{
  "upload": {
    "id": 456,
    "status": "completed",
    "channel_id": "UCxxxxxx",
    "titulo": "Batalha de Stalingrado",
    "youtube_video_id": "dQw4w9WgXcQ",
    "started_at": "2024-01-10T08:00:00Z",
    "completed_at": "2024-01-10T08:05:23Z",
    "error_message": null
  }
}
```

**Status possíveis:**
- `pending` - Na fila
- `downloading` - Baixando do Drive
- `uploading` - Enviando para YouTube
- `completed` - Concluído com sucesso
- `failed` - Erro (ver `error_message`)

---

### 3. GET /api/yt-upload/queue

**Descrição:** Lista fila de uploads pendentes

**Response:**
```json
{
  "queue": [
    {
      "id": 457,
      "status": "pending",
      "channel_id": "UCxxxxxx",
      "titulo": "Segunda Guerra Mundial",
      "scheduled_at": "2024-01-10T09:00:00Z"
    }
  ],
  "total_pending": 5
}
```

---

## Transcrições Endpoints

### 1. POST /api/transcribe

**Descrição:** Solicita transcrição de vídeo YouTube

**Request Body:**
```json
{
  "video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "job_id": "trans_20240110_080000",
  "status": "processing",
  "video_id": "dQw4w9WgXcQ"
}
```

**Servidor:** `https://transcription.2growai.com.br`

---

### 2. GET /api/transcribe/status/{job_id}

**Descrição:** Verifica status da transcrição

**Response:**
```json
{
  "job_id": "trans_20240110_080000",
  "status": "completed",
  "transcription": "Texto completo da transcrição...",
  "duration": 45.2,
  "completed_at": "2024-01-10T08:02:00Z"
}
```

---

## Modelos Pydantic

### 1. RegraNotificacaoCreate

```python
class RegraNotificacaoCreate(BaseModel):
    nome_regra: str
    views_minimas: int
    periodo_dias: int
    tipo_canal: str = "ambos"  # "minerado" | "nosso" | "ambos"
    subnichos: Optional[List[str]] = None
```

**Uso:**
```python
@app.post("/api/regras-notificacoes")
async def criar_regra(regra: RegraNotificacaoCreate):
    # Validação automática pelo Pydantic
    return {"success": True}
```

---

### 2. WebhookUploadRequest

```python
class WebhookUploadRequest(BaseModel):
    video_url: str
    titulo: str
    descricao: str
    channel_id: str
    subnicho: Optional[str] = None
    spreadsheet_id: Optional[str] = None
    row_number: Optional[int] = None
```

---

## Padrões de Integração

### 1. Paginação

```python
# Backend
@app.get("/api/videos")
async def get_videos(limit: int = 50, offset: int = 0):
    query = db.supabase.table("videos_monitorados")\
        .select("*")\
        .range(offset, offset + limit - 1)
    return {"videos": response.data, "total": total_count}

# Frontend (Lovable)
const fetchVideos = async (page = 1) => {
  const limit = 50;
  const offset = (page - 1) * limit;
  const response = await fetch(`/api/videos?limit=${limit}&offset=${offset}`);
  return response.json();
};
```

---

### 2. Filtros Dinâmicos

```python
@app.get("/api/canais")
async def get_canais(
    tipo: Optional[str] = None,
    subnicho: Optional[str] = None,
    search: Optional[str] = None
):
    query = db.supabase.table("canais_monitorados").select("*")

    if tipo:
        query = query.eq("tipo", tipo)
    if subnicho:
        query = query.ilike("subnicho", f"%{subnicho}%")
    if search:
        query = query.ilike("nome_canal", f"%{search}%")

    return query.execute()
```

---

### 3. Error Handling

```python
from fastapi import HTTPException

@app.get("/api/canais/{canal_id}")
async def get_canal(canal_id: int):
    try:
        response = db.supabase.table("canais_monitorados")\
            .select("*")\
            .eq("id", canal_id)\
            .single()\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        return response.data

    except Exception as e:
        logger.error(f"Erro ao buscar canal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 4. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Produção: especificar domínio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Testing Endpoints

### 1. Health Check

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}
```

---

### 2. Test API com cURL

```bash
# Listar canais
curl -X GET "http://localhost:8000/api/canais?tipo=minerado&limit=10"

# Adicionar canal
curl -X POST "http://localhost:8000/api/add-canal" \
  -H "Content-Type: application/json" \
  -d '{"url_canal": "https://youtube.com/@exemplo", "tipo": "minerado"}'

# Forçar notificações
curl -X POST "http://localhost:8000/api/force-notifier"
```

---

### 3. Test com Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Listar vídeos
response = requests.get(f"{BASE_URL}/api/videos", params={
    "min_views": 10000,
    "dias": 7,
    "limit": 20
})
print(response.json())

# Criar lançamento financeiro
response = requests.post(f"{BASE_URL}/api/financeiro/lancamentos", json={
    "categoria_id": 1,
    "valor": 450.00,
    "data": "2024-01-10",
    "descricao": "Publicidade",
    "tipo": "despesa"
})
print(response.json())
```

---

## Performance Tips

### 1. Use Indexes (Supabase)

```sql
CREATE INDEX idx_canais_tipo ON canais_monitorados(tipo);
CREATE INDEX idx_videos_canal ON videos_monitorados(canal_id);
CREATE INDEX idx_videos_views ON videos_monitorados(views DESC);
CREATE INDEX idx_notificacoes_vista ON notificacoes(vista);
```

---

### 2. Limit Results

```python
# ❌ Evitar
query.select("*").execute()  # Retorna TUDO

# ✅ Sempre limitar
query.select("*").limit(50).execute()
```

---

### 3. Select Specific Columns

```python
# ❌ Busca tudo (mais lento)
query.select("*")

# ✅ Busca apenas necessário
query.select("id, nome_canal, inscritos")
```

---

## Próximos Passos

1. **Adicionar autenticação JWT** (proteger endpoints sensíveis)
2. **Rate limiting** (limitar requisições por IP)
3. **Caching com Redis** (cache de queries frequentes)
4. **Webhooks** (notificar frontend em tempo real)
5. **Batch operations** (operações em lote)

---

**Referências:**
- Código fonte: `D:\ContentFactory\youtube-dashboard-backend\main.py`
- Lovable frontend: https://lovable.com/projects/[PROJECT_ID]
- Railway deploy: https://railway.app/project/[PROJECT_ID]

---

**Última atualização:** 2024-01-12
