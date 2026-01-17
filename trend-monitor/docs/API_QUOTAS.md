# Calculo de Quotas e Custos das APIs

## Resumo Executivo

| API | Quota Diaria | Uso por Coleta | Coletas/Dia Possiveis | Status |
|-----|--------------|----------------|----------------------|--------|
| YouTube | 10.000 units | 7 units | 1.428 coletas | ✅ Sobra muito |
| Google Trends | ~100/hora | 7 requests | ~14/hora | ✅ Tranquilo |
| Hacker News | Ilimitado | 1 request | Ilimitado | ✅ Sem limite |
| Reddit | - | - | - | ❌ Desabilitado |

---

## YouTube Data API v3

### Quota
- **Limite diario:** 10.000 unidades
- **Reset:** Meia-noite Pacific Time (PT)

### Custo por Request
| Endpoint | Custo | Uso no Trend Monitor |
|----------|-------|---------------------|
| `videos.list(chart=mostPopular)` | 1 unidade | Sim (trending) |
| `search.list` | 100 unidades | Nao usado na coleta padrao |
| `channels.list` | 1 unidade | Nao usado |

### Calculo por Coleta
```
7 paises × 1 request × 1 unidade = 7 unidades por coleta
```

### Capacidade Diaria
```
10.000 unidades ÷ 7 unidades = 1.428 coletas possiveis/dia
```

### Uso Real
- **1 coleta/dia:** 7 unidades (0.07% da quota)
- **2 coletas/dia:** 14 unidades (0.14% da quota)
- **10 coletas/dia:** 70 unidades (0.7% da quota)

**Conclusao:** Quota MUITO folgada. Podemos rodar ate 1.428x por dia.

### Dados Retornados por Coleta
- 7 paises × 50 videos = **350 videos/coleta**
- Campos: title, views, likes, comments, channel, thumbnail, URL

---

## Google Trends (pytrends)

### Como Funciona
- **Nao usa API key** - faz scraping do Google Trends
- **Rate limit:** ~100 requests/hora (soft limit, Google pode bloquear temporariamente)

### Calculo por Coleta
```
7 paises × 1 request = 7 requests por coleta
```

### Capacidade
```
100 requests/hora ÷ 7 = ~14 coletas/hora
```

### Uso Real
- 1 coleta/dia = 7 requests = **muito seguro**
- Delay de 1s entre requests ja implementado

### Dados Retornados
- 7 paises × ~20 trends = **~140 trends/coleta**
- Campos: title, volume aproximado, link do Google Trends

---

## Hacker News API

### Como Funciona
- **API publica** - sem autenticacao
- **Sem limite** oficial de requests

### Calculo por Coleta
```
1 request (top stories) + 30 requests (detalhes) = 31 requests
```

### Dados Retornados
- Top 30 stories
- Campos: title, URL, score, author, comments

---

## Reddit (DESABILITADO)

### Status
Reddit nao liberou criacao de app. Coleta desabilitada.

### Quando ativar
- Criar app em reddit.com/prefs/apps
- Adicionar CLIENT_ID e SECRET no .env
- Limite: 60 requests/minuto (gratis)

---

## Consumo Total por Coleta

| Fonte | Requests | Dados |
|-------|----------|-------|
| YouTube | 7 | 350 videos |
| Google Trends | 7 | ~140 trends |
| Hacker News | 31 | 30 stories |
| **TOTAL** | **45 requests** | **~520 itens** |

### Tempo de Execucao
- YouTube: ~4 segundos (0.5s delay × 7)
- Google Trends: ~10 segundos (1s delay × 7 + processamento)
- Hacker News: ~5 segundos
- **Total: ~20-30 segundos por coleta**

---

## Recomendacao de Frequencia

| Frequencia | YouTube Units/Dia | Seguro? |
|------------|-------------------|---------|
| 1x/dia | 7 | ✅ Muito seguro |
| 2x/dia | 14 | ✅ Muito seguro |
| 6x/dia (4h em 4h) | 42 | ✅ Seguro |
| 24x/dia (1h em 1h) | 168 | ✅ Seguro |
| 144x/dia (10 em 10 min) | 1.008 | ⚠️ Ainda dentro da quota |

**Recomendacao:** 1-2 coletas por dia e suficiente para capturar trends.

---

## Alertas de Quota

### YouTube
Se a quota exceder, erro HTTP 403:
```
quotaExceeded: The request cannot be completed because you have exceeded your quota.
```

### Google Trends
Se rate limit for atingido, erro 429:
```
Too Many Requests
```
Solucao: Esperar alguns minutos.

---

## Ultima Atualizacao
- **Data:** 2025-01-14
- **Versao:** 1.0
- **YouTube Key:** Projeto TrendMonitor (isolado)
