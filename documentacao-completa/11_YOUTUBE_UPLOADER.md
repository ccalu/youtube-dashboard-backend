# 11 - YouTube Uploader

**Sistema completo de upload automatizado para YouTube com OAuth, fila e integração Google Sheets**

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Fluxo de Upload](#fluxo-de-upload)
4. [OAuth Manager](#oauth-manager)
5. [Queue Worker](#queue-worker)
6. [Google Sheets Integration](#google-sheets-integration)
7. [Troubleshooting](#troubleshooting)

---

## Visão Geral

**Localização:** `D:\ContentFactory\youtube-dashboard-backend\yt_uploader\`

**Arquivos:**
- `uploader.py` - Lógica principal de upload (213 linhas)
- `oauth_manager.py` - Gestão de credenciais OAuth (107 linhas)
- `database.py` - Queries Supabase (209 linhas)
- `sheets.py` - Integração Google Sheets (86 linhas)
- `queue_worker.py` - Worker automático (254 linhas)
- `spreadsheet_scanner.py` - Scanner de planilhas (495 linhas)

**Objetivo:** Upload automático de vídeos do Google Drive para YouTube em modo RASCUNHO

---

## Arquitetura

### 1. Componentes

```
┌─────────────────┐
│ Google Sheets   │ (Planilha com metadados)
│ • Título        │
│ • Descrição     │
│ • Drive URL     │
└────────┬────────┘
         │ Webhook (n8n ou manual)
         ↓
┌─────────────────┐
│ Webhook Endpoint│ POST /api/yt-upload/webhook
└────────┬────────┘
         │ Insere em fila
         ↓
┌─────────────────┐
│ Upload Queue    │ yt_upload_queue (Supabase)
│ • status=pending│
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Queue Worker    │ (Roda em background)
│ • Busca pending │
│ • Processa 3x3  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Uploader        │
│ 1. Download     │ Google Drive (gdown)
│ 2. Upload       │ YouTube API (OAuth)
│ 3. Playlist     │ Adiciona à playlist
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Google Sheets   │
│ Coluna O: "done"│
└─────────────────┘
```

---

### 2. Tabelas Supabase

**yt_upload_queue:**
```sql
CREATE TABLE yt_upload_queue (
  id SERIAL PRIMARY KEY,
  channel_id TEXT NOT NULL REFERENCES yt_channels(channel_id),
  video_url TEXT NOT NULL,             -- Google Drive URL
  titulo TEXT NOT NULL,                -- EXATO da planilha
  descricao TEXT,                      -- COM #hashtags
  subnicho TEXT,
  lingua TEXT,
  sheets_row_number INTEGER,           -- Número da linha na planilha
  spreadsheet_id TEXT,                 -- ID da planilha
  status TEXT DEFAULT 'pending',       -- pending|downloading|uploading|completed|failed
  youtube_video_id TEXT,               -- ID após upload bem-sucedido
  error_message TEXT,
  scheduled_at TIMESTAMP DEFAULT NOW(),
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE INDEX idx_upload_status ON yt_upload_queue(status);
CREATE INDEX idx_upload_channel ON yt_upload_queue(channel_id);
```

---

## Fluxo de Upload

### 1. Receber Upload (Webhook)

**Endpoint:** `POST /api/yt-upload/webhook`

**Request Body:**
```json
{
  "video_url": "https://drive.google.com/file/d/1abc123xyz/view",
  "titulo": "Batalha de Stalingrado",
  "descricao": "História completa da batalha #historia #guerra",
  "channel_id": "UCxxxxxx",
  "subnicho": "Guerras Mundiais",
  "spreadsheet_id": "1abc123xyz",
  "row_number": 15
}
```

**Código (main.py):**
```python
class WebhookUploadRequest(BaseModel):
    video_url: str
    titulo: str
    descricao: str
    channel_id: str
    subnicho: Optional[str] = None
    spreadsheet_id: Optional[str] = None
    row_number: Optional[int] = None

@app.post("/api/yt-upload/webhook")
async def receive_upload_webhook(upload: WebhookUploadRequest):
    """Recebe upload do webhook n8n/Sheets"""

    # Validações
    if not upload.video_url or not upload.titulo:
        raise HTTPException(400, "video_url e titulo são obrigatórios")

    # Inserir na fila
    upload_record = create_upload(
        channel_id=upload.channel_id,
        video_url=upload.video_url,
        titulo=upload.titulo,
        descricao=upload.descricao,
        subnicho=upload.subnicho,
        sheets_row=upload.row_number,
        spreadsheet_id=upload.spreadsheet_id
    )

    logger.info(f"✅ Upload {upload_record['id']} adicionado à fila")

    return {
        "success": True,
        "upload_id": upload_record['id'],
        "status": "pending"
    }
```

---

### 2. Processar Upload (Worker)

**Arquivo:** `queue_worker.py`

**Lógica:**
```python
class UploadQueueWorker:
    """Worker que processa fila automaticamente"""

    def __init__(self):
        self.interval_seconds = 120  # Verifica fila a cada 2 minutos
        self.batch_size = 5          # Processa 5 vídeos por vez
        self.max_consecutive_errors = 5

    async def _process_batch(self):
        """Processa batch de uploads pendentes"""

        # 1. Buscar vídeos pendentes
        pending_uploads = get_pending_uploads(limit=self.batch_size)

        if not pending_uploads:
            return  # Nenhum vídeo na fila

        logger.info(f"📤 Processando {len(pending_uploads)} vídeos")

        # 2. Processar cada upload
        tasks = []
        for upload in pending_uploads:
            task = asyncio.create_task(process_upload_task(upload['id']))
            tasks.append(task)

        # 3. Aguardar todos (com tratamento de erros)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. Log de resultados
        succeeded = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - succeeded

        logger.info(f"✅ {succeeded} uploads concluídos, ❌ {failed} falhas")

    async def run(self):
        """Loop principal do worker"""
        while self.is_active:
            try:
                await self._process_batch()
                self.consecutive_errors = 0
            except Exception as e:
                self.consecutive_errors += 1
                if self.consecutive_errors >= self.max_consecutive_errors:
                    logger.critical("🚨 Worker desativado após erros consecutivos")
                    return

            await asyncio.sleep(self.interval_seconds)
```

---

### 3. Download do Google Drive

**Arquivo:** `uploader.py`

**Função:**
```python
def download_video(self, video_url: str, channel_id: str = None) -> str:
    """
    Baixa vídeo do Google Drive usando gdown.
    Aceita URLs: drive.google.com/file/d/FILE_ID ou ?id=FILE_ID

    Bypass automático de "virus scan warning" para arquivos grandes.
    """

    # 1. Extrair file_id da URL
    if '/file/d/' in video_url:
        file_id = video_url.split('/file/d/')[1].split('/')[0]
    elif 'id=' in video_url:
        file_id = video_url.split('id=')[1].split('&')[0]
    else:
        raise ValueError(f"URL do Drive inválida: {video_url}")

    # 2. Caminho de destino (/tmp/videos)
    file_path = os.path.join(self.temp_path, f"{file_id}.mp4")

    # 3. Download usando gdown (lida com virus scan warning)
    download_url = f"https://drive.google.com/uc?id={file_id}"

    try:
        gdown.download(download_url, file_path, quiet=False, fuzzy=True)
    except Exception as e:
        raise ValueError(
            f"Erro ao baixar do Google Drive: {str(e)}. "
            f"Verifique se o arquivo está compartilhado publicamente."
        )

    # 4. Validar download
    if not os.path.exists(file_path):
        raise ValueError("Download falhou - arquivo não foi criado")

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    if file_size_mb < 0.1:  # < 100KB
        os.remove(file_path)
        raise ValueError(f"Arquivo muito pequeno ({file_size_mb:.2f} MB)")

    logger.info(f"✅ Download concluído ({file_size_mb:.1f} MB)")

    return file_path
```

**IMPORTANTE:**
- Usa `gdown` (não `requests`) para bypass de virus scan
- Google Drive bloqueia arquivos grandes com "scan warning"
- `gdown` lida automaticamente com esse problema
- Arquivo deve estar "Anyone with the link" (compartilhado)

---

### 4. Upload para YouTube

**Função:**
```python
def upload_to_youtube(self, channel_id: str, video_path: str, metadata: Dict) -> Dict:
    """
    Faz upload de vídeo para YouTube em modo RASCUNHO.

    IMPORTANTE:
    - Título e descrição são usados EXATAMENTE como vem (sem alteração)
    - Vídeo fica PRIVATE (rascunho) - nunca publicado automaticamente
    - Upload direto via YouTube Data API (sem proxy)
    """

    # 1. Sanitizar título UTF-8 (fix para caracteres especiais)
    titulo_sanitized = unicodedata.normalize('NFC', metadata['titulo'])
    titulo_sanitized = titulo_sanitized.encode('utf-8', errors='ignore').decode('utf-8')
    titulo_sanitized = titulo_sanitized.replace('\ufffd', 'O')  # Remove �

    # YouTube limite = 100 caracteres
    if len(titulo_sanitized) > 100:
        titulo_sanitized = titulo_sanitized[:97] + "..."

    # 2. Buscar configuração do canal
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError(f"Canal {channel_id} não encontrado")

    # 3. Obter credenciais OAuth válidas
    credentials = OAuthManager.get_valid_credentials(channel_id)

    # 4. Criar serviço YouTube API
    youtube = build('youtube', 'v3', credentials=credentials)

    # 5. Preparar metadata
    body = {
        'snippet': {
            'title': titulo_sanitized,
            'description': metadata['descricao'],  # EXATO da planilha (COM #hashtags)
            'categoryId': '24',  # Entertainment
            'defaultLanguage': channel.get('lingua', 'en'),
            'defaultAudioLanguage': channel.get('lingua', 'en')
        },
        'status': {
            'privacyStatus': 'private',  # ← RASCUNHO!!!
            'selfDeclaredMadeForKids': False,
            'containsSyntheticMedia': True  # ← MARCA COMO CONTEÚDO IA
        }
    }

    # 6. Preparar arquivo para upload (resumable)
    media = MediaFileUpload(
        video_path,
        chunksize=1024*1024*5,  # 5MB chunks
        resumable=True
    )

    # 7. Executar upload com progress tracking
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            logger.info(f"⬆️  Upload: {progress}%")

    video_id = response['id']

    # 8. Adicionar à playlist (se configurado)
    if channel.get('default_playlist_id'):
        playlist_id = channel['default_playlist_id']
        youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        ).execute()

    return {
        'success': True,
        'video_id': video_id
    }
```

**Features:**
- UTF-8 sanitization (caracteres especiais alemães, franceses, etc)
- Upload SEMPRE em modo `private` (rascunho)
- Marca vídeo como synthetic media (IA)
- Adiciona automaticamente à playlist do canal
- Progress tracking (logs de progresso)

---

## OAuth Manager

### 1. Arquitetura

**Arquivo:** `oauth_manager.py`

**Nova arquitetura (v2.0):**
```
1 Canal = 1 Client ID/Secret (isolado)

✅ Vantagens:
- Isolamento total entre canais
- Ban de 1 canal não afeta outros
- Contingência máxima
- Rastreabilidade perfeita
```

**Arquitetura antiga (v1.0 - DEPRECATED):**
```
1 Proxy = 3 Canais (compartilham Client ID/Secret)

❌ Problemas:
- Ban de 1 canal → 3 canais afetados
- Risco de ban em massa
```

---

### 2. Get Valid Credentials

```python
class OAuthManager:
    """Gerencia autenticação OAuth dos canais"""

    @staticmethod
    def get_valid_credentials(channel_id: str) -> Credentials:
        """
        Retorna credenciais OAuth válidas para um canal.
        Renova automaticamente se expirado.

        NOVA ARQUITETURA (v2.0):
        - Busca credenciais direto do canal (yt_channel_credentials)
        - Fallback para proxy (yt_proxy_credentials) se necessário
        - Isolamento total entre canais
        """

        # 1. Buscar dados do canal
        channel = get_channel(channel_id)
        if not channel:
            raise ValueError(f"Canal {channel_id} não encontrado")

        # 2. Buscar tokens OAuth
        oauth = get_oauth_tokens(channel_id)
        if not oauth or not oauth.get('refresh_token'):
            raise ValueError(f"Canal {channel_id} sem OAuth configurado")

        # 3. NOVA ARQUITETURA: Buscar credenciais do canal
        channel_creds = get_channel_credentials(channel_id)

        if channel_creds:
            # Arquitetura nova: credenciais isoladas
            client_id = channel_creds['client_id']
            client_secret = channel_creds['client_secret']
            logger.info(f"✅ Usando credenciais isoladas do canal")
        else:
            # FALLBACK: Arquitetura antiga (compatibilidade)
            proxy_name = channel.get('proxy_name')
            if not proxy_name:
                raise ValueError("Canal sem credenciais")

            proxy_creds = get_proxy_credentials(proxy_name)
            client_id = proxy_creds['client_id']
            client_secret = proxy_creds['client_secret']
            logger.warning(f"⚠️ Usando proxy: {proxy_name} (DEPRECATED)")

        # 4. Criar objeto Credentials
        credentials = Credentials(
            token=oauth.get('access_token'),
            refresh_token=oauth.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )

        # 5. Renovar se expirado
        if credentials.expired and credentials.refresh_token:
            logger.info(f"⚠️ Token expirado, renovando...")

            credentials.refresh(Request())

            # Salvar novo token no banco
            update_oauth_tokens(
                channel_id=channel_id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=credentials.expiry.isoformat()
            )

            logger.info(f"✅ Token renovado com sucesso")

        return credentials
```

---

## Queue Worker

### 1. Configuração

**ENV Variables:**
```bash
UPLOAD_WORKER_ENABLED=true              # Habilitar/desabilitar worker
UPLOAD_WORKER_INTERVAL_SECONDS=120      # Intervalo entre verificações (2 min)
UPLOAD_WORKER_BATCH_SIZE=5              # Máximo de vídeos por vez
UPLOAD_WORKER_MAX_ERRORS=5              # Max erros consecutivos antes de desligar
UPLOAD_WORKER_MIN_FREE_MEMORY_MB=200    # Memória mínima disponível
UPLOAD_WORKER_MIN_FREE_DISK_MB=500      # Disco mínimo disponível (/tmp)
UPLOAD_WORKER_STARTUP_DELAY=180         # Delay inicial (3 min)
```

---

### 2. Circuit Breaker

**Lógica:**
```python
# Se erros consecutivos >= 5, worker auto-desliga
if self.consecutive_errors >= self.max_consecutive_errors:
    self.is_active = False
    logger.critical("🚨 WORKER DESATIVADO após erros consecutivos")
    return
```

**Benefícios:**
- Protege Railway de gastar recursos desnecessariamente
- Evita loop infinito de erros
- Logs claros de quando/por que desligou

---

### 3. Resource Monitoring

```python
def check_resources(self) -> tuple[bool, str]:
    """Verifica se há recursos suficientes para processar uploads"""

    # 1. Memória disponível (usando psutil)
    import psutil
    memory = psutil.virtual_memory()
    available_mb = memory.available / (1024 * 1024)

    if available_mb < self.min_free_memory_mb:
        return False, f"Memória insuficiente: {available_mb:.0f}MB"

    # 2. Espaço em disco (/tmp para vídeos)
    import shutil
    stat = shutil.disk_usage('/tmp')
    available_mb = stat.free / (1024 * 1024)

    if available_mb < self.min_free_disk_mb:
        return False, f"Disco insuficiente: {available_mb:.0f}MB"

    return True, "OK"
```

---

## Google Sheets Integration

### 1. Service Account Setup

**Arquivo:** `sheets.py`

**Credenciais:**
```bash
# Railway env var (JSON)
GOOGLE_SHEETS_CREDENTIALS_2='{"type":"service_account","project_id":"...",...}'
```

**Função:**
```python
def get_sheets_client():
    """
    Cria cliente gspread autenticado via Service Account.
    Credenciais vêm da variável GOOGLE_SHEETS_CREDENTIALS_2 (JSON).
    """

    # Parse JSON das credenciais
    credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_2')
    credentials_dict = json.loads(credentials_json)

    # Escopos necessários
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    # Criar credentials do Service Account
    credentials = Credentials.from_service_account_info(
        credentials_dict,
        scopes=scopes
    )

    # Retornar client autenticado
    return gspread.authorize(credentials)
```

---

### 2. Atualizar Planilha

**Função:**
```python
def update_upload_status_in_sheet(spreadsheet_id: str, row: int, status: str):
    """
    Atualiza coluna O (Upload) na planilha Google Sheets.

    Args:
        spreadsheet_id: ID da planilha (da URL)
        row: Número da linha (começa em 1, header é linha 1)
        status: Status a escrever (ex: "done", "❌ Erro")
    """

    # 1. Conectar ao Google Sheets
    client = get_sheets_client()

    # 2. Abrir planilha
    spreadsheet = client.open_by_key(spreadsheet_id)

    # 3. Abrir aba "Página1"
    worksheet = spreadsheet.worksheet('Página1')

    # 4. Atualizar célula O{row} (coluna 15)
    worksheet.update_cell(row, 15, status)

    # 5. Formatar célula (fonte preta)
    worksheet.format(f'O{row}', {
        "textFormat": {
            "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0},
            "bold": False
        }
    })

    logger.info(f"✅ Planilha atualizada - Row {row}: {status}")
```

**Colunas típicas:**
```
A: Thumbnail
B: Drive URL
C: Título
D: Descrição
...
O: Upload (atualizado após upload)
```

---

## Troubleshooting

### 1. Download Falha (Google Drive)

**Sintomas:**
- Erro "file too large" ou "virus scan warning"
- Download retorna HTML ao invés de vídeo

**Causa:** Google Drive bloqueia downloads grandes

**Solução:**
```python
# ✅ CORRETO: Usar gdown (lida com virus scan)
import gdown
gdown.download(drive_url, file_path, fuzzy=True)

# ❌ ERRADO: Usar requests (não funciona para arquivos grandes)
requests.get(drive_url)
```

---

### 2. OAuth Expirado

**Sintomas:**
- Erro 401 Unauthorized
- "Token expired"

**Causa:** Access token expirou (expira em ~1h)

**Solução:** Sistema renova automaticamente usando `refresh_token`

**Debug:**
```python
from yt_uploader.oauth_manager import OAuthManager

# Forçar renovação
credentials = OAuthManager.get_valid_credentials("UCxxxxxx")
print(f"Token: {credentials.token[:20]}...")
print(f"Expiry: {credentials.expiry}")
```

---

### 3. Worker Não Processa

**Sintomas:**
- Vídeos ficam `status=pending` na fila
- Nenhum log de processamento

**Causas possíveis:**

**a) Worker desabilitado:**
```bash
# Verificar env var
echo $UPLOAD_WORKER_ENABLED
# Deve ser "true"
```

**b) Worker em startup delay:**
```bash
# Verificar logs
# "Upload worker aguardando 180s (startup protection)"
# Aguardar 3 minutos após deploy
```

**c) Worker desligou (circuit breaker):**
```bash
# Verificar logs
# "🚨 WORKER DESATIVADO após 5 erros consecutivos"
# Redeployar Railway
```

---

### 4. UTF-8 Encoding Error

**Sintomas:**
- Erro "invalid character in title"
- Caracteres especiais quebrados (ö, ü, ñ, etc)

**Causa:** YouTube rejeita alguns caracteres UTF-8

**Solução:** Sanitização automática implementada
```python
titulo_sanitized = unicodedata.normalize('NFC', titulo)
titulo_sanitized = titulo_sanitized.encode('utf-8', errors='ignore').decode('utf-8')
titulo_sanitized = titulo_sanitized.replace('\ufffd', 'O')  # Remove �
```

---

### 5. Playlist Add Falha

**Sintomas:**
- Upload sucesso, mas não aparece na playlist
- Log: "Erro ao adicionar à playlist"

**Causas:**
- `default_playlist_id` incorreto no canal
- Playlist não existe
- OAuth sem permissão de playlist

**Solução:**
```sql
-- Verificar playlist ID
SELECT channel_id, default_playlist_id FROM yt_channels WHERE channel_id = 'UCxxxxxx';

-- Atualizar se necessário
UPDATE yt_channels
SET default_playlist_id = 'PLxxxxxxxxxxxxxx'
WHERE channel_id = 'UCxxxxxx';
```

---

## Fluxo Completo (Exemplo Real)

### 1. Setup Canal Novo

```bash
# 1. Criar projeto Google Cloud
# 2. Ativar YouTube Data API v3
# 3. Criar OAuth 2.0 Client ID
# 4. Salvar credenciais no Supabase
```

```python
from yt_uploader.database import save_channel_credentials

save_channel_credentials(
    channel_id="UCxxxxxx",
    client_id="123-abc.apps.googleusercontent.com",
    client_secret="GOCSPX-xxx"
)
```

```bash
# 5. Autorizar canal (gera tokens OAuth)
python autorizar_canal.py UCxxxxxx

# 6. Configurar playlist padrão
```

```sql
UPDATE yt_channels
SET default_playlist_id = 'PLxxxxxxxxxxxxxx'
WHERE channel_id = 'UCxxxxxx';
```

---

### 2. Upload Manual (via API)

```bash
curl -X POST http://localhost:8000/api/yt-upload/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://drive.google.com/file/d/1abc123/view",
    "titulo": "Batalha de Stalingrado",
    "descricao": "História completa #historia #guerra",
    "channel_id": "UCxxxxxx",
    "subnicho": "Guerras Mundiais"
  }'
```

**Response:**
```json
{
  "success": true,
  "upload_id": 456,
  "status": "pending"
}
```

---

### 3. Verificar Status

```bash
curl http://localhost:8000/api/yt-upload/status/456
```

**Response:**
```json
{
  "upload": {
    "id": 456,
    "status": "completed",
    "youtube_video_id": "dQw4w9WgXcQ",
    "completed_at": "2024-01-10T08:05:23Z"
  }
}
```

---

### 4. Verificar Vídeo no YouTube

```
https://studio.youtube.com → Conteúdo → Filtrar por "Não listados"
```

**Status esperado:**
- Vídeo em modo PRIVATE (rascunho)
- Título correto
- Descrição completa (com hashtags)
- Adicionado à playlist

---

**Referências:**
- YouTube Data API: https://developers.google.com/youtube/v3
- gdown docs: https://github.com/wkentaro/gdown
- gspread docs: https://docs.gspread.org

---

**Última atualização:** 2024-01-12
