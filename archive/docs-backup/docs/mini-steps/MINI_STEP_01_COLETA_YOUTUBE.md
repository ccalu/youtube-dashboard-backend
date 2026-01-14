# MINI-STEP 01: YouTube Data Collection System

## 🎯 What This Function Does

The YouTube collector is the **heart of the data mining operation**. It collects data from 263 YouTube channels automatically, extracting:
- Channel statistics (subscribers, views, video count)
- Recent videos (last 30 days)
- Video details (views, likes, comments, duration)
- Historical evolution data

**Key Features:**
- **20 API keys rotation** (KEY_3-10, KEY_21-32) for 200k requests/day capacity
- **Rate limiter** (90 requests/100s per key) prevents quota errors
- **Channel ID cache** to avoid duplicate API calls
- **Circuit breaker** suspends bad keys automatically
- **Resilient retry logic** with exponential backoff
- **Daily quota reset** at UTC midnight

This system runs automatically at **5 AM daily** via Railway scheduler and can be manually triggered via `/api/collect` endpoint.

---

## 📍 Location in System

### Backend Files
- **Main File:** `collector.py` (lines 1-792)
- **Database Integration:** `database.py` (lines 40-103 for save methods)
- **API Endpoint:** `main.py` (lines ~500-650 for `/api/collect`)

### Database Tables
- **canais_monitorados** - Channel list (263 channels)
- **dados_canais_historico** - Daily snapshots (channel stats)
- **videos_historico** - Video tracking (30-day window)
- **coletas_historico** - Collection logs (status, duration, errors)

### API Endpoints
- `POST /api/collect` - Manual collection trigger
- `GET /api/collection-status` - Check collection status
- `GET /health` - System health (includes quota info)

---

## 🔄 Complete Flow (Railway → Supabase Integration)

### Flow Diagram
```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Scheduler Triggers (Railway Cron: 5 AM Daily)      │
├─────────────────────────────────────────────────────────────┤
│ Railway → main.py → scheduled_collection()                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Collector Initialization                            │
├─────────────────────────────────────────────────────────────┤
│ collector.py → YouTubeCollector.__init__()                  │
│  - Loads 20 API keys from ENV (Railway)                     │
│  - Initializes rate limiters (one per key)                  │
│  - Resets quota counters                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Fetch Active Channels from Supabase                 │
├─────────────────────────────────────────────────────────────┤
│ database.py → get_canais_for_collection()                   │
│  Query: SELECT * FROM canais_monitorados                    │
│         WHERE status = 'ativo'                               │
│  Result: 263 channels                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Create Collection Log                               │
├─────────────────────────────────────────────────────────────┤
│ database.py → create_coleta_log()                           │
│  INSERT INTO coletas_historico                              │
│  (status='em_progresso', canais_total=263)                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Process Each Channel (Loop)                         │
├─────────────────────────────────────────────────────────────┤
│ FOR EACH canal IN canais:                                   │
│   5.1 → get_channel_id(url_canal)  ← May use cache         │
│   5.2 → get_channel_info(channel_id)  ← API call (1 unit)  │
│   5.3 → get_channel_videos(channel_id, days=30)            │
│         ← search.list (100 units!) + videos.list (1 unit)  │
│   5.4 → calculate_views_by_period(videos)  ← Local calc    │
│   5.5 → database.save_canal_data(canal_id, data)          │
│         ← INSERT/UPDATE dados_canais_historico             │
│   5.6 → database.save_videos_data(canal_id, videos)       │
│         ← INSERT/UPDATE videos_historico                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Handle API Key Rotation                             │
├─────────────────────────────────────────────────────────────┤
│ IF error 403 "quota exceeded":                              │
│   → mark_key_as_exhausted()                                 │
│   → rotate_to_next_key()                                    │
│   → retry request with new key                              │
│                                                              │
│ IF error 403 "rate limit":                                  │
│   → wait exponentially (30s, 60s, 120s)                     │
│   → retry up to 3 times                                     │
│                                                              │
│ IF error 403 (generic):                                     │
│   → mark_key_as_suspended()                                 │
│   → rotate_to_next_key()                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Finalize Collection                                 │
├─────────────────────────────────────────────────────────────┤
│ database.py → update_coleta_log()                           │
│  UPDATE coletas_historico                                   │
│  SET status='completo', canais_sucesso=X, canais_erro=Y    │
│      requisicoes_usadas=Z, duracao_segundos=W              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Trigger Notifications (if enabled)                  │
├─────────────────────────────────────────────────────────────┤
│ notifier.py → check_and_create_notifications()              │
│  (See MINI_STEP_02 for details)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Code Implementation

### 1. YouTubeCollector Class Initialization
**File:** `collector.py` (lines 84-143)

```python
class YouTubeCollector:
    def __init__(self):
        # 🆕 SUPPORT FOR 20 API KEYS (KEY_3 to KEY_10 + KEY_21 to KEY_32)
        self.api_keys = [
            os.environ.get("YOUTUBE_API_KEY_3"),
            os.environ.get("YOUTUBE_API_KEY_4"),
            # ... (lines 88-107)
            os.environ.get("YOUTUBE_API_KEY_32")
        ]

        # Remove None values
        self.api_keys = [key for key in self.api_keys if key]

        if not self.api_keys:
            raise ValueError("At least one YouTube API key is required")

        # Create rate limiter for each key (90 req/100s protection)
        self.rate_limiters = {i: RateLimiter() for i in range(len(self.api_keys))}

        # Current key index for rotation
        self.current_key_index = 0

        # Track exhausted keys (resets at UTC midnight)
        self.exhausted_keys_date: Dict[int, datetime.date] = {}

        # Track suspended keys (resets on server restart)
        self.suspended_keys: Set[int] = set()

        # Quota counters (REAL costs: search=100, channels=1, videos=1)
        self.total_quota_units = 0
        self.quota_units_per_key = {i: 0 for i in range(len(self.api_keys))}

        # Channel ID cache (avoids duplicate API calls)
        self.channel_id_cache: Dict[str, str] = {}

        logger.info(f"🚀 YouTube collector initialized with {len(self.api_keys)} API keys")
        logger.info(f"📊 Total quota disponível: {len(self.api_keys) * 10000:,} units/dia")
