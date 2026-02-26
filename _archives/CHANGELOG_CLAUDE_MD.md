# CHANGELOG - Histórico de Atualizações do Backend

> Este arquivo foi extraído do CLAUDE.md em 26/02/2026.
> Contém o histórico completo de features, bug fixes e otimizações.
> NÃO é carregado pelo Claude Code — serve apenas como referência humana.

---

## 🆕 ATUALIZAÇÕES (25/02/2026):

### 📊 CTR Collector via YouTube Reporting API ✅
**Desenvolvido:** 25/02/2026
**Status:** ✅ Implementado, 21 jobs criados, aguardando primeiros CSVs (~48h)
**Commit:** `8519920`

**Por que Reporting API?**
- YouTube Analytics API **NÃO** suporta `videoThumbnailImpressions` com `dimension=video` (retorna erro 400)
- YouTube Reporting API é a **única** forma de obter CTR por vídeo individual
- Report type: `channel_reach_basic_a1` (gera CSV diário com impressions + CTR por vídeo)

**Arquitetura:**
```
1. SETUP (1x só):  POST /api/ctr/setup-jobs → cria job no Google por canal
2. Google gera:    1 CSV por dia automaticamente (cada CSV = 1 dia de dados)
3. COLETA SEMANAL: Domingo 8AM (SP) → baixa 7 CSVs → soma + CTR ponderado
4. SALVA:          PATCH em yt_video_metrics (impressions + ctr) + yt_channels (avg_ctr)
```

**ctr_collector.py (~824 linhas):**
- 20 funções: OAuth, reporting jobs, download CSV, agregação, salvamento
- `get_or_create_job()`: auto-provisioning
- `download_and_parse_csv()`: baixa CSV (com suporte a gzip) e parseia
- `aggregate_weekly_data()`: soma impressões + CTR médio ponderado
- `save_ctr_data()`: PATCH-only em yt_video_metrics
- `save_channel_avg_ctr()`: salva avg_ctr + total_impressions em yt_channels

**Migration `017_ctr_reporting_tables.sql`:**
- yt_video_metrics: +impressions (BIGINT) + ctr (FLOAT)
- yt_video_daily: +impressions (BIGINT) + ctr (FLOAT)
- yt_channels: +avg_ctr (FLOAT) + total_impressions (BIGINT)
- Nova tabela yt_reporting_jobs

**Testes:** 72/72 PASS

---

## 🆕 ATUALIZAÇÕES (24/02/2026):

### 🛡 Agente de Score de Autenticidade + Relatório Unificado ✅
**Commit:** `89aa376`

**Arquitetura: 2 agentes, 1 relatório**
```
POST /api/analise-completa/{channel_id}
  ├── copy_analysis_agent.run_analysis()     → performance
  ├── authenticity_agent.run_analysis()       → autenticidade
  └── _build_unified_report() combina os 2
```

**authenticity_agent.py (~1100 linhas):**
- Score 0-100 (mais alto = mais seguro)
- 2 fatores (50/50): Variedade de Estruturas + Diversidade de Títulos
- Níveis: EXCELENTE/BOM/ATENCAO/RISCO/CRITICO
- LLM (GPT-4o-mini) para diagnóstico

**Migration `016_authenticity_tables.sql`:**
- Tabela authenticity_analysis_runs

**Testes:** 205/205 PASS

### Dashboard Visual de Análise de Copy ✅
- HTML/CSS/JS inline em main.py como DASH_COPY_ANALYSIS_HTML
- Sidebar com 21 canais por subnicho
- Dark theme

### Bug Fixes (24/02/2026):
- Erro 500 Railway: reescrito para usar supabase client
- Emojis surrogate pair: substituídos por badges
- Cores subnicho corrigidas
- Campo lingua adicionado

---

## 🆕 ATUALIZAÇÕES (23/02/2026):

### 🧠 Agente de Análise de Copy - MVP ✅
- copy_analysis_agent.py - analisa estruturas de copy por canal
- monetization_oauth_collector.py - coleta métricas via Analytics API
- Campo copy_spreadsheet_id em yt_channels
- 21 canais com Analytics API habilitado

### Fix: Dashboard Upload Mostra Último Vídeo ✅
- upload_map pega mais recente por created_at

### 🏢 Mission Control - Escritório Virtual ✅
- 3 endpoints: /mission-control, /api/mission-control/status, /api/mission-control/sala/{canal_id}

---

## 🆕 ATUALIZAÇÕES (16/02/2026):

### ⚡ Otimização Quota API 95% mais barata ✅
- De search.list (100 units) para playlistItems.list (1 unit)
- Total diário: ~26,380 → ~1,324 units
- 7 chaves suspensas removidas, 13 ativas

### 🎬 Animação de Upload Forçado ✅
- Botão com estados visuais (⏳/✅/❌)
- Polling inteligente a cada 3s

### 🔧 Correção OAuth + Script Re-auth ✅
- Canal "Crônicas da Coroa" com invalid_grant resolvido

---

## 🆕 ATUALIZAÇÕES (03/02/2026):

### OAuth Scopes para Playlists ✅
- 4 scopes obrigatórios: upload, youtube, force-ssl, spreadsheets
- Canais antigos devem refazer OAuth com wizard v3

---

## 🆕 ATUALIZAÇÕES (02/02/2026):

### Sistema de Comentários ✅
- 15.074 comentários coletados
- 100% traduzidos PT-BR
- 6 endpoints API
- 6 fixes aplicados (13/02/2026)

---

## ATUALIZAÇÕES (30/01/2026):
- Reorganização: de 304 para 232 canais
- Fix endpoint DELETE (erro 500)
- Materialized Views via botão Atualizar

## ATUALIZAÇÕES (29/01/2026):
- Reorganização completa do projeto (5 pastas)
- Sistema Kanban endpoint de movimentação
- Correções sistema de comentários (inscritos_diff, collected_at)

## ATUALIZAÇÕES (23/01/2026):
- Materialized Views + Cache 24h (3000ms → 0.1ms)

## ATUALIZAÇÕES (22/01/2026):
- sync.py v4.3
- Bug fix: colisão variável offset
- Bug fix: cálculo inscritos_diff
- Campos views_growth_7d/30d

## ATUALIZAÇÕES (17/01/2026):
- Otimização coleta (50% menos API calls)
- Tracking de falhas de coleta
- Endpoints de diagnóstico

## ATUALIZAÇÕES (02/12/2025):
- Aba Tabela (nossos canais)
- Notificações bugs corrigidos
- 8 novas API keys (KEY_25-32)
