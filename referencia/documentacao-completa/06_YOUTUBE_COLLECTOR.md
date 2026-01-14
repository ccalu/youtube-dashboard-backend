# 06 - YouTube Data Collection System

**Arquivo:** `D:\ContentFactory\youtube-dashboard-backend\collector.py` (792 linhas)
**Classe Principal:** `YouTubeCollector`
**Propósito:** Sistema robusto de coleta de dados do YouTube com 20 API keys, rate limiting inteligente, e retry logic

---

## Índice

1. [Visão Geral](#visão-geral)
2. [RateLimiter Class](#ratelimiter-class)
3. [YouTubeCollector Class](#youtubecollector-class)
4. [Sistema de API Keys](#sistema-de-api-keys)
5. [Quota Management](#quota-management)
6. [Métodos de Coleta](#métodos-de-coleta)
7. [Error Handling & Retry](#error-handling--retry)
8. [Otimizações](#otimizações)
9. [Integração com main.py](#integração-com-mainpy)
10. [Troubleshooting](#troubleshooting)

---

## Visão Geral

O `YouTubeCollector` é o coração do sistema de mineração de dados do YouTube. Ele foi projetado para coletar dados de até **80 canais** sem exceder os limites da API do YouTube.

### Capacidade Total

```python
# 20 API Keys × 10,000 units/dia = 200,000 units/dia
#
# Custos por requisição:
# - search.list = 100 units (MUITO CARA!)
# - channels.list = 1 unit
# - videos.list = 1 unit
#
# Coleta típica por canal:
# - get_channel_id (se não cached): 1-100 units
# - get_channel_info: 1 unit
# - get_channel_videos (30 dias): ~100-200 units
# - get_video_details (batches): 1-2 units
#
# Total médio: 150-300 units/canal
# Capacidade: ~650-1300 canais/dia (mas limitamos a 80 por questão de qualidade)
```

### Localização no Sistema

```
D:\ContentFactory\youtube-dashboard-backend\
├── collector.py          ← Você está aqui
├── main.py               ← Chama o collector (run_collection_job)
├── database.py           ← Salva os dados coletados
└── .env                  ← API keys (Railway apenas)
```

---

## RateLimiter Class

**Linhas:** 23-82
**Propósito:** Respeitar o limite de 100 req/100s do YouTube

### Funcionamento

```python
class RateLimiter:
    def __init__(self, max_requests: int = 90, time_window: int = 100):
        """
        max_requests: 90 (margem de segurança, limite real é 100)
        time_window: 100 segundos
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()  # Armazena timestamps
```

### Métodos Principais

#### 1. `_clean_old_requests()`
```python
def _clean_old_requests(self):
    """Remove requisições antigas (fora da janela de 100s)"""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=self.time_window)

    while self.requests and self.requests[0] < cutoff:
        self.requests.popleft()
```

#### 2. `can_make_request()` → bool
```python
def can_make_request(self) -> bool:
    """Verifica se pode fazer uma nova requisição"""
    self._clean_old_requests()
    return len(self.requests) < self.max_requests
```

#### 3. `get_wait_time()` → float
```python
def get_wait_time(self) -> float:
    """Calcula quanto tempo deve aguardar antes da próxima requisição"""
    self._clean_old_requests()

    if len(self.requests) < self.max_requests:
        return 0.0

    # Calcular quando a requisição mais antiga expira
    oldest = self.requests[0]
    now = datetime.now(timezone.utc)
    wait = (oldest + timedelta(seconds=self.time_window)) - now
    return max(0.0, wait.total_seconds())
```

#### 4. `wait_if_needed()` (async)
```python
async def wait_if_needed(self):
    """Aguarda automaticamente se necessário antes de fazer requisição"""
    wait_time = self.get_wait_time()
    if wait_time > 0:
        logger.info(f"⏳ Rate limit próximo - aguardando {wait_time:.1f}s")
        await asyncio.sleep(wait_time + 0.5)  # +0.5s de margem
```

### Exemplo de Uso

```python
rate_limiter = RateLimiter()

# Antes de fazer requisição
await rate_limiter.wait_if_needed()

# Fazer requisição à API
response = await make_youtube_request()

# Registrar que requisição foi feita
rate_limiter.record_request()
```

---

## YouTubeCollector Class

**Linhas:** 84-792
**Propósito:** Coletar dados de canais e vídeos do YouTube

### Inicialização (__init__)

**Linhas:** 85-142

```python
def __init__(self):
    # 1. Carregar 20 API keys do ambiente
    self.api_keys = [
        os.environ.get("YOUTUBE_API_KEY_3"),
        os.environ.get("YOUTUBE_API_KEY_4"),
        # ... KEY_5 a KEY_10 ...
        os.environ.get("YOUTUBE_API_KEY_21"),
        # ... KEY_22 a KEY_32 ...
    ]

    # 2. Filtrar keys None (não configuradas)
    self.api_keys = [key for key in self.api_keys if key]

    if not self.api_keys:
        raise ValueError("At least one YouTube API key is required")

    # 3. Criar um RateLimiter para cada chave
    self.rate_limiters = {i: RateLimiter() for i in range(len(self.api_keys))}

    # 4. Índice da chave atual (rotaciona)
    self.current_key_index = 0

    # 5. Rastrear chaves esgotadas (por dia UTC)
    self.exhausted_keys_date: Dict[int, datetime.date] = {}

    # 6. Rastrear chaves suspensas (reseta no restart)
    self.suspended_keys: Set[int] = set()

    # 7. Contadores de quota (agora corretos!)
    self.total_quota_units = 0
    self.quota_units_per_key = {i: 0 for i in range(len(self.api_keys))}
    self.quota_units_per_canal: Dict[str, int] = {}

    # 8. Cache de channel_id (otimização)
    self.channel_id_cache: Dict[str, str] = {}

    logger.info(f"🚀 YouTube collector initialized with {len(self.api_keys)} API keys")
    logger.info(f"📊 Total quota disponível: {len(self.api_keys) * 10000:,} units/dia")
```

### Atributos Principais

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `api_keys` | List[str] | 20 chaves do YouTube (KEY_3-10 + KEY_21-32) |
| `rate_limiters` | Dict[int, RateLimiter] | Um rate limiter por chave |
| `current_key_index` | int | Índice da chave atual (0-19) |
| `exhausted_keys_date` | Dict[int, date] | Chaves esgotadas + data |
| `suspended_keys` | Set[int] | Chaves com 403 genérico |
| `total_quota_units` | int | Total de units gastos |
| `channel_id_cache` | Dict[str, str] | Cache de URLs resolvidas |
| `failed_canals` | Set[str] | Canais que falharam na coleta |

---

## Sistema de API Keys

### Configuração (Railway)

```bash
# No Railway, configurar 20 variáveis de ambiente:
YOUTUBE_API_KEY_3=AIzaSy...
YOUTUBE_API_KEY_4=AIzaSy...
YOUTUBE_API_KEY_5=AIzaSy...
# ... até ...
YOUTUBE_API_KEY_32=AIzaSy...
```

### Por que KEY_3 a KEY_32?

**Histórico:**
- KEY_1 e KEY_2 foram usadas inicialmente
- Depois expandimos para KEY_3 a KEY_10 (8 chaves)
- Depois adicionamos KEY_21 a KEY_32 (12 chaves)
- **Total: 20 chaves**

### Estados das Chaves

#### 1. Disponível (Normal)
- Pode fazer requisições
- Não está em `exhausted_keys_date` nem `suspended_keys`

#### 2. Esgotada (Quota Exceeded)
- Atingiu 10,000 units no dia UTC
- Registrada em `exhausted_keys_date` com data
- **Reset:** Meia-noite UTC automática

```python
def mark_key_as_exhausted(self):
    """Marca chave atual como esgotada ATÉ MEIA-NOITE UTC"""
    today_utc = datetime.now(timezone.utc).date()
    self.exhausted_keys_date[self.current_key_index] = today_utc

    logger.error(f"🚨 QUOTA EXCEEDED - Key {self.current_key_index + 2} EXHAUSTED")
    logger.error(f"🔑 Chaves restantes: {len(self.api_keys) - len(self.exhausted_keys_date)}")

    self.rotate_to_next_key()
```

#### 3. Suspensa (403 Genérico)
- Recebeu 403 sem ser quota/ratelimit
- Registrada em `suspended_keys`
- **Reset:** Apenas com restart do servidor ou endpoint `/api/reset-suspended-keys`

```python
def mark_key_as_suspended(self):
    """Marca chave atual como SUSPENSA (reseta no restart)"""
    self.suspended_keys.add(self.current_key_index)

    logger.error(f"❌ KEY SUSPENDED - Key {self.current_key_index + 2}")
    logger.error(f"🔑 Chaves restantes: {len(self.api_keys) - len(self.exhausted_keys_date) - len(self.suspended_keys)}")

    self.rotate_to_next_key()
```

### Rotação de Chaves

**Linhas:** 240-267

```python
def get_current_api_key(self) -> Optional[str]:
    """Get current API key - PULA chaves esgotadas E SUSPENSAS"""
    if self.all_keys_exhausted():
        return None

    attempts = 0
    while (self.current_key_index in self.exhausted_keys_date or
           self.current_key_index in self.suspended_keys) and
           attempts < len(self.api_keys):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        attempts += 1

    if attempts >= len(self.api_keys):
        return None

    return self.api_keys[self.current_key_index]

def rotate_to_next_key(self):
    """Rotaciona para próxima chave disponível"""
    old_index = self.current_key_index
    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)

    # Pular chaves indisponíveis
    attempts = 0
    while (self.current_key_index in self.exhausted_keys_date or
           self.current_key_index in self.suspended_keys) and
           attempts < len(self.api_keys):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        attempts += 1

    if old_index != self.current_key_index:
        stats = self.rate_limiters[self.current_key_index].get_stats()
        logger.info(f"🔄 Rotated: Key {old_index + 2} → Key {self.current_key_index + 2}")
```

---

## Quota Management

### Cálculo de Custo

**Linhas:** 199-213

```python
def get_request_cost(self, url: str) -> int:
    """
    Calcula o custo REAL em units de cada requisição
    - search.list = 100 units (CARA!)
    - channels.list = 1 unit
    - videos.list = 1 unit
    """
    if "/search" in url:
        return 100  # Search é MUITO caro!
    elif "/channels" in url:
        return 1
    elif "/videos" in url:
        return 1
    else:
        return 1
```

### Incrementar Contador

**Linhas:** 215-225

```python
def increment_quota_counter(self, canal_name: str, cost: int):
    """Incrementa contador de QUOTA UNITS (correto!)"""
    # Total geral
    self.total_quota_units += cost

    # Por chave
    self.quota_units_per_key[self.current_key_index] += cost

    # Por canal
    if canal_name not in self.quota_units_per_canal:
        self.quota_units_per_canal[canal_name] = 0
    self.quota_units_per_canal[canal_name] += cost
```

### Estatísticas

**Linhas:** 227-238

```python
def get_request_stats(self) -> Dict[str, Any]:
    """Get request statistics"""
    return {
        "total_quota_units": self.total_quota_units,
        "quota_units_per_key": self.quota_units_per_key.copy(),
        "quota_units_per_canal": self.quota_units_per_canal.copy(),
        "failed_canals": list(self.failed_canals),
        "exhausted_keys": len(self.exhausted_keys_date),
        "suspended_keys": len(self.suspended_keys),
        "active_keys": len(self.api_keys) - len(self.exhausted_keys_date) - len(self.suspended_keys),
        "total_available_quota": (len(self.api_keys) - len(self.exhausted_keys_date) - len(self.suspended_keys)) * 10000
    }
```

### Reset para Nova Coleta

**Linhas:** 144-197

```python
def reset_for_new_collection(self):
    """
    Reset collector state - LIMPA CHAVES SE JÁ MUDOU DE DIA UTC

    Chamado antes de cada coleta manual (POST /api/collect-data)
    """
    # 1. Limpar contadores
    self.failed_canals = set()
    self.total_quota_units = 0
    self.quota_units_per_key = {i: 0 for i in range(len(self.api_keys))}
    self.quota_units_per_canal = {}

    # 2. NÃO limpar channel_id_cache (otimização!)
    # Cache persiste até restart do servidor

    # 3. Resetar chaves suspensas (podem ter voltado)
    if self.suspended_keys:
        logger.info(f"🔄 RESETANDO {len(self.suspended_keys)} CHAVES SUSPENSAS")
        self.suspended_keys = set()

    # 4. Limpar chaves esgotadas se já é outro dia UTC
    today_utc = datetime.now(timezone.utc).date()

    keys_to_reset = []
    for key_index, exhausted_date in list(self.exhausted_keys_date.items()):
        if exhausted_date < today_utc:
            keys_to_reset.append(key_index)

    if keys_to_reset:
        logger.info(f"🔄 RESETANDO {len(keys_to_reset)} CHAVES (novo dia UTC)")
        for key_index in keys_to_reset:
            del self.exhausted_keys_date[key_index]
            logger.info(f"✅ Key {key_index + 2} disponível novamente")

    # 5. Log status
    logger.info("=" * 80)
    logger.info("🔄 COLLECTOR RESET")
    logger.info(f"📅 Dia UTC atual: {today_utc}")
    logger.info(f"🔑 Chaves disponíveis: {len(self.api_keys) - len(self.exhausted_keys_date) - len(self.suspended_keys)}/{len(self.api_keys)}")
    logger.info(f"💰 Quota total disponível: {(len(self.api_keys) - len(self.exhausted_keys_date) - len(self.suspended_keys)) * 10000:,} units")
    logger.info("=" * 80)
```

---

## Métodos de Coleta

### 1. make_api_request() - Requisição Base

**Linhas:** 310-398
**Propósito:** Fazer requisições à API do YouTube com retry automático

```python
async def make_api_request(
    self,
    url: str,
    params: dict,
    canal_name: str = "system",
    retry_count: int = 0
) -> Optional[dict]:
    """
    Função para fazer requisições à API do YouTube

    Fluxo:
    1. Verificar se todas as chaves estão esgotadas
    2. Obter chave atual
    3. Aguardar rate limit se necessário
    4. Calcular custo e incrementar contador
    5. Fazer requisição HTTP
    6. Tratar erros (403, timeouts, etc)
    """
    # 1. Check se todas chaves esgotadas
    if self.all_keys_exhausted():
        logger.error("❌ All keys exhausted or suspended!")
        return None

    # 2. Obter chave atual
    current_key = self.get_current_api_key()
    if not current_key:
        return None

    params['key'] = current_key

    # 3. Rate limit wait
    await self.rate_limiters[self.current_key_index].wait_if_needed()

    try:
        async with aiohttp.ClientSession() as session:
            # 4. Calcular custo e incrementar
            request_cost = self.get_request_cost(url)
            self.increment_quota_counter(canal_name, request_cost)
            self.rate_limiters[self.current_key_index].record_request()

            # 5. Fazer requisição
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:

                # 200 OK
                if response.status == 200:
                    data = await response.json()
                    return data

                # 403 Forbidden
                elif response.status == 403:
                    error_data = await response.json()
                    error_obj = error_data.get('error', {})
                    error_msg = error_obj.get('message', '').lower()
                    error_reason = ''
                    if error_obj.get('errors'):
                        error_reason = error_obj['errors'][0].get('reason', '').lower()

                    logger.warning(f"⚠️ 403 Error - Message: '{error_msg}' | Reason: '{error_reason}'")

                    # CASO 1: Quota Excedida
                    if 'quota' in error_msg or 'quota' in error_reason or 'dailylimit' in error_reason:
                        logger.error(f"🚨 QUOTA EXCEEDED on key {self.current_key_index + 2}")
                        self.mark_key_as_exhausted()

                        # Retry com próxima chave
                        if retry_count < self.max_retries and not self.all_keys_exhausted():
                            logger.info(f"♻️ Tentando com próxima chave disponível...")
                            return await self.make_api_request(url, params, canal_name, retry_count + 1)
                        return None

                    # CASO 2: Rate Limit
                    elif 'ratelimit' in error_msg or 'ratelimit' in error_reason:
                        if retry_count < self.max_retries:
                            wait_time = (2 ** retry_count) * 30  # Exponential backoff
                            logger.warning(f"⏱️ RATE LIMIT hit on key {self.current_key_index + 2}")
                            logger.info(f"♻️ Retry {retry_count + 1}/{self.max_retries} após {wait_time}s")
                            await asyncio.sleep(wait_time)
                            return await self.make_api_request(url, params, canal_name, retry_count + 1)
                        else:
                            logger.error(f"❌ Max retries atingido após rate limit")
                            return None

                    # CASO 3: Key Suspensa (403 genérico)
                    else:
                        logger.error(f"❌ KEY SUSPENDED (403 genérico) on key {self.current_key_index + 2}: {error_msg}")
                        self.mark_key_as_suspended()

                        # Retry com próxima chave
                        if retry_count < self.max_retries and not self.all_keys_exhausted():
                            logger.info(f"♻️ Tentando com próxima chave disponível...")
                            return await self.make_api_request(url, params, canal_name, retry_count + 1)
                        else:
                            logger.error(f"❌ Todas as chaves esgotadas ou suspensas")
                            return None

                else:
                    logger.warning(f"⚠️ HTTP {response.status}: {await response.text()}")
                    return None

    except asyncio.TimeoutError:
        logger.warning(f"⏱️ Timeout na requisição")
        if retry_count < self.max_retries:
            await asyncio.sleep(5)
            return await self.make_api_request(url, params, canal_name, retry_count + 1)
        return None

    except Exception as e:
        logger.error(f"❌ Exception na requisição: {e}")
        return None
```

### 2. get_channel_id() - Resolver URL para ID

**Linhas:** 476-509
**Propósito:** Converter URL do YouTube para channel_id (UC...)

```python
async def get_channel_id(self, url: str, canal_name: str) -> Optional[str]:
    """
    Get channel ID from URL

    Otimização: Usa cache para evitar requisições duplicadas

    Tipos de URL suportados:
    - youtube.com/channel/UC... (direto)
    - youtube.com/@handle (requer busca)
    - youtube.com/c/username (requer busca)
    - youtube.com/user/username (requer busca)
    """
    # 1. Verificar cache primeiro (0 requisições!)
    if url in self.channel_id_cache:
        logger.debug(f"⚡ {canal_name}: Cache hit para channel_id")
        return self.channel_id_cache[url]

    # 2. Extrair identificador da URL
    identifier, id_type = self.extract_channel_identifier(url)

    if not identifier:
        logger.error(f"❌ {canal_name}: Não foi possível extrair identificador da URL: {url}")
        return None

    channel_id = None

    # 3. Se já é um channel_id válido (UC...)
    if id_type == 'id' and self.is_valid_channel_id(identifier):
        channel_id = identifier

    # 4. Se é handle ou username, precisa buscar na API
    elif id_type in ['handle', 'username']:
        channel_id = await self.get_channel_id_from_handle(identifier, canal_name)

    # 5. Adicionar ao cache se resolveu com sucesso
    if channel_id:
        self.channel_id_cache[url] = channel_id
        logger.debug(f"💾 {canal_name}: Channel ID cacheado: {channel_id}")

    return channel_id
```

**Método auxiliar:** `extract_channel_identifier()`

**Linhas:** 411-443

```python
def extract_channel_identifier(self, url: str) -> tuple[Optional[str], str]:
    """
    Extract channel identifier from YouTube URL

    Suporta CARACTERES UNICODE (árabe, coreano, etc)

    Returns: (identifier, type)
    - ('UC...', 'id') - Channel ID direto
    - ('handle', 'handle') - @handle
    - ('username', 'username') - /c/ ou /user/
    """
    url = self.clean_youtube_url(url)

    # 1. Channel ID direto (mais confiável)
    channel_id_match = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', url)
    if channel_id_match:
        channel_id = channel_id_match.group(1)
        if self.is_valid_channel_id(channel_id):
            return (channel_id, 'id')

    # 2. Handle (@...) - ACEITA QUALQUER CARACTERE
    handle_match = re.search(r'youtube\.com/@([^/?&#]+)', url)
    if handle_match:
        handle = handle_match.group(1)
        # Decodifica URL encoding (%C4%B1 etc)
        handle = urllib.parse.unquote(handle)
        logger.debug(f"Handle extraído: {handle}")
        return (handle, 'handle')

    # 3. Custom URL (/c/)
    custom_match = re.search(r'youtube\.com/c/([a-zA-Z0-9._-]+)', url)
    if custom_match:
        username = custom_match.group(1)
        return (username, 'username')

    # 4. Old style (/user/)
    user_match = re.search(r'youtube\.com/user/([a-zA-Z0-9._-]+)', url)
    if user_match:
        username = user_match.group(1)
        return (username, 'username')

    return (None, 'unknown')
```

### 3. get_channel_info() - Dados do Canal

**Linhas:** 511-534
**Custo:** 1 unit

```python
async def get_channel_info(self, channel_id: str, canal_name: str) -> Optional[Dict[str, Any]]:
    """Get channel info (subscribers, video count, views)"""
    if not self.is_valid_channel_id(channel_id):
        return None

    url = f"{self.base_url}/channels"
    params = {
        'part': 'statistics,snippet',
        'id': channel_id
    }

    data = await self.make_api_request(url, params, canal_name)

    if data and data.get('items'):
        channel = data['items'][0]
        stats = channel.get('statistics', {})
        snippet = channel.get('snippet', {})

        return {
            'channel_id': channel_id,
            'title': snippet.get('title'),
            'subscriber_count': int(stats.get('subscriberCount', 0)),
            'video_count': int(stats.get('videoCount', 0)),
            'view_count': int(stats.get('viewCount', 0))
        }

    return None
```

### 4. get_channel_videos() - Lista de Vídeos

**Linhas:** 536-605
**Custo:** ~100-200 units (search.list é cara!)

```python
async def get_channel_videos(
    self,
    channel_id: str,
    canal_name: str,
    days: int = 30
) -> List[Dict[str, Any]]:
    """
    Get channel videos - AGORA BUSCA APENAS 30 DIAS (em vez de 60)
    Isso economiza ~40-50% de quota!

    Retorna lista de vídeos com:
    - video_id
    - titulo (HTML decoded)
    - url_video
    - data_publicacao
    - views_atuais, likes, comentarios
    - duracao (segundos)
    """
    if not self.is_valid_channel_id(channel_id):
        logger.warning(f"❌ {canal_name}: Invalid channel ID")
        return []

    if self.all_keys_exhausted():
        logger.warning(f"❌ {canal_name}: All keys exhausted")
        return []

    videos = []
    page_token = None
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    logger.info(f"🔍 {canal_name}: Buscando vídeos desde {cutoff_date.date()} (últimos {days} dias)")

    # Loop de paginação
    while True:
        if self.all_keys_exhausted():
            logger.warning(f"⚠️ {canal_name}: Keys exhausted during video fetch")
            break

        # Search API (100 units!)
        url = f"{self.base_url}/search"
        params = {
            'part': 'id,snippet',
            'channelId': channel_id,
            'type': 'video',
            'order': 'date',
            'maxResults': 50,
            'publishedAfter': cutoff_date.isoformat()
        }

        if page_token:
            params['pageToken'] = page_token

        data = await self.make_api_request(url, params, canal_name)

        if not data:
            logger.warning(f"⚠️ {canal_name}: API request returned None")
            break

        if not data.get('items'):
            logger.info(f"ℹ️ {canal_name}: No more videos found")
            break

        # Buscar detalhes dos vídeos (1 unit por batch de 50)
        video_ids = [item['id']['videoId'] for item in data['items']]
        video_details = await self.get_video_details(video_ids, canal_name)

        # Combinar search results + details
        for item, details in zip(data['items'], video_details):
            if details:
                video_info = {
                    'video_id': item['id']['videoId'],
                    'titulo': decode_html_entities(item['snippet']['title']),  # Decodifica &#39; etc
                    'url_video': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'data_publicacao': item['snippet']['publishedAt'],
                    'views_atuais': details.get('view_count', 0),
                    'likes': details.get('like_count', 0),
                    'comentarios': details.get('comment_count', 0),
                    'duracao': details.get('duration_seconds', 0)
                }
                videos.append(video_info)

        # Próxima página
        page_token = data.get('nextPageToken')
        if not page_token:
            break

    logger.info(f"✅ {canal_name}: Encontrados {len(videos)} vídeos nos últimos {days} dias")
    return videos
```

### 5. get_video_details() - Detalhes dos Vídeos

**Linhas:** 607-647
**Custo:** 1 unit por batch (até 50 vídeos)

```python
async def get_video_details(
    self,
    video_ids: List[str],
    canal_name: str
) -> List[Optional[Dict[str, Any]]]:
    """
    Get video details (views, likes, comments, duration)

    Processa em batches de 50 (limite da API)
    """
    if self.all_keys_exhausted():
        return [None] * len(video_ids)

    if not video_ids:
        return []

    details = []

    # Processar em batches de 50
    for i in range(0, len(video_ids), 50):
        if self.all_keys_exhausted():
            details.extend([None] * (len(video_ids) - i))
            break

        batch_ids = video_ids[i:i+50]

        url = f"{self.base_url}/videos"
        params = {
            'part': 'statistics,contentDetails',
            'id': ','.join(batch_ids)
        }

        data = await self.make_api_request(url, params, canal_name)

        if data and data.get('items'):
            for item in data['items']:
                stats = item.get('statistics', {})
                content = item.get('contentDetails', {})

                video_detail = {
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'comment_count': int(stats.get('commentCount', 0)),
                    'duration_seconds': self.parse_duration(content.get('duration', 'PT0S'))
                }
                details.append(video_detail)
        else:
            details.extend([None] * len(batch_ids))

    return details
```

### 6. get_canal_data() - Coleta Completa

**Linhas:** 708-769
**Propósito:** Método principal - coleta TUDO de um canal

```python
async def get_canal_data(self, url_canal: str, canal_name: str) -> Optional[Dict[str, Any]]:
    """
    Get complete canal data

    Retorna:
    {
        'inscritos': int,
        'videos_publicados_7d': int,
        'engagement_rate': float,
        'views_30d': int,
        'views_15d': int,
        'views_7d': int
    }
    """
    try:
        # 1. Verificar se canal já falhou antes
        if self.is_canal_failed(url_canal):
            logger.warning(f"⏭️ Skipping {canal_name} - already failed")
            return None

        # 2. Verificar se todas chaves esgotadas
        if self.all_keys_exhausted():
            logger.error(f"❌ {canal_name}: All keys exhausted")
            return None

        logger.info(f"🎬 Iniciando coleta: {canal_name}")

        # 3. Rotacionar para próxima chave (distribuir carga)
        self.rotate_to_next_key()

        # 4. Obter channel_id (cache ou API)
        channel_id = await self.get_channel_id(url_canal, canal_name)
        if not channel_id:
            logger.error(f"❌ {canal_name}: Não foi possível obter channel_id")
            self.mark_canal_as_failed(url_canal)
            return None

        logger.info(f"✅ {canal_name}: Channel ID = {channel_id}")

        # 5. Obter info do canal
        channel_info = await self.get_channel_info(channel_id, canal_name)
        if not channel_info:
            logger.error(f"❌ {canal_name}: Não foi possível obter info do canal")
            self.mark_canal_as_failed(url_canal)
            return None

        logger.info(f"✅ {canal_name}: {channel_info['subscriber_count']:,} inscritos")

        # 6. Obter vídeos (últimos 30 dias)
        videos = await self.get_channel_videos(channel_id, canal_name, days=30)

        if not videos:
            logger.warning(f"⚠️ {canal_name}: NENHUM vídeo encontrado nos últimos 30 dias!")

        # 7. Calcular métricas
        current_date = datetime.now(timezone.utc)
        views_by_period = self.calculate_views_by_period(videos, current_date)

        videos_7d = sum(
            1 for v in videos
            if (current_date - datetime.fromisoformat(v['data_publicacao'].replace('Z', '+00:00'))).total_seconds() / 86400 <= 7
        )

        total_engagement = sum(v['likes'] + v['comentarios'] for v in videos)
        total_views = sum(v['views_atuais'] for v in videos)
        engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0

        # 8. Montar resultado
        result = {
            'inscritos': channel_info['subscriber_count'],
            'videos_publicados_7d': videos_7d,
            'engagement_rate': round(engagement_rate, 2),
            **views_by_period  # views_30d, views_15d, views_7d
        }

        logger.info(f"✅ {canal_name}: Coleta concluída - 7d={views_by_period['views_7d']:,} views")

        return result

    except Exception as e:
        logger.error(f"❌ Error for {canal_name}: {e}")
        self.mark_canal_as_failed(url_canal)
        return None
```

---

## Error Handling & Retry

### Tipos de Erro

#### 1. 403 Quota Exceeded
```python
# Detectado por:
if 'quota' in error_msg or 'dailylimit' in error_reason:
    # Ação:
    self.mark_key_as_exhausted()
    # Retry com próxima chave
```

#### 2. 403 Rate Limit
```python
# Detectado por:
if 'ratelimit' in error_msg or 'usageratelimit' in error_reason:
    # Ação:
    wait_time = (2 ** retry_count) * 30  # Exponential backoff
    await asyncio.sleep(wait_time)
    # Retry com mesma chave
```

#### 3. 403 Genérico (Key Suspended)
```python
# Qualquer outro 403:
else:
    # Ação:
    self.mark_key_as_suspended()
    # Retry com próxima chave
```

#### 4. Timeout
```python
except asyncio.TimeoutError:
    # Aguardar 5s e retry
    await asyncio.sleep(5)
    return await self.make_api_request(url, params, canal_name, retry_count + 1)
```

### Retry Logic

```python
# Configuração
self.max_retries = 3
self.base_delay = 0.8  # Não usado mais (RateLimiter controla)

# Retry automático para:
# - 403 Quota → Retry com próxima chave (até 3x)
# - 403 Rate Limit → Exponential backoff (30s, 60s, 120s)
# - 403 Genérico → Retry com próxima chave (até 3x)
# - Timeout → Retry após 5s (até 3x)
```

---

## Otimizações

### 1. Channel ID Cache

**Linhas:** 484-509

```python
# Cache de channel_id (evita requisições duplicadas)
self.channel_id_cache: Dict[str, str] = {}  # {url_canal: channel_id}

async def get_channel_id(self, url: str, canal_name: str) -> Optional[str]:
    # 1. Verificar cache primeiro (0 requisições!)
    if url in self.channel_id_cache:
        logger.debug(f"⚡ {canal_name}: Cache hit para channel_id")
        return self.channel_id_cache[url]

    # 2. Resolver via API (1-100 units)
    # ...

    # 3. Adicionar ao cache se resolveu
    if channel_id:
        self.channel_id_cache[url] = channel_id
        logger.debug(f"💾 {canal_name}: Channel ID cacheado: {channel_id}")
```

**Benefício:**
- Cache persiste até restart do servidor
- Economiza 1-100 units por canal em coletas subsequentes
- Especialmente útil para @handles (que custam 100 units)

### 2. Busca de 30 Dias (não 60)

**Linhas:** 536-605

```python
# Antes: days=60 (default)
# Agora: days=30 (padrão)
videos = await self.get_channel_videos(channel_id, canal_name, days=30)

# Economia:
# - Menos páginas de search.list (100 units cada)
# - ~40-50% menos quota por canal
```

### 3. RateLimiter Inteligente

**Linhas:** 23-82

```python
# Em vez de delay fixo (0.8s), usa janela deslizante:
# - Máximo 90 req/100s por chave
# - Aguarda automaticamente quando necessário
# - Utilização máxima sem estourar limite
```

### 4. Rotação de Chaves

**Linhas:** 720-721

```python
# Antes de cada canal, rotacionar chave
self.rotate_to_next_key()

# Benefício: Distribuir carga entre todas as chaves
```

---

## Integração com main.py

### Inicialização

**main.py, linhas 75-76:**
```python
from collector import YouTubeCollector

collector = YouTubeCollector()
```

### Chamada durante Coleta

**main.py, linhas ~200-300 (run_collection_job):**

```python
async def run_collection_job():
    global collection_in_progress, last_collection_time

    try:
        # 1. Criar registro de coleta
        coleta_id = await db.create_coleta_record()

        # 2. RESET do collector
        collector.reset_for_new_collection()

        # 3. Buscar canais ativos
        canais = await db.get_active_canais()
        logger.info(f"🎬 INICIANDO COLETA: {len(canais)} canais")

        # 4. Coletar dados de cada canal
        for idx, canal in enumerate(canais, 1):
            canal_name = canal['nome_canal']
            url_canal = canal['url_canal']

            logger.info(f"📊 [{idx}/{len(canais)}] Coletando: {canal_name}")

            # USAR O COLLECTOR
            canal_data = await collector.get_canal_data(url_canal, canal_name)

            if canal_data:
                # Salvar no banco
                await db.save_canal_stats(canal['id'], canal_data)
                logger.info(f"✅ {canal_name}: Dados salvos")
            else:
                logger.error(f"❌ {canal_name}: Falha na coleta")

        # 5. Coletar vídeos
        for canal in canais:
            videos = await collector.get_videos_data(canal['url_canal'], canal['nome_canal'])
            if videos:
                await db.save_videos(canal['id'], videos)

        # 6. Finalizar coleta
        stats = collector.get_request_stats()
        await db.complete_coleta_record(
            coleta_id,
            canais_sucesso=len(canais) - len(collector.failed_canals),
            canais_falha=len(collector.failed_canals),
            quota_usada=stats['total_quota_units']
        )

        logger.info("✅ COLETA FINALIZADA COM SUCESSO")

    except Exception as e:
        logger.error(f"❌ ERRO NA COLETA: {e}")
        raise
```

### Endpoints Relacionados

#### POST /api/collect-data
```python
@app.post("/api/collect-data")
async def collect_data(background_tasks: BackgroundTasks):
    can_collect, message = await can_start_collection()

    if not can_collect:
        return {"message": message, "status": "blocked"}

    background_tasks.add_task(run_collection_job)
    return {"message": "Collection started", "status": "processing"}
```

#### GET /api/coletas/historico
```python
@app.get("/api/coletas/historico")
async def get_coletas_historico(limit: Optional[int] = 20):
    historico = await db.get_coletas_historico(limit=limit)

    # Quota info do collector
    quota_usada = await db.get_quota_diaria_usada()
    quota_total = len(collector.api_keys) * 10000

    return {
        "historico": historico,
        "quota_info": {
            "total_diario": quota_total,
            "usado_hoje": quota_usada,
            "disponivel": quota_total - quota_usada,
            "total_chaves": len(collector.api_keys),
            "chaves_ativas": len(collector.api_keys) - len(collector.exhausted_keys_date) - len(collector.suspended_keys),
            "chaves_esgotadas": list(collector.exhausted_keys_date.keys()),
            "chaves_suspensas": list(collector.suspended_keys)
        }
    }
```

#### POST /api/reset-suspended-keys
```python
@app.post("/api/reset-suspended-keys")
async def reset_suspended_keys():
    """Endpoint para resetar chaves suspensas (testar novamente após contestação)"""
    count = collector.reset_suspended_keys()
    return {
        "message": f"{count} chave(s) suspensa(s) resetada(s) com sucesso",
        "keys_reset": count,
        "status": "success"
    }
```

---

## Troubleshooting

### Problema 1: Todas as chaves esgotadas

**Sintoma:**
```
❌ All keys exhausted or suspended!
🔑 Chaves restantes: 0/20
```

**Causas:**
1. Quota diária excedida (200,000 units gastos)
2. Muitos search.list (100 units cada)
3. Muitos canais coletados no mesmo dia

**Solução:**
```bash
# 1. Aguardar meia-noite UTC (reset automático)
# 2. Reduzir número de canais
# 3. Verificar se há loops infinitos

# Ver quando reseta:
GET /api/coletas/historico
# Response: quota_info.proximo_reset_utc
```

### Problema 2: Chaves suspensas (403 genérico)

**Sintoma:**
```
❌ KEY SUSPENDED (403 genérico) on key 3
🔑 Chaves restantes: 15/20
```

**Causas:**
1. YouTube detectou comportamento suspeito
2. Chave comprometida
3. Quota excedida mas API retornou erro genérico

**Solução:**
```bash
# 1. Resetar chaves suspensas (tentativa)
POST /api/reset-suspended-keys

# 2. Se não funcionar, aguardar 24h
# 3. Se persistir, contestar no Google Cloud Console

# 4. Verificar status:
GET /api/coletas/historico
# quota_info.chaves_suspensas: [3, 5, 7]
```

### Problema 3: Rate limit constante

**Sintoma:**
```
⏱️ RATE LIMIT hit on key 5
♻️ Retry 1/3 após 30s
```

**Causas:**
1. RateLimiter não está funcionando
2. Outra aplicação usando mesma chave
3. Bug no código (loops)

**Solução:**
```python
# 1. Verificar se rate_limiter.wait_if_needed() está sendo chamado
# 2. Aumentar margem de segurança:
# collector.py, linha 28:
self.max_requests = 80  # Em vez de 90

# 3. Verificar se há múltiplas instâncias rodando
```

### Problema 4: Channel ID não encontrado

**Sintoma:**
```
❌ Canal @حكايات_مظلمة: Não foi possível obter channel_id
```

**Causas:**
1. Handle com caracteres especiais (árabe, coreano)
2. URL mal formada
3. Canal deletado/privado

**Solução:**
```python
# 1. Verificar URL no browser
# 2. Tentar diferentes formatos:
# - youtube.com/@handle
# - youtube.com/channel/UC...
# - youtube.com/c/username

# 3. Ver logs:
# collector.py, linha 428:
logger.debug(f"Handle extraído: {handle}")

# 4. Testar manualmente:
from collector import YouTubeCollector
collector = YouTubeCollector()
await collector.get_channel_id("URL_AQUI", "TEST")
```

### Problema 5: Coleta muito lenta

**Sintoma:**
- Coleta de 80 canais leva > 30 minutos

**Causas:**
1. RateLimiter aguardando muito
2. Muitos canais com @handles (100 units cada)
3. Muitos vídeos por canal

**Solução:**
```python
# 1. Verificar cache hit rate:
# Se baixo, é porque muitos canais novos
# Cache só ajuda em coletas repetidas

# 2. Reduzir days:
# collector.py, linha 741:
videos = await self.get_channel_videos(channel_id, canal_name, days=15)  # Em vez de 30

# 3. Aumentar max_requests:
# collector.py, linha 28:
self.max_requests = 95  # Mais arriscado, mas mais rápido

# 4. Usar channel IDs diretos (em vez de @handles)
# youtube.com/channel/UC... (1 unit)
# vs
# youtube.com/@handle (100 units)
```

### Problema 6: HTML entities no título

**Sintoma:**
```
Título: "I&#39;m a video"
```

**Causa:**
- API retorna HTML entities encoded

**Solução:**
```python
# Já implementado! (linha 16-20)
def decode_html_entities(text: str) -> str:
    """Decodifica HTML entities em texto (ex: &#39; -> ')"""
    if not text:
        return text
    return html.unescape(text)

# Uso (linha 590):
'titulo': decode_html_entities(item['snippet']['title'])
```

### Problema 7: Timeout constante

**Sintoma:**
```
⏱️ Timeout na requisição
♻️ Retry 1/3...
```

**Causas:**
1. Problema de rede
2. API do YouTube lenta
3. Timeout muito curto

**Solução:**
```python
# 1. Aumentar timeout:
# collector.py, linha 335:
async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=60)):  # 60s

# 2. Verificar conexão:
curl https://www.googleapis.com/youtube/v3/channels?part=id&id=UCuPMXZ05uQnIuj5bhAk_BPQ&key=YOUR_KEY

# 3. Usar proxy se necessário (não implementado ainda)
```

---

## Exemplo de Uso Completo

### Script de Teste

```python
# test_collector.py
import asyncio
import logging
from collector import YouTubeCollector

logging.basicConfig(level=logging.INFO)

async def test_collector():
    # 1. Inicializar collector
    collector = YouTubeCollector()

    # 2. Reset (simular início de coleta)
    collector.reset_for_new_collection()

    # 3. Testar coleta de 1 canal
    canal_data = await collector.get_canal_data(
        url_canal="https://www.youtube.com/@MrBeast",
        canal_name="MrBeast"
    )

    if canal_data:
        print("✅ Coleta bem-sucedida!")
        print(f"Inscritos: {canal_data['inscritos']:,}")
        print(f"Views 7d: {canal_data['views_7d']:,}")
        print(f"Videos 7d: {canal_data['videos_publicados_7d']}")
        print(f"Engagement: {canal_data['engagement_rate']:.2f}%")
    else:
        print("❌ Coleta falhou")

    # 4. Ver estatísticas
    stats = collector.get_request_stats()
    print(f"\n📊 Quota usada: {stats['total_quota_units']} units")
    print(f"🔑 Chaves ativas: {stats['active_keys']}/{len(collector.api_keys)}")

if __name__ == "__main__":
    asyncio.run(test_collector())
```

### Rodar

```bash
# Local (precisa de pelo menos 1 API key)
python test_collector.py

# Railway (deploy)
git add collector.py
git commit -m "Update collector"
git push origin main
```

---

## Métricas de Performance

### Coleta Típica (80 canais)

```
🎬 INICIANDO COLETA: 80 canais
📊 Quota inicial disponível: 200,000 units
⏱️ Tempo estimado: 15-25 minutos

Breakdown por canal:
- get_channel_id (cached): 0 units
- get_channel_id (novo): 1-100 units
- get_channel_info: 1 unit
- get_channel_videos (30d): ~100-150 units
- get_video_details: 1-2 units

Total médio: 150-250 units/canal

80 canais × 200 units = 16,000 units (8% da quota)

✅ COLETA FINALIZADA
📊 Quota usada: 16,234 units
🔑 Chaves ativas: 20/20
⏱️ Duração: 18 minutos
```

---

## Referências

**Arquivos relacionados:**
- `D:\ContentFactory\youtube-dashboard-backend\main.py` - Integração com endpoints
- `D:\ContentFactory\youtube-dashboard-backend\database.py` - Salvar dados coletados
- `D:\ContentFactory\youtube-dashboard-backend\notifier.py` - Processar vídeos coletados

**Documentação YouTube API:**
- [Quota Limits](https://developers.google.com/youtube/v3/getting-started#quota)
- [Search.list](https://developers.google.com/youtube/v3/docs/search/list) - 100 units
- [Channels.list](https://developers.google.com/youtube/v3/docs/channels/list) - 1 unit
- [Videos.list](https://developers.google.com/youtube/v3/docs/videos/list) - 1 unit

**Ver também:**
- `05_DATABASE_SCHEMA.md` - Estrutura do banco (canais_monitorados, videos_historico)
- `07_NOTIFICACOES_INTELIGENTES.md` - O que acontece após coleta
- `08_API_ENDPOINTS_COMPLETA.md` - Todos os endpoints do sistema

---

**Última atualização:** 12/01/2026
**Versão collector.py:** 792 linhas (20 API keys)
