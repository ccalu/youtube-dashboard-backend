# 📋 CHANGELOG - Dashboard Mineração YouTube

Atualizações recentes do backend (Nov-Dez 2025)

---

## 🎯 ARQUITETURA ATUAL

### **Core Files:**
- `main.py` - FastAPI app + endpoints + scheduler
- `database.py` - Supabase client + queries
- `collector.py` - YouTube Data API collector (20 keys)
- `notifier.py` - Sistema de notificações inteligente

### **Monetização:**
- `monetization_collector.py` - Estimativas (RPM aproximado)
- `monetization_oauth_collector.py` - Revenue REAL (OAuth)
- `monetization_endpoints.py` - Endpoints FastAPI

### **Tabelas Supabase:**
- `canais_monitorados` - Registro de canais
- `dados_canais_historico` - Snapshots diários
- `videos_historico` - Performance vídeos
- `notificacoes` - Alertas inteligentes
- `yt_daily_metrics`, `yt_video_metrics`, `yt_country_metrics` - Monetização

---

## 🆕 FEATURES IMPLEMENTADAS

### **1. Sistema de Monetização (02/12/2025)**
**Backend:**
- Coleta OAuth revenue REAL (YouTube Analytics API)
- Estimativas via RPM quando OAuth indisponível
- 3 níveis: canal, vídeo, país
- Separação quota: OAuth não usa Data API v3

**Endpoints:**
- `/api/monetization/revenue-24h` - Receita últimas 24h
- `/api/monetization/top-videos` - Top 10 vídeos
- `/api/monetization/top-performers` - Canais performance
- `/api/monetization/country-stats` - Distribuição países
- `/api/monetization/daily-chart` - Gráfico 30 dias

### **2. Aba Tabela - Nossos Canais (02/12/2025)**
**Backend:**
- Endpoint `/api/canais-tabela`
- Agrupamento por subnicho
- Ordenação: melhor → menor → zero → null
- Cálculo `inscritos_diff` (ganho 24h)

**Lógica:**
```python
# database.py:327-332
inscritos_diff = inscritos_hoje - inscritos_ontem
# Comparação: última coleta vs penúltima
```

### **3. Expansão API Keys (02/12/2025)**
- **Antes:** 12 chaves (KEY_3 a KEY_10, KEY_21 a KEY_24)
- **Depois:** 20 chaves (KEY_3 a KEY_32)
- **Capacidade:** +67% (120k → 200k units/dia)

### **4. Correção Notificações (02/12/2025)**
**Bugs corrigidos:**
- Query SQL otimizada (dados em uma query)
- Filtro subnicho case-insensitive
- Re-notificação para milestones maiores

**Regras:**
- 100 inscritos, depois 1K, 5K, 10K, 25K, 50K, 100K, 250K, 500K, 1M
- Vídeo 1K views (primeiras 24h)
- Vídeo 10K views (48h-7d)

### **5. Correção 41 Canais com Erro → 4 (11/12/2025)**
**Ações:**
- Deletados: 7 canais inativos
- Corrigidos: 19 canais (Unicode + /featured)
  - 3 via Search API (Channel ID)
  - 16 via format fix (decode URLs)
- Resultado: **87% redução erros**

**Técnica:**
- Remover `/featured` das URLs
- Decode URL encoding (`%C4%B1` → `ı`)
- Formatos suportados: `/channel/UCxxx`, `/@handle`

---

## ⚙️ CONFIGURAÇÕES

### **Coleta Automática:**
- **Horário:** 5 AM (Railway scheduler)
- **Ordem:** Mineração → OAuth → Notificações
- **Duração:** ~60-80min para 550 canais

### **API Quota:**
- 20 chaves × 10.000 units = 200.000 units/dia
- Rate limit: 90 req/100s por key
- Rotação automática quando esgota

### **Cache:**
- Channel ID resolution (em memória)
- Persiste até restart servidor

---

## 🐛 BUGS CONHECIDOS

### **1. YouTube API Limites:**
- Canais >1M inscritos: número aproximado (~100K precision)
- forHandle() falha com Unicode (turco, polonês, russo, coreano)
- **Solução:** Usar `/channel/UCxxx` quando possível

### **2. Inscritos Diff:**
- Comparação última vs penúltima coleta (não necessariamente 24h)
- Se canal falhou ontem: mostra diferença de 2+ dias
- **Design:** Intencional (Opção A escolhida)

---

## 📊 MÉTRICAS ATUAIS

- **Canais ativos:** ~551 (após limpeza 11/12)
- **Quota diária usada:** ~150k units (75%)
- **Taxa sucesso coleta:** >95%
- **Canais com erro:** ≤4 (meta: ≤10)

---

## 🔄 PRÓXIMAS MELHORIAS

**Sugestões futuras:**
1. Fallback Search API automático (handles Unicode)
2. Dashboard monetização real-time
3. Alertas Telegram/Discord
4. Export dados CSV/Excel
5. Análise ML (previsão growth)

---

**Última atualização:** 11/12/2025
**Versão backend:** 2.0 (Monetização + Tabela)
