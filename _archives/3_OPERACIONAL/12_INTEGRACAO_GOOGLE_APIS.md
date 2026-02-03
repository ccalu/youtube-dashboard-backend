# 12 - Integração com Google APIs

**Guia completo de todas as integrações Google utilizadas no sistema**

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Google Sheets API](#google-sheets-api)
3. [Google Drive API](#google-drive-api)
4. [YouTube Data API v3](#youtube-data-api-v3)
5. [YouTube Analytics API v3](#youtube-analytics-api-v3)
6. [Setup e Permissões](#setup-e-permissões)

---

## Visão Geral

**APIs utilizadas:**
1. **Google Sheets API** - Integração com planilhas (metadados)
2. **Google Drive API** - Download de vídeos
3. **YouTube Data API v3** - Mineração de canais/vídeos + Upload
4. **YouTube Analytics API v3** - Revenue e métricas OAuth

**Tipos de autenticação:**
- **Service Account** - Google Sheets (sem interação usuário)
- **OAuth 2.0** - YouTube upload e Analytics (autorização por canal)
- **API Key** - YouTube Data API (mineração, leitura pública)

---

## Google Sheets API

### 1. Propósito

**Uso:** Ler/escrever metadados de vídeos (título, descrição, status upload)

**Biblioteca:** `gspread` (Python wrapper)

**Autenticação:** Service Account (JSON key)

---

### 2. Service Account Setup

**Passo 1: Criar Service Account**
```
1. Google Cloud Console → IAM & Admin → Service Accounts
2. Create Service Account
3. Name: "youtube-sheets-integration"
4. Role: (não precisa de role, apenas API access)
5. Create Key → JSON → Download
```

**Passo 2: Habilitar Google Sheets API**
```
1. APIs & Services → Library
2. Buscar "Google Sheets API"
3. Enable
```

**Passo 3: Compartilhar Planilhas**
```
1. Abrir planilha no Google Sheets
2. Compartilhar com email do Service Account:
   exemplo@project-id.iam.gserviceaccount.com
3. Permissão: Editor
```

---

### 3. Configurar no Railway

**ENV Variable:**
```bash
GOOGLE_SHEETS_CREDENTIALS_2='{"type":"service_account","project_id":"youtube-dashboard-123","private_key_id":"abc123...","private_key":"-----BEGIN PRIVATE KEY-----\n...","client_email":"youtube-sheets@project.iam.gserviceaccount.com","client_id":"123456789","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token"}'
```

**IMPORTANTE:** JSON em string única (sem quebras de linha no meio)

---

### 4. Uso no Código

**Arquivo:** `yt_uploader/sheets.py`

```python
import gspread
from google.oauth2.service_account import Credentials
import json
import os

def get_sheets_client():
    """Cria cliente gspread autenticado"""

    # 1. Buscar credenciais do env
    credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_2')
    credentials_dict = json.loads(credentials_json)

    # 2. Definir escopos necessários
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    # 3. Criar credentials
    credentials = Credentials.from_service_account_info(
        credentials_dict,
        scopes=scopes
    )

    # 4. Retornar client autenticado
    return gspread.authorize(credentials)
```

**Exemplo de uso:**
```python
# Abrir planilha
client = get_sheets_client()
spreadsheet = client.open_by_key('1abc123xyz')
worksheet = spreadsheet.worksheet('Página1')

# Ler célula
valor = worksheet.cell(2, 3).value  # Linha 2, Coluna 3

# Escrever célula
worksheet.update_cell(2, 15, 'done')  # Coluna O (15)

# Ler range
data = worksheet.get('A2:D10')  # Array 2D

# Buscar linha por valor
row = worksheet.find('Batalha de Stalingrado').row
```

---

### 5. Rate Limits

**Limites Google Sheets API:**
- **Read requests:** 100 requests/100s por usuário
- **Write requests:** 100 requests/100s por usuário
- **Total queries:** 500 queries/100s por projeto

**Best Practices:**
- Usar batch updates quando possível
- Cache de leituras
- Retry com exponential backoff

**Batch Update (múltiplas células):**
```python
# ❌ Lento (múltiplas requests)
for i in range(10):
    worksheet.update_cell(i+2, 15, 'done')

# ✅ Rápido (1 request)
worksheet.batch_update([{
    'range': 'O2:O11',
    'values': [['done']] * 10
}])
```

---

## Google Drive API

### 1. Propósito

**Uso:** Download de vídeos produzidos (arquivos grandes, 50-200MB)

**Biblioteca:** `gdown` (Python, não oficial mas funciona melhor)

**Autenticação:** Não precisa (arquivos públicos com "Anyone with the link")

---

### 2. Setup

**Compartilhar Vídeos:**
```
1. Google Drive → Selecionar vídeo
2. Botão direito → Share → "Anyone with the link" → Viewer
3. Copy link
```

**Formato de URL:**
```
https://drive.google.com/file/d/1abc123xyz/view
ou
https://drive.google.com/uc?id=1abc123xyz
```

---

### 3. Download com gdown

**Instalação:**
```bash
pip install gdown
```

**Código:**
```python
import gdown
import os

def download_from_drive(drive_url: str, output_path: str) -> str:
    """
    Baixa arquivo do Google Drive.
    Lida automaticamente com virus scan warning (arquivos grandes).
    """

    # 1. Extrair file_id da URL
    if '/file/d/' in drive_url:
        file_id = drive_url.split('/file/d/')[1].split('/')[0]
    elif 'id=' in drive_url:
        file_id = drive_url.split('id=')[1].split('&')[0]
    else:
        raise ValueError("URL inválida")

    # 2. Construir URL de download
    download_url = f"https://drive.google.com/uc?id={file_id}"

    # 3. Download
    # fuzzy=True: Lida com virus scan warning
    # quiet=False: Mostra progress bar
    gdown.download(download_url, output_path, quiet=False, fuzzy=True)

    # 4. Validar
    if not os.path.exists(output_path):
        raise ValueError("Download falhou")

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)

    if file_size_mb < 0.1:  # < 100KB
        raise ValueError("Arquivo muito pequeno (provável erro)")

    return output_path
```

---

### 4. Troubleshooting Virus Scan

**Problema:**
Google Drive bloqueia downloads diretos de arquivos grandes (>25MB) com mensagem:
```
"Google Drive can't scan this file for viruses"
```

**Solução: gdown**
```python
# ✅ CORRETO: gdown lida automaticamente
import gdown
gdown.download(url, output, fuzzy=True)  # fuzzy=True é essencial

# ❌ ERRADO: requests retorna HTML ao invés de vídeo
import requests
response = requests.get(url)  # Retorna página HTML de aviso
```

**Alternativa manual (sem gdown):**
```python
# Extrair confirm token da resposta e fazer segundo request
# Complexo e instável - melhor usar gdown
```

---

## YouTube Data API v3

### 1. Propósito

**Usos:**
- **Mineração:** Buscar canais, vídeos, statistics (público)
- **Upload:** Enviar vídeos para YouTube (OAuth)

**Autenticação:**
- **Mineração:** API Key (leitura pública)
- **Upload:** OAuth 2.0 (escrita, precisa autorização)

---

### 2. API Keys (Mineração)

**Setup:**
```
1. Google Cloud Console → APIs & Services → Credentials
2. Create Credentials → API Key
3. Restrict Key:
   - API restrictions → YouTube Data API v3
   - (Opcional) Application restrictions → HTTP referrers
```

**Configurar no Railway:**
```bash
# 20 chaves para rotação
YOUTUBE_API_KEY_3=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_4=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
...
YOUTUBE_API_KEY_32=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### 3. Quota YouTube Data API v3

**Limite:** 10,000 units/dia por projeto (por API key)

**Custos por operação:**
```
channels.list (statistics):     1 unit
search.list:                   100 units
videos.list:                     1 unit
commentThreads.list:             1 unit
playlistItems.list:              1 unit
videos.insert (upload):         1600 units
```

**Sistema atual:**
- 20 chaves = 200,000 units/dia
- Coleta diária gasta ~145,000 units (150 canais)
- Margem: ~55,000 units (extras/testes)

---

### 4. Endpoints Utilizados

**a) channels.list (Buscar dados do canal)**
```python
import requests

url = "https://www.googleapis.com/youtube/v3/channels"
params = {
    'part': 'snippet,statistics',
    'id': 'UCxxxxxx',
    'key': 'AIzaSyAxxxxx'
}

response = requests.get(url, params=params)
data = response.json()

# Response:
{
  "items": [{
    "id": "UCxxxxxx",
    "snippet": {
      "title": "Canal Exemplo",
      "description": "...",
      "thumbnails": {...}
    },
    "statistics": {
      "subscriberCount": "150000",
      "videoCount": "234",
      "viewCount": "5000000"
    }
  }]
}
```

**Custo:** 1 unit

---

**b) videos.list (Buscar dados de vídeos)**
```python
url = "https://www.googleapis.com/youtube/v3/videos"
params = {
    'part': 'snippet,statistics',
    'id': 'dQw4w9WgXcQ',  # Pode passar até 50 IDs separados por vírgula
    'key': 'AIzaSyAxxxxx'
}

# Response:
{
  "items": [{
    "id": "dQw4w9WgXcQ",
    "snippet": {
      "title": "Batalha de Stalingrado",
      "description": "...",
      "publishedAt": "2024-01-01T10:00:00Z"
    },
    "statistics": {
      "viewCount": "45000",
      "likeCount": "2300",
      "commentCount": "450"
    }
  }]
}
```

**Custo:** 1 unit (até 50 vídeos)

---

**c) search.list (Buscar vídeos de um canal)**
```python
url = "https://www.googleapis.com/youtube/v3/search"
params = {
    'part': 'snippet',
    'channelId': 'UCxxxxxx',
    'order': 'date',
    'type': 'video',
    'maxResults': 50,
    'publishedAfter': '2024-01-01T00:00:00Z',
    'key': 'AIzaSyAxxxxx'
}

# Response:
{
  "items": [{
    "id": {"videoId": "dQw4w9WgXcQ"},
    "snippet": {
      "title": "Batalha de Stalingrado",
      "publishedAt": "2024-01-01T10:00:00Z",
      "thumbnails": {...}
    }
  }]
}
```

**Custo:** 100 units (caro!)

**IMPORTANTE:** Nosso collector usa `playlistItems.list` (1 unit) ao invés de `search.list` (100 units) → economia de 100x

---

**d) videos.insert (Upload de vídeo)**
```python
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

youtube = build('youtube', 'v3', credentials=oauth_credentials)

body = {
    'snippet': {
        'title': 'Batalha de Stalingrado',
        'description': '...',
        'categoryId': '24'
    },
    'status': {
        'privacyStatus': 'private'
    }
}

media = MediaFileUpload('video.mp4', resumable=True)

request = youtube.videos().insert(
    part='snippet,status',
    body=body,
    media_body=media
)

response = request.execute()
```

**Custo:** 1600 units (mais caro!)

---

## YouTube Analytics API v3

### 1. Propósito

**Uso:** Coletar revenue real e métricas avançadas (OAuth por canal)

**Autenticação:** OAuth 2.0 (precisa autorização do dono do canal)

**Diferença do Data API:**
- **Data API:** Dados públicos (views, likes, etc) - Qualquer um pode ver
- **Analytics API:** Dados privados (revenue, demographics, CTR) - Só o dono

---

### 2. Setup

**Habilitar API:**
```
Google Cloud Console → APIs & Services → Library
→ YouTube Analytics API → Enable
```

**OAuth 2.0 Client ID:**
```
1. Credentials → Create Credentials → OAuth client ID
2. Application type: Web application
3. Authorized redirect URIs:
   http://localhost:8000/oauth/callback
   https://your-backend.railway.app/oauth/callback
4. Download JSON (ou copiar Client ID + Secret)
```

---

### 3. Scopes Necessários

```python
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.upload"  # Se for fazer upload
]
```

---

### 4. Endpoints Utilizados

**a) Daily Metrics (Revenue diário)**
```python
url = "https://youtubeanalytics.googleapis.com/v2/reports"
headers = {"Authorization": f"Bearer {access_token}"}

params = {
    "ids": f"channel=={channel_id}",
    "startDate": "2024-01-01",
    "endDate": "2024-01-10",
    "metrics": "estimatedRevenue,views,likes,comments,shares,subscribersGained,subscribersLost,estimatedMinutesWatched",
    "dimensions": "day",
    "sort": "day"
}

response = requests.get(url, params=params, headers=headers)

# Response:
{
  "columnHeaders": [
    {"name": "day", "dataType": "STRING"},
    {"name": "estimatedRevenue", "dataType": "FLOAT"},
    {"name": "views", "dataType": "INTEGER"},
    ...
  ],
  "rows": [
    ["2024-01-01", 12.45, 5432, 234, 45, 12, 15, 2, 2340],
    ["2024-01-02", 15.67, 6234, 312, 67, 23, 18, 3, 3120]
  ]
}
```

**Custo:** 1 query (limite: 50,000 queries/dia)

---

**b) Country Metrics (Revenue por país)**
```python
params = {
    "ids": f"channel=={channel_id}",
    "startDate": "2024-01-01",
    "endDate": "2024-01-10",
    "metrics": "views,estimatedRevenue,estimatedMinutesWatched",
    "dimensions": "country",
    "sort": "-views",
    "maxResults": "25"
}
```

---

**c) Traffic Sources (Fontes de tráfego)**
```python
params = {
    "ids": f"channel=={channel_id}",
    "startDate": "2024-01-01",
    "endDate": "2024-01-10",
    "metrics": "views,estimatedMinutesWatched",
    "dimensions": "insightTrafficSourceType",
    "sort": "-views"
}

# Response:
{
  "rows": [
    ["YT_SEARCH", 12000, 6000],      # Busca YouTube
    ["YT_RELATED", 8500, 4250],      # Vídeos sugeridos
    ["NOTIFICATION", 3200, 1600],    # Notificações
    ["EXTERNAL", 1500, 750]          # Sites externos
  ]
}
```

---

**d) Demographics (Idade e Gênero)**
```python
params = {
    "ids": f"channel=={channel_id}",
    "startDate": "2024-01-01",
    "endDate": "2024-01-10",
    "metrics": "viewerPercentage",
    "dimensions": "ageGroup,gender",
    "sort": "-viewerPercentage"
}

# Response:
{
  "rows": [
    ["age25-34", "male", 32.5],
    ["age18-24", "male", 28.3],
    ["age25-34", "female", 15.2]
  ]
}
```

---

### 5. Rate Limits

**YouTube Analytics API:**
- **Queries:** 50,000 queries/dia por projeto
- **Concurrent requests:** Sem limite explícito

**IMPORTANTE:**
- Cada report query = 1 query
- Bem mais generoso que Data API (10k units/dia)
- 16 canais × 5 métricas × 1 query = 80 queries/dia (muito abaixo do limite)

---

## Setup e Permissões

### 1. Checklist Completo (Canal Novo)

**Google Cloud Console:**
- [ ] Criar projeto (ou usar existente)
- [ ] Ativar APIs:
  - [ ] YouTube Data API v3
  - [ ] YouTube Analytics API v3
  - [ ] Google Sheets API
  - [ ] Google Drive API
- [ ] Criar API Key (para mineração)
- [ ] Criar OAuth 2.0 Client ID (para upload/analytics)
- [ ] Criar Service Account + JSON key (para Sheets)

**Google Sheets:**
- [ ] Compartilhar planilha com Service Account email
- [ ] Permissão: Editor

**Google Drive:**
- [ ] Vídeos compartilhados como "Anyone with the link"
- [ ] Permissão: Viewer

**Supabase:**
- [ ] Salvar API Key em `YOUTUBE_API_KEY_X` (Railway)
- [ ] Salvar OAuth Client ID/Secret em `yt_channel_credentials`
- [ ] Salvar Service Account JSON em `GOOGLE_SHEETS_CREDENTIALS_2`

**Autorização OAuth:**
- [ ] Rodar `autorizar_canal.py` para gerar tokens
- [ ] Tokens salvos em `yt_oauth_tokens`

---

### 2. Permissões IAM (Service Account)

**Mínimas necessárias:**
```
Google Sheets API: Read/Write
Google Drive API: Read-only
```

**Não precisa:**
- Roles de IAM do projeto (conta não precisa acessar recursos GCP)
- Apenas precisa access às APIs públicas

---

### 3. Permissões OAuth Scopes

**Mineração + Upload + Analytics:**
```python
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"  # Acesso completo (se necessário)
]
```

**Apenas Mineração:**
```python
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly"
]
```

**Apenas Analytics:**
```python
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]
```

---

### 4. Renovação de Tokens

**Access Token:**
- Expira em ~1 hora
- Sistema renova automaticamente usando `refresh_token`

**Refresh Token:**
- Não expira (até ser revogado)
- Obtido na primeira autorização (com `prompt=consent`)
- Se perdido/revogado: precisa reautorizar canal

**Código de renovação:**
```python
import requests

def refresh_access_token(refresh_token, client_id, client_secret):
    """Renova access_token usando refresh_token"""

    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    })

    if resp.status_code == 200:
        return resp.json().get("access_token")

    # Erro: refresh_token inválido/revogado
    return None
```

---

### 5. Testing APIs

**Test YouTube Data API (API Key):**
```bash
curl "https://www.googleapis.com/youtube/v3/channels?part=statistics&id=UCxxxxxx&key=AIzaSyAxxxxx"
```

**Test YouTube Analytics API (OAuth):**
```bash
curl "https://youtubeanalytics.googleapis.com/v2/reports?ids=channel==UCxxxxxx&startDate=2024-01-01&endDate=2024-01-10&metrics=views" \
  -H "Authorization: Bearer ya29.a0xxxxxxxxxxxxx"
```

**Test Google Sheets API (Service Account):**
```python
from yt_uploader.sheets import get_sheets_client

client = get_sheets_client()
spreadsheet = client.open_by_key('1abc123xyz')
print(spreadsheet.title)  # Deve printar nome da planilha
```

---

**Referências:**
- YouTube Data API: https://developers.google.com/youtube/v3
- YouTube Analytics API: https://developers.google.com/youtube/analytics
- Google Sheets API: https://developers.google.com/sheets/api
- Google Drive API: https://developers.google.com/drive
- OAuth 2.0: https://developers.google.com/identity/protocols/oauth2

---

**Última atualização:** 2024-01-12
