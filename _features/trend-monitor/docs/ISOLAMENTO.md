# Garantia de Isolamento

Este documento descreve como o Trend Monitor e 100% isolado do Dashboard de Mineracao existente.

## Resumo

| Aspecto | Dashboard Mineracao | Trend Monitor |
|---------|--------------------|--------------|
| Pasta | `/docs/` | `/docs/trend-monitor/` |
| Entry Point | `main.py` (FastAPI) | `trend-monitor/main.py` (Script) |
| Banco | Supabase | Supabase (MESMO, tabelas diferentes) |
| Tabelas | canais, videos, notificacoes | trends, trend_patterns, collections |

---

## Tabelas no Supabase

### Dashboard Mineracao (EXISTENTES - NAO TOCAR)
```
canais              - Canais monitorados
videos              - Videos coletados
notificacoes        - Sistema de alertas
spreadsheet_ids     - IDs das planilhas
...outras tabelas do dashboard
```

### Trend Monitor (NOVAS - ISOLADAS)
```
trends              - Trends coletados de 4 fontes
trend_patterns      - Padroes detectados (evergreen)
collections         - Metadados de cada coleta
```

**GARANTIA:** O Trend Monitor NUNCA faz SELECT, INSERT, UPDATE ou DELETE em tabelas do Dashboard.

---

## APIs Utilizadas

### Dashboard Mineracao
- YouTube API: `channels().list()`, `videos().list()` por canal
- Supabase: tabelas de canais e videos

### Trend Monitor
- YouTube API: `videos().list(chart='mostPopular')` - endpoint DIFERENTE
- Google Trends: pytrends (scraping, sem API key)
- Reddit: PRAW (API separada)
- Hacker News: API publica

**GARANTIA:** Endpoints diferentes, sem sobreposicao.

---

## Execucao

### Dashboard Mineracao
```bash
cd "/Users/marcelo/Downloads/Dashboard Youtube/docs"
python main.py  # FastAPI na porta 8000
```

### Trend Monitor
```bash
cd "/Users/marcelo/Downloads/Dashboard Youtube/docs/trend-monitor"
python main.py  # Script standalone, sem servidor
```

**GARANTIA:** Executaveis diferentes, em pastas diferentes.

---

## Credenciais

### Compartilhadas (seguro)
- `SUPABASE_URL` - Mesmo projeto Supabase
- `SUPABASE_KEY` - Mesma chave anon

### Separadas
- Dashboard: 20 YouTube API keys no Railway
- Trend Monitor: 1 YouTube API key local (pode ser qualquer uma das 20)
- Trend Monitor: Reddit credentials (proprio)

**GARANTIA:** Credenciais Supabase sao compartilhadas, mas acessam tabelas diferentes.

---

## Fluxo de Dados

```
DASHBOARD MINERACAO:
YouTube (canais) ──► collector.py ──► Supabase (canais, videos)
                                            ↓
                                    FastAPI (main.py)
                                            ↓
                                    Frontend React

TREND MONITOR (ISOLADO):
Google Trends ──┐
YouTube Trending ──┤
Reddit ──┤──► main.py ──► Supabase (trends, patterns)
Hacker News ──┘                    ↓
                            Dashboard HTML local
```

**GARANTIA:** Fluxos completamente separados, sem intersecao.

---

## Checklist de Isolamento

- [x] Pasta separada: `/docs/trend-monitor/`
- [x] Tabelas proprias: `trends`, `trend_patterns`, `collections`
- [x] Entry point separado: `trend-monitor/main.py`
- [x] .env proprio: `trend-monitor/.env`
- [x] Requirements proprio: `trend-monitor/requirements.txt`
- [x] Output proprio: `trend-monitor/output/`
- [x] Sem imports do projeto pai
- [x] Sem dependencias do projeto pai

---

## Regras para Futuras Alteracoes

1. **NUNCA** importar codigo do Dashboard Mineracao
2. **NUNCA** criar tabelas com nomes existentes
3. **SEMPRE** manter documentacao atualizada
4. **SEMPRE** testar isoladamente antes de deploy

---

## Ultima Atualizacao

- **Data:** 2025-01-13
- **Versao:** 1.0
- **Status:** Isolamento confirmado e documentado