```

**What This Does:**
- Loads 20 API keys from Railway environment variables
- Creates a rate limiter for each key (prevents hitting 100 req/100s limit)
- Initializes quota tracking (search=100 units, others=1 unit)
- Sets up key rotation system
- Creates channel ID cache to avoid duplicate requests

---

### 2. Rate Limiter Class
**File:** `collector.py` (lines 23-82)

```python
class RateLimiter:
    """
    Rate Limiter to respect YouTube's 100 req/100s limit
    Maintains history and calculates when next request can be made
    """
    def __init__(self, max_requests: int = 90, time_window: int = 100):
        """
        max_requests: Max allowed (90 for safety margin)
        time_window: Time window in seconds (100s)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()  # Stores request timestamps

    def _clean_old_requests(self):
        """Remove old requests (outside 100s window)"""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.time_window)

        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

    def can_make_request(self) -> bool:
        """Check if can make new request"""
        self._clean_old_requests()
        return len(self.requests) < self.max_requests

    def get_wait_time(self) -> float:
        """Calculate how long to wait before next request"""
        self._clean_old_requests()

        if len(self.requests) < self.max_requests:
            return 0.0

        # Calculate when oldest request expires
        oldest = self.requests[0]
        now = datetime.now(timezone.utc)
        wait = (oldest + timedelta(seconds=self.time_window)) - now
        return max(0.0, wait.total_seconds())

    async def wait_if_needed(self):
        """Automatically wait if necessary before making request"""
        wait_time = self.get_wait_time()
        if wait_time > 0:
            logger.info(f"⏳ Rate limit próximo - aguardando {wait_time:.1f}s")
            await asyncio.sleep(wait_time + 0.5)  # +0.5s safety margin
```

**What This Does:**
- Tracks all API requests in a sliding 100-second window
- Automatically blocks if 90 requests already made
- Calculates precise wait time until next slot available
- Prevents quota errors by staying under limit

---

### 3. API Request with Key Rotation
**File:** `collector.py` (lines 310-398)

```python
async def make_api_request(self, url: str, params: dict,
                           canal_name: str = "system",
                           retry_count: int = 0) -> Optional[dict]:
    """Make API request to YouTube with automatic key rotation"""

    # Check if all keys exhausted
    if self.all_keys_exhausted():
        logger.error("❌ All keys exhausted or suspended!")
        return None

    # Get current valid key
    current_key = self.get_current_api_key()
    if not current_key:
        return None

    params['key'] = current_key

    # Wait if rate limit near
    await self.rate_limiters[self.current_key_index].wait_if_needed()

    try:
        async with aiohttp.ClientSession() as session:
            # Calculate real cost and track quota
            request_cost = self.get_request_cost(url)  # search=100, others=1
            self.increment_quota_counter(canal_name, request_cost)
            self.rate_limiters[self.current_key_index].record_request()

            async with session.get(url, params=params,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:

                if response.status == 200:
                    data = await response.json()
                    return data

                elif response.status == 403:
                    error_data = await response.json()
                    error_obj = error_data.get('error', {})
                    error_msg = error_obj.get('message', '').lower()
                    error_reason = ''
                    if error_obj.get('errors'):
                        error_reason = error_obj['errors'][0].get('reason', '').lower()

                    # CASE 1: Quota Exceeded
                    if 'quota' in error_msg or 'quota' in error_reason:
                        logger.error(f"🚨 QUOTA EXCEEDED on key {self.current_key_index + 2}")
                        self.mark_key_as_exhausted()

                        # Retry with next key
                        if retry_count < self.max_retries and not self.all_keys_exhausted():
                            logger.info(f"♻️ Tentando com próxima chave...")
                            return await self.make_api_request(url, params,
                                                               canal_name, retry_count + 1)
                        return None

                    # CASE 2: Rate Limit
                    elif 'ratelimit' in error_msg or 'ratelimit' in error_reason:
                        if retry_count < self.max_retries:
                            wait_time = (2 ** retry_count) * 30  # Exponential backoff
                            logger.warning(f"⏱️ RATE LIMIT - waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            return await self.make_api_request(url, params,
                                                               canal_name, retry_count + 1)
                        return None

                    # CASE 3: Key Suspended (generic 403)
                    else:
                        logger.error(f"❌ KEY SUSPENDED (403 generic) on key {self.current_key_index + 2}")
                        self.mark_key_as_suspended()

                        # Retry with next key
                        if retry_count < self.max_retries and not self.all_keys_exhausted():
                            return await self.make_api_request(url, params,
                                                               canal_name, retry_count + 1)
                        return None

                else:
                    logger.warning(f"⚠️ HTTP {response.status}")
                    return None

    except asyncio.TimeoutError:
        logger.warning(f"⏱️ Timeout")
        if retry_count < self.max_retries:
            await asyncio.sleep(5)
            return await self.make_api_request(url, params, canal_name, retry_count + 1)
        return None

    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        return None
```

**What This Does:**
- Makes YouTube API request with current key
- Waits automatically if rate limit near
- Tracks quota usage (real costs: search=100, others=1)
- Handles 3 types of 403 errors differently:
  1. Quota exceeded → mark key exhausted, rotate
  2. Rate limit → exponential backoff, retry
  3. Generic 403 → mark key suspended, rotate
- Retries up to 3 times with different keys

---

### 4. Channel Video Collection
**File:** `collector.py` (lines 536-605)

```python
async def get_channel_videos(self, channel_id: str, canal_name: str,
                             days: int = 30) -> List[Dict[str, Any]]:
    """
    Get channel videos - NOW FETCHES ONLY 30 DAYS (instead of 60)
    Saves ~40-50% quota!
    """
    if not self.is_valid_channel_id(channel_id):
        logger.warning(f"❌ {canal_name}: Invalid channel ID")
        return []

    videos = []
    page_token = None
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    logger.info(f"🔍 {canal_name}: Buscando vídeos desde {cutoff_date.date()}")

    while True:
        if self.all_keys_exhausted():
            logger.warning(f"⚠️ {canal_name}: Keys exhausted during fetch")
            break

        # Build search request (EXPENSIVE: 100 units!)
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

        # Make API request
        data = await self.make_api_request(url, params, canal_name)

        if not data or not data.get('items'):
            break

        # Extract video IDs
        video_ids = [item['id']['videoId'] for item in data['items']]

        # Get detailed stats (1 unit per 50 videos)
        video_details = await self.get_video_details(video_ids, canal_name)

        # Combine data
        for item, details in zip(data['items'], video_details):
            if details:
                video_info = {
                    'video_id': item['id']['videoId'],
                    'titulo': decode_html_entities(item['snippet']['title']),
                    'url_video': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'data_publicacao': item['snippet']['publishedAt'],
                    'views_atuais': details.get('view_count', 0),
                    'likes': details.get('like_count', 0),
                    'comentarios': details.get('comment_count', 0),
                    'duracao': details.get('duration_seconds', 0)
                }
                videos.append(video_info)

        # Check for more pages
        page_token = data.get('nextPageToken')
        if not page_token:
            break

    logger.info(f"✅ {canal_name}: Encontrados {len(videos)} vídeos")
    return videos
```

**What This Does:**
- Searches for videos published in last 30 days
- Uses YouTube Search API (100 units per request!)
- Paginates through results (50 videos per page)
- Fetches detailed stats for each video batch
- Returns complete video data with views, likes, comments

---

## 📊 Database Schema

### canais_monitorados
```sql
CREATE TABLE canais_monitorados (
    id SERIAL PRIMARY KEY,
    nome_canal TEXT NOT NULL,
    url_canal TEXT UNIQUE NOT NULL,
    nicho TEXT,
    subnicho TEXT,
    lingua TEXT DEFAULT 'English',
    tipo TEXT DEFAULT 'minerado',  -- 'minerado' or 'nosso'
    status TEXT DEFAULT 'ativo',   -- 'ativo' or 'inativo'
    ultima_coleta TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### dados_canais_historico
```sql
CREATE TABLE dados_canais_historico (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER REFERENCES canais_monitorados(id) ON DELETE CASCADE,
    data_coleta DATE NOT NULL,
    inscritos INTEGER,
    views_30d INTEGER,
    views_15d INTEGER,
    views_7d INTEGER,
    videos_publicados_7d INTEGER,
    engagement_rate DECIMAL(5,2),
    UNIQUE(canal_id, data_coleta)
);
```

### videos_historico
```sql
CREATE TABLE videos_historico (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER REFERENCES canais_monitorados(id) ON DELETE CASCADE,
    video_id TEXT NOT NULL,
    titulo TEXT,
    url_video TEXT,
    data_publicacao TIMESTAMPTZ,
    data_coleta DATE NOT NULL,
    views_atuais INTEGER,
    likes INTEGER,
    comentarios INTEGER,
    duracao INTEGER,  -- seconds
    UNIQUE(video_id, data_coleta)
);
```

### coletas_historico
```sql
CREATE TABLE coletas_historico (
    id SERIAL PRIMARY KEY,
    data_inicio TIMESTAMPTZ NOT NULL,
    data_fim TIMESTAMPTZ,
    status TEXT DEFAULT 'em_progresso',  -- 'em_progresso', 'completo', 'erro'
    canais_total INTEGER,
    canais_sucesso INTEGER,
    canais_erro INTEGER,
    videos_coletados INTEGER,
    requisicoes_usadas INTEGER,
    duracao_segundos INTEGER,
    mensagem_erro TEXT
);
```

---

## 🔌 API Reference

### Manual Collection Trigger
```bash
# Start manual collection
curl -X POST https://your-railway-app.railway.app/api/collect \
  -H "Content-Type: application/json"

# Response
{
  "status": "in_progress",
  "message": "Coleta iniciada em background",
  "canais_total": 263,
  "coleta_id": 123
}
```

### Check Collection Status
```bash
# Get current collection status
curl https://your-railway-app.railway.app/health

# Response
{
  "status": "healthy",
  "collection_in_progress": true,
  "quota_usada_hoje": 45230,
  "last_collection": "2026-01-12T05:00:00Z"
}
```

### Get Collection History
```bash
# List recent collections
curl https://your-railway-app.railway.app/api/coletas-historico?limit=10

# Response
{
  "coletas": [
    {
      "id": 123,
      "data_inicio": "2026-01-12T05:00:00Z",
      "data_fim": "2026-01-12T06:15:00Z",
      "status": "completo",
      "canais_total": 263,
      "canais_sucesso": 263,
      "canais_erro": 0,
      "videos_coletados": 1547,
      "requisicoes_usadas": 45230,
      "duracao_segundos": 4500
    }
  ]
}
```

---

## 🐛 Troubleshooting

### Problem 1: Quota Exceeded Error
**Symptom:** Collection stops with "🚨 QUOTA EXCEEDED" in logs
**Cause:** One or more API keys hit 10,000 requests/day limit
**Solution:**
```bash
# Check which keys are exhausted
curl https://your-railway-app.railway.app/api/quota-status

# Wait until UTC midnight for automatic reset
# OR add more API keys to Railway environment
```

**Prevention:**
- Use 30-day collection (not 60-day) - saves 40% quota
- Monitor quota usage via `/health` endpoint
- Add more API keys if consistently hitting limit

---

### Problem 2: Rate Limit Hit
**Symptom:** "⏱️ RATE LIMIT" warnings with exponential backoff
**Cause:** More than 100 requests in 100 seconds on one key
**Solution:** This is handled automatically by rate limiter. Just wait.

**Prevention:**
- Rate limiter already prevents this (90/100s protection)
- If still seeing errors, reduce max_requests in RateLimiter init

---

### Problem 3: Suspended API Key
**Symptom:** "❌ KEY SUSPENDED (403 generic)" in logs
**Cause:** API key rejected by YouTube (usually temporary)
**Solution:**
```python
# Keys automatically unsuspended on server restart
# Manual unsuspend (if needed):
collector.reset_suspended_keys()
```

**Prevention:**
- Usually resolves itself after hours/days
- Use diverse API keys from different Google Cloud projects
- Don't abuse keys (respect rate limits)

---

### Problem 4: Channel Not Found
**Symptom:** "❌ Não foi possível obter channel_id" for specific channel
**Cause:** Invalid YouTube URL or channel deleted/hidden
**Solution:**
```sql
-- Check channel URL in database
SELECT id, nome_canal, url_canal
FROM canais_monitorados
WHERE nome_canal LIKE '%channel_name%';

-- Update URL if incorrect
UPDATE canais_monitorados
SET url_canal = 'https://www.youtube.com/@correct_handle'
WHERE id = X;
```

**Prevention:**
- Always use official YouTube channel URL
- Test new URLs manually before adding to database
- Use Channel ID format (youtube.com/channel/UCxxxx) when possible

---

### Problem 5: Missing Views Data
**Symptom:** Videos collected but views_30d = 0
**Cause:** Video published before 30-day cutoff window
**Solution:** This is expected behavior. Only videos from last 30 days are counted.

**Prevention:**
- Use /api/channel/{id}/history for historical view analysis
- Check data_publicacao field to confirm video age

---

### Problem 6: Collection Stuck "em_progresso"
**Symptom:** Collection log shows "em_progresso" for >2 hours
**Cause:** Server crashed mid-collection
**Solution:** Automatic cleanup runs every collection start:
```python
# In database.py (line 216-233)
await db.cleanup_stuck_collections()
# Marks collections older than 2h as 'erro'
```

**Prevention:**
- Monitor Railway logs during collection
- Set up Railway auto-restart on crash
- Check resource usage (memory/CPU) during collection

---

### Problem 7: UTF-8 Encoding Issues
**Symptom:** Broken characters in video titles (e.g., "��")
**Cause:** HTML entities not decoded
**Solution:** Already handled by `decode_html_entities()` function (line 16-20)

**Prevention:**
- Always use decode_html_entities() when storing YouTube data
- Check database encoding is UTF-8

---

## 🔗 Dependencies

### Depends On:
- **Railway Environment Variables:** 20 YouTube API keys (KEY_3-10, KEY_21-32)
- **Supabase Database:** All 4 tables (canais_monitorados, dados_canais_historico, videos_historico, coletas_historico)
- **YouTube Data API v3:** Must be enabled in Google Cloud Console for each project

### Used By:
- **Notifier System** (MINI_STEP_02) - triggers after successful collection
- **Frontend Mining Tab** (MINI_STEP_09) - displays collected data
- **Frontend Table Tab** (MINI_STEP_10) - shows subscriber evolution
- **Frontend Analytics Tab** (MINI_STEP_11) - uses historical data for trends

---

## 🎓 For Claude Next Time

**Key Points to Remember:**
1. **20 API keys** (not 8!) - KEY_3-10 + KEY_21-32 on Railway
2. **Rate limiter** runs BEFORE making requests (not after)
3. **search.list costs 100 units** - most expensive operation
4. **30-day collection** (changed from 60-day) - saves 40% quota
5. **Channel ID cache** persists until server restart - avoids duplicate calls
6. **Quota resets at UTC midnight** - exhausted_keys_date tracked by date
7. **Suspended keys reset on restart** - not persisted to database

**Common Modifications:**
- To add new API key: Add to Railway ENV as `YOUTUBE_API_KEY_X`, update collector.py lines 86-108
- To change collection window: Modify `days=30` parameter in get_channel_videos()
- To adjust rate limit: Change `max_requests=90` in RateLimiter.__init__()

**Architecture Notes:**
- Collection runs ASYNC (doesn't block API server)
- Each channel processed sequentially (not parallel) to control quota usage
- Database saves happen per-channel (not bulk at end) for resilience
- Errors logged but don't stop entire collection (keeps going with next channel)
