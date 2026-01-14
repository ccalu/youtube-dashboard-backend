# COMPLETE SYSTEM FLOW DIAGRAM

**YouTube Dashboard Backend - End-to-End Architecture**

Created: 2026-01-12
Location: `D:\ContentFactory\youtube-dashboard-backend\`

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUTUBE DASHBOARD SYSTEM                         │
│                     (FastAPI + Railway + Supabase)                      │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   FRONTEND   │ ───→ │   RAILWAY    │ ───→ │   SUPABASE   │
│   (Lovable)  │ ←─── │  (FastAPI)   │ ←─── │ (PostgreSQL) │
└──────────────┘      └──────────────┘      └──────────────┘
      │                      │                      │
      │                      ↓                      │
      │               ┌─────────────┐              │
      │               │  SCHEDULER  │              │
      │               │  (APScheduler)│             │
      │               └─────────────┘              │
      │                      ↓                      │
      ↓                      ↓                      ↓
┌──────────────────────────────────────────────────────────────┐
│  EXTERNAL SERVICES                                            │
│  • YouTube Data API v3 (20 keys)                            │
│  • YouTube Analytics API (OAuth per channel)                │
│  • Google Drive API (video downloads)                       │
│  • Google Sheets API (tracking)                             │
│  • AwesomeAPI (USD→BRL conversion)                          │
│  • M5 Server (transcription)                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Main System Flows

### 1. Daily Collection Flow (5 AM)

```
┌─────────────────────────────────────────────────────────────────┐
│ TRIGGER: Railway Scheduler (5:00 AM UTC daily)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Initialize Collection                                   │
│  File: main.py → scheduled_collection()                         │
│  - Check if collection already in progress                      │
│  - Create collection log in Supabase                            │
│  - Reset collector state                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Collect YouTube Data                                    │
│  File: collector.py → collect_channels_data()                   │
│  - For each of 263 channels:                                    │
│    • Resolve channel ID (with cache)                            │
│    • Fetch channel statistics (1 unit)                          │
│    • Fetch videos from last 30 days (100 units per page)       │
│    • Fetch video details (1 unit per 50 videos)                │
│    • Calculate views by period (local)                          │
│  - Rotate API keys as needed (20 keys available)               │
│  - Handle quota exceeded / rate limit / suspended keys         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Save to Database                                        │
│  File: database.py → save_canal_data() + save_videos_data()    │
│  Tables Updated:                                                │
│  • dados_canais_historico (daily snapshot)                     │
│  • videos_historico (latest video data)                        │
│  • canais_monitorados (ultima_coleta timestamp)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Check Notifications                                     │
│  File: notifier.py → check_and_create_notifications()           │
│  - Query videos that hit milestones (10k/24h, 50k/7d, etc)     │
│  - Check for existing notifications (anti-duplication)          │
│  - Create or elevate notifications                             │
│  - Filter by subniche if rule specifies                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Collect Monetization Data (if enabled)                  │
│  File: monetization_collector.py → collect_monetization_data() │
│  - For each of 16 monetized channels:                          │
│    • Fetch total views (YouTube Data API)                      │
│    • Calculate views_24h (today - yesterday)                   │
│    • Save snapshot to dados_canais_historico                   │
│    • Create revenue estimate if no data yet                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Finalize Collection                                     │
│  File: database.py → update_coleta_log()                        │
│  - Mark collection as 'completo'                                │
│  - Record: canais_sucesso, canais_erro, videos_coletados       │
│  - Record: requisicoes_usadas, duracao_segundos                │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2. User Requests Video Transcription

