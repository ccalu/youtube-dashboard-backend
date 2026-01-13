# MINI-STEPS DOCUMENTATION INDEX

**YouTube Dashboard Backend - Complete System Documentation**

Created: 2026-01-12
Location: `D:\ContentFactory\youtube-dashboard-backend\docs\mini-steps\`

---

## 📋 Purpose

This documentation provides **ultra-detailed** mini-step guides for every major function in the YouTube Dashboard system. Each mini-step includes:

- Complete code with line numbers
- Flow diagrams (Frontend → Railway → Supabase)
- API reference with curl examples
- Database schemas
- Troubleshooting guides
- Dependencies mapping

**Target Audience:** Future Claude sessions, new developers, and Cellibs for understanding the complete system.

---

## 🗂️ Documentation Structure

### Backend Mini-Steps (8 documents)

1. **[MINI_STEP_01_COLETA_YOUTUBE.md](mini-steps/MINI_STEP_01_COLETA_YOUTUBE.md)**
   - YouTube Data API collector
   - 20 API keys rotation system
   - Rate limiter (90/100s protection)
   - Channel and video collection

2. **[MINI_STEP_02_NOTIFICACOES.md](mini-steps/MINI_STEP_02_NOTIFICACOES.md)**
   - Intelligent notification system
   - Rules engine (10k/24h, 50k/7d, 100k/30d)
   - Anti-duplication + elevation logic
   - Arthur's workflow integration

3. **[MINI_STEP_03_MONETIZACAO_OAUTH.md](mini-steps/MINI_STEP_03_MONETIZACAO_OAUTH.md)**
   - OAuth 2.0 flow (isolated per channel)
   - YouTube Analytics API integration
   - Revenue collection (USD→BRL conversion)
   - Token refresh automation

4. **[MINI_STEP_04_UPLOAD_AUTOMATICO.md](mini-steps/MINI_STEP_04_UPLOAD_AUTOMATICO.md)**
   - Upload queue system
   - Semaphore concurrency control (max 3 uploads)
   - Google Drive download integration
   - Google Sheets tracking

5. **[MINI_STEP_05_SISTEMA_FINANCEIRO.md](mini-steps/MINI_STEP_05_SISTEMA_FINANCEIRO.md)**
   - Financial management system
   - Manual entries (revenue/expense)
   - Categories and taxes
   - USD→BRL conversion (AwesomeAPI)

6. **[MINI_STEP_06_TRANSCRICAO_M5.md](mini-steps/MINI_STEP_06_TRANSCRICAO_M5.md)**
   - M5 server transcription integration
   - Async jobs system
   - Polling mechanism
   - Cache management

7. **[MINI_STEP_07_HISTORICO_DIARIO.md](mini-steps/MINI_STEP_07_HISTORICO_DIARIO.md)**
   - Daily subscriber tracking
   - Historical evolution data
   - Problem detection (sudden drops)
   - Performance graphs

8. **[MINI_STEP_08_INTEGRACAO_SHEETS.md](mini-steps/MINI_STEP_08_INTEGRACAO_SHEETS.md)**
   - Google Sheets API integration
   - Service Account authentication
   - Upload tracking (column O: "done")
   - Revenue dashboards

### Frontend Mini-Steps (3 documents)

9. **[MINI_STEP_09_FRONTEND_ABA_MINERACAO.md](mini-steps/MINI_STEP_09_FRONTEND_ABA_MINERACAO.md)**
   - Mining tab UI/UX
   - Channels, videos, notifications display
   - Transcription request button
   - Filters and search

10. **[MINI_STEP_10_FRONTEND_ABA_TABELA.md](mini-steps/MINI_STEP_10_FRONTEND_ABA_TABELA.md)**
    - Table tab (our 50 channels)
    - Grouping by subniche
    - Daily subscriber diff display
    - Performance-based sorting

11. **[MINI_STEP_11_FRONTEND_ABA_ANALYTICS.md](mini-steps/MINI_STEP_11_FRONTEND_ABA_ANALYTICS.md)**
    - Analytics tab
    - Subniche trends
    - Revenue graphs
    - Best/worst days analysis

---

## 📁 Additional Documentation

### Changelog
- **[changelog/2025-01-12_CRIACAO_SISTEMA_COMPLETO.md](changelog/2025-01-12_CRIACAO_SISTEMA_COMPLETO.md)** - Complete system creation log

### System Architecture
- **[CODIGO_DETALHADO/FLOW_COMPLETO_SISTEMA.md](CODIGO_DETALHADO/FLOW_COMPLETO_SISTEMA.md)** - Complete system flow diagram

---

## 🔍 How to Use This Documentation

### For Claude (Next Session)
1. Start with **MINI_STEPS_INDEX.md** (this file) for overview
2. Read relevant mini-step before modifying code
3. Follow the "Para Claude Próxima Vez" section in each doc
4. Check **troubleshooting** sections for common issues

### For Cellibs (Understanding System)
1. Read **FLOW_COMPLETO_SISTEMA.md** for big picture
2. Dive into specific mini-steps as needed
3. Use **API Reference** sections to test endpoints
4. Refer to **Database Schema** sections for data structure

### For New Features
1. Identify which mini-step covers the area
2. Read **Dependencies** section to understand impact
3. Check **Code Snippets** for implementation patterns
4. Update the mini-step doc after changes

---

## 📊 System Statistics

- **Total Backend Files:** 792 lines (collector.py), 449 lines (notifier.py), 1141 lines (database.py), 311 lines (monetization_collector.py), 994 lines (financeiro.py)
- **Total API Endpoints:** 50+ endpoints across main.py and monetization_endpoints.py
- **Database Tables:** 20+ tables (canais_monitorados, videos_historico, notificacoes, yt_channels, yt_daily_metrics, financeiro_*, etc.)
- **YouTube API Keys:** 20 keys (200k requests/day capacity)
- **Monetized Channels:** 16 channels with OAuth integration

---

## 🎯 Quick Navigation

### I need to understand...
- **How YouTube collection works** → [MINI_STEP_01](mini-steps/MINI_STEP_01_COLETA_YOUTUBE.md)
- **How notifications are triggered** → [MINI_STEP_02](mini-steps/MINI_STEP_02_NOTIFICACOES.md)
- **How OAuth works for monetization** → [MINI_STEP_03](mini-steps/MINI_STEP_03_MONETIZACAO_OAUTH.md)
- **How uploads are automated** → [MINI_STEP_04](mini-steps/MINI_STEP_04_UPLOAD_AUTOMATICO.md)
- **How financial system works** → [MINI_STEP_05](mini-steps/MINI_STEP_05_SISTEMA_FINANCEIRO.md)
- **How transcription works** → [MINI_STEP_06](mini-steps/MINI_STEP_06_TRANSCRICAO_M5.md)
- **How subscriber tracking works** → [MINI_STEP_07](mini-steps/MINI_STEP_07_HISTORICO_DIARIO.md)
- **How Google Sheets integration works** → [MINI_STEP_08](mini-steps/MINI_STEP_08_INTEGRACAO_SHEETS.md)

### I need to fix...
- **Quota exceeded errors** → [MINI_STEP_01](mini-steps/MINI_STEP_01_COLETA_YOUTUBE.md#troubleshooting)
- **Duplicate notifications** → [MINI_STEP_02](mini-steps/MINI_STEP_02_NOTIFICACOES.md#troubleshooting)
- **OAuth token expired** → [MINI_STEP_03](mini-steps/MINI_STEP_03_MONETIZACAO_OAUTH.md#troubleshooting)
- **Upload timeout** → [MINI_STEP_04](mini-steps/MINI_STEP_04_UPLOAD_AUTOMATICO.md#troubleshooting)
- **Wrong currency conversion** → [MINI_STEP_05](mini-steps/MINI_STEP_05_SISTEMA_FINANCEIRO.md#troubleshooting)
- **Transcription stuck** → [MINI_STEP_06](mini-steps/MINI_STEP_06_TRANSCRICAO_M5.md#troubleshooting)
- **Missing historical data** → [MINI_STEP_07](mini-steps/MINI_STEP_07_HISTORICO_DIARIO.md#troubleshooting)
- **Sheets permission denied** → [MINI_STEP_08](mini-steps/MINI_STEP_08_INTEGRACAO_SHEETS.md#troubleshooting)

---

## ⚠️ Important Notes

1. **Line Numbers:** All code snippets include actual line numbers from source files (as of 2026-01-12)
2. **Railway Context:** All flows assume deployment on Railway with proper environment variables
3. **Supabase Integration:** All database operations go through Supabase client
4. **Windows Environment:** Cellibs uses Windows + PowerShell
5. **No Local API Keys:** YouTube API keys only exist on Railway, not locally

---

## 🔄 Keeping Documentation Updated

When making changes to code:
1. Update the relevant mini-step document
2. Update line numbers if functions moved
3. Add new troubleshooting entries if issues found
4. Update **changelog** with date and changes
5. Keep **FLOW_COMPLETO_SISTEMA.md** synced with architecture changes

---

## 📞 Support

For questions or issues with documentation:
- **Cellibs:** Review specific mini-step + troubleshooting section
- **Claude:** Read "Para Claude Próxima Vez" sections for context
- **Developers:** Follow code snippets + API reference sections

---

**Last Updated:** 2026-01-12
**Created By:** Claude Code (Sonnet 4.5)
**Maintained By:** Cellibs + Claude Code
