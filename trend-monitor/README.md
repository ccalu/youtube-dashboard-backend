# TREND MONITOR

Sistema automatizado de monitoramento de tendencias para pesquisa de mercado.

```
┌─────────────────────────────────────────────────────────────┐
│                    TREND MONITOR                            │
├─────────────────────────────────────────────────────────────┤
│  Coleta → Filtra → Pontua → Dashboard HTML                  │
│                                                             │
│  Fontes: Google Trends | YouTube | Reddit | Hacker News     │
│  Banco:  SQLite (local) ou Supabase (nuvem)                │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Testar com mock
python main.py --mock

# 4. Abrir dashboard
open output/trends-dashboard-*.html
```

## Estrutura do Projeto

```
trend-monitor/
│
├── main.py                 # Orquestrador principal
├── config.py               # Configuracoes e subnichos
├── requirements.txt        # Dependencias Python
├── .env.example            # Template de credenciais
├── .gitignore              # Arquivos ignorados pelo Git
│
├── database/               # Modulos de banco de dados
│   ├── __init__.py
│   ├── sqlite.py           # Cliente SQLite (local)
│   └── supabase.py         # Cliente Supabase (nuvem)
│
├── collectors/             # Coletores de dados
│   ├── google_trends.py    # pytrends (sem credencial)
│   ├── youtube.py          # YouTube Data API v3
│   ├── reddit.py           # Reddit PRAW
│   └── hackernews.py       # HN API (sem credencial)
│
├── filters/                # Filtros e scoring
│   └── relevance.py        # Score 0-100 por subnicho
│
├── generators/             # Geradores de output
│   └── html_report.py      # Dashboard HTML
│
├── templates/              # Templates Jinja2
│   └── dashboard.html
│
├── data/                   # Dados coletados (local)
│   └── *.json, *.db
│
├── output/                 # Dashboards gerados
│   └── *.html
│
└── docs/                   # Documentacao detalhada
    ├── SETUP.md            # Instalacao
    ├── ARQUITETURA.md      # Arquitetura do sistema
    ├── API_CREDENTIALS.md  # Como obter APIs
    ├── SUPABASE_SETUP.md   # Configurar Supabase
    ├── DASHBOARD.md        # Como usar o dashboard
    ├── SUBNICHOS.md        # Lista de subnichos
    └── DESENVOLVIMENTO.md  # Guia para devs
```

## Configuracao

### 1. Credenciais (obrigatorio para producao)

```bash
cp .env.example .env
# Editar .env com suas credenciais
```

| API | Credencial | Onde obter |
|-----|------------|------------|
| Google Trends | Nenhuma | - |
| YouTube | API Key | [Google Cloud Console](https://console.cloud.google.com/) |
| Reddit | Client ID + Secret | [Reddit Apps](https://www.reddit.com/prefs/apps) |
| Hacker News | Nenhuma | - |
| Supabase | URL + Key | [Supabase](https://supabase.com/) |

### 2. Banco de Dados

- **Sem configurar**: Usa SQLite local (`data/trends.db`)
- **Com Supabase**: Dados na nuvem (ver `docs/SUPABASE_SETUP.md`)

## Comandos

```bash
python main.py                    # Coleta + Dashboard
python main.py --mock             # Dados mock (teste)
python main.py --collect-only     # So coleta
python main.py --generate-only    # So dashboard
python main.py --date 2025-01-10  # Data especifica
```

## Dashboard

O dashboard HTML tem 4 abas:

| Aba | Conteudo |
|-----|----------|
| **GERAL** | Todos os trends, por fonte e pais |
| **DIRECIONADO** | Filtrado por subnichos, com score |
| **RELATORIO** | Resumo executivo e insights |
| **HISTORICO** | Calendario e trends evergreen |

## Subnichos Monitorados

1. Relatos de Guerra
2. Guerras e Civilizacoes
3. Empreendedorismo
4. Terror
5. Misterios
6. Psicologia e Mindset
7. Historias Sombrias

Ver `docs/SUBNICHOS.md` para keywords.

## Documentacao

| Documento | Descricao |
|-----------|-----------|
| [docs/SETUP.md](docs/SETUP.md) | Instalacao completa |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | Arquitetura e fluxo |
| [docs/API_CREDENTIALS.md](docs/API_CREDENTIALS.md) | Obter credenciais |
| [docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md) | Configurar Supabase |
| [docs/DASHBOARD.md](docs/DASHBOARD.md) | Usar o dashboard |
| [docs/SUBNICHOS.md](docs/SUBNICHOS.md) | Lista de subnichos |
| [docs/DESENVOLVIMENTO.md](docs/DESENVOLVIMENTO.md) | Guia para devs |

---

**Content Factory** // 2025