```
┌─────────────────────────────────────────────────────────────────┐
│ USER ACTION: Clicks "Transcrever" button on video               │
│ Frontend (Lovable) → POST /api/transcribe?video_id=xyz         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Check Cache                                             │
│  File: main.py → transcribe_video_async()                       │
│  Query: SELECT * FROM transcriptions WHERE video_id = 'xyz'    │
│  - If cached: return immediately                                │
│  - If not: continue to Step 2                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Create Async Job                                        │
│  File: main.py → process_transcription_job()                    │
│  - Generate job_id (UUID)                                       │
│  - Store in transcription_jobs dict                             │
│  - Start background thread                                      │
│  - Return job_id to frontend                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Send to M5 Server                                       │
│  File: main.py → process_transcription_job() (background)       │
│  POST https://transcription.2growai.com.br/transcribe          │
│  Body: {video_id: 'xyz', language: 'en'}                       │
│  - Receive m5_job_id                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Poll M5 Status                                          │
│  File: main.py → process_transcription_job() (loop)             │
│  GET https://transcription.2growai.com.br/status/{m5_job_id}   │
│  - Poll every 5 seconds                                         │
│  - Max 360 attempts (30 minutes)                                │
│  - Update job status in transcription_jobs                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Store Result                                            │
│  File: database.py → save_transcription_cache()                 │
│  INSERT INTO transcriptions (video_id, transcription, ...)      │
│  - Mark job as 'completed'                                      │
│  - Store transcription text                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Frontend Polls Status                                   │
│  GET /api/transcribe/status/{job_id}                            │
│  - Frontend polls every 5 seconds                               │
│  - Shows progress message                                       │
│  - Displays transcription when completed                        │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. Automatic Video Upload Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ TRIGGER: New row added to upload_queue (via Google Sheets)      │
│ Status: 'pending' → picked up by queue worker                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Queue Worker Detects Pending Upload                     │
│  File: yt_uploader/queue_worker.py → _process_batch()           │
│  Query: SELECT * FROM upload_queue                              │
│         WHERE status = 'pending' LIMIT 5                        │
│  - Respect semaphore (max 3 simultaneous uploads)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Download Video from Google Drive                        │
│  File: yt_uploader/uploader.py → download_video()               │
│  - Extract file_id from GDrive URL                              │
│  - Use gdown library (handles virus scan warning)               │
│  - Save to /tmp/videos/{file_id}.mp4                            │
│  - Validate file size (must be > 100KB)                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Get OAuth Credentials                                   │
│  File: yt_uploader/oauth_manager.py → get_valid_credentials()  │
│  Query: SELECT * FROM yt_oauth_tokens                           │
│         WHERE channel_id = 'UCxxxx'                             │
│  - Check if token expired                                       │
│  - Refresh token if needed                                      │
│  - Return valid credentials                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Upload to YouTube                                       │
│  File: yt_uploader/uploader.py → upload_to_youtube()            │
│  - Sanitize title (UTF-8 fix, 100 char limit)                  │
│  - Create YouTube API service (googleapiclient)                 │
│  - Upload with resumable chunks (5MB chunks)                    │
│  - Set privacy: 'private' (draft mode)                          │
│  - Add to default playlist (if configured)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Update Google Sheets                                    │
│  File: yt_uploader/sheets.py → update_upload_status_in_sheet() │
│  - Find row by unique identifier                                │
│  - Update column O with "done"                                  │
│  - Update column P with video_id                                │
│  - Use service account credentials                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Cleanup & Mark Complete                                 │
│  File: main.py → process_upload_task()                          │
│  - Delete temp file from /tmp/videos/                           │
│  - UPDATE upload_queue SET status='completed'                   │
│  - Record video_id and youtube_url                              │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4. Revenue Collection Flow (OAuth)

```
┌─────────────────────────────────────────────────────────────────┐
│ TRIGGER: Scheduler (daily after main collection)                │
│ OR: Manual via POST /api/monetization/collect                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Get Monetized Channels                                  │
│  File: monetization_collector.py → get_monetized_channels()     │
│  Query: SELECT * FROM yt_channels                               │
│         WHERE is_monetized = true                               │
│  Result: 16 channels                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: For Each Channel - Get OAuth Token                      │
│  File: monetization_endpoints.py → get_oauth_token()            │
│  Query: SELECT * FROM yt_oauth_tokens                           │
│         WHERE channel_id = 'UCxxxx'                             │
│  - Check expiry                                                 │
│  - Refresh if needed                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Fetch Analytics Data                                    │
│  File: monetization_endpoints.py → fetch_analytics_data()       │
│  YouTube Analytics API:                                         │
│  GET youtubeAnalytics.reports.query                             │
│  Dimensions: day                                                │
│  Metrics: views, estimatedRevenue                               │
│  - Fetch last 7 days of data                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Convert USD → BRL                                       │
│  File: financeiro.py → get_usd_brl_rate()                       │
│  GET https://economia.awesomeapi.com.br/last/USD-BRL           │
│  - Get current exchange rate                                    │
│  - Revenue_BRL = Revenue_USD * Rate                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Save to Database                                        │
│  File: monetization_endpoints.py → save_daily_metrics()         │
│  INSERT INTO yt_daily_metrics                                   │
│  (channel_id, date, views, revenue, is_estimate, rpm)          │
│  - One row per day per channel                                  │
│  - is_estimate = false (real data from YouTube)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema Overview

### Core Tables

```sql
-- Channel tracking
canais_monitorados (263 channels)
  ├─ dados_canais_historico (daily snapshots)
  ├─ videos_historico (video data, 30-day window)
  └─ notificacoes (intelligent alerts)

-- Monetization (16 channels)
yt_channels
  ├─ yt_oauth_tokens (OAuth credentials per channel)
  ├─ yt_daily_metrics (revenue data per day)
  └─ yt_channel_credentials (Client ID/Secret per channel)

-- Upload automation
upload_queue (pending/processing/completed)
  └─ Tracks: video URL, channel, metadata, status

-- Financial system
financeiro_categorias
financeiro_lancamentos (manual entries)
financeiro_taxas (tax rules)
financeiro_metas (targets)

-- System logs
coletas_historico (collection logs)
transcriptions (cache)
```

---

## 🔑 Key Integration Points

### Railway Environment Variables
```bash
# YouTube Data API (20 keys)
YOUTUBE_API_KEY_3, _4, _5, ..., _10
YOUTUBE_API_KEY_21, _22, ..., _32

# Supabase
SUPABASE_URL
SUPABASE_KEY
SUPABASE_SERVICE_ROLE_KEY (for OAuth tables)

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS (service account JSON)

# Upload system
TEMP_VIDEO_PATH=/tmp/videos
UPLOAD_WORKER_ENABLED=true
UPLOAD_WORKER_INTERVAL_SECONDS=120

# Monetization
MONETIZATION_COLLECTOR_ENABLED=true
```

### External APIs Used
- **YouTube Data API v3** - Channel/video data (collector.py)
- **YouTube Analytics API** - Revenue data (monetization_endpoints.py)
- **Google Drive API** - Video downloads (yt_uploader/uploader.py)
- **Google Sheets API** - Tracking updates (yt_uploader/sheets.py)
- **AwesomeAPI** - USD→BRL conversion (financeiro.py)
- **M5 Server** - Transcriptions (main.py)

---

## 🚀 Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      RAILWAY DEPLOYMENT                       │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ main.py (FastAPI app)                                        │
│  ├─ Runs on PORT (Railway assigns)                          │
│  ├─ CORS enabled for Lovable frontend                       │
│  └─ Includes monetization_router                            │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ APScheduler (background tasks)                               │
│  ├─ 5:00 AM: scheduled_collection()                         │
│  ├─ 5:30 AM: collect_monetization() (if enabled)            │
│  └─ 6:00 AM: cleanup_old_jobs()                             │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ Queue Worker (background thread)                             │
│  ├─ Polls upload_queue every 120s                           │
│  ├─ Processes max 5 uploads per batch                       │
│  └─ Respects semaphore (max 3 simultaneous)                 │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ Supabase (PostgreSQL)                                        │
│  ├─ All data persistence                                    │
│  ├─ RLS enabled on OAuth tables                             │
│  └─ Automatic backups                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Summary

### Inbound Data
1. **YouTube → Collector** - Channel/video stats (5 AM daily)
2. **YouTube Analytics → Monetization** - Revenue data (5:30 AM daily)
3. **Google Sheets → Upload Queue** - New videos to upload (continuous scan)
4. **M5 Server → Transcription** - Transcription results (async)
5. **AwesomeAPI → Financial** - Exchange rates (on demand)

### Outbound Data
1. **Database → Frontend** - All API endpoints (real-time)
2. **Upload System → YouTube** - Video uploads (queued)
3. **Upload System → Google Sheets** - Status updates (after upload)

---

## 🎯 Critical Paths

### Path 1: New Video Gets Notification
```
Video published → Collector finds it (5 AM) → Saves to videos_historico →
Notifier checks rules → Hits 10k views in 24h → Creates notification →
Frontend polls /api/notificacoes → Arthur sees alert
```

### Path 2: Revenue Tracked
```
YouTube generates revenue → Analytics API collects (daily) →
OAuth token validates → Revenue fetched (USD) → Converted to BRL →
Saved to yt_daily_metrics → Frontend shows in graphs
```

### Path 3: Video Uploaded
```
Producer adds row to Sheet → Scanner finds it → Creates upload_queue entry →
Worker downloads from GDrive → Gets OAuth credentials →
Uploads to YouTube (draft) → Updates Sheet with "done" →
Video appears in YouTube Studio
```

---

## 📝 For Claude Next Time

**Critical Architecture Points:**
1. **Async everywhere** - FastAPI + asyncio for all I/O operations
2. **Circuit breakers** - API keys, upload worker, transcription jobs
3. **Rate limiting** - YouTube (90/100s), sheets (100/100s), drive (no hard limit)
4. **OAuth isolation** - Each channel has own Client ID (prevents conflicts)
5. **Queue-based uploads** - Never blocks API server, respects concurrency limits
6. **Cache strategy** - Channel IDs, transcriptions (persistent), jobs (1h expiry)

**Scaling Considerations:**
- Add more API keys if quota consistently exceeded
- Increase upload workers if queue grows (currently max 3)
- Add Redis for distributed caching (currently in-memory)
- Consider separate service for transcriptions (currently embedded)

**Monitoring Points:**
- `/health` - Overall system status
- `/api/coletas-historico` - Collection success rate
- `/api/upload-status` - Upload queue health
- Railway logs - Errors and performance
