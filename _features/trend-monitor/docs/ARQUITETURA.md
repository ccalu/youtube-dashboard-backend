# Arquitetura do Sistema

## Visao Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                    TREND MONITOR SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [EXECUCAO]                                                     │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              COLETORES (collectors/)                     │   │
│  │                                                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │   │
│  │  │ Google   │  │ Reddit   │  │ YouTube  │  │ Hacker  │ │   │
│  │  │ Trends   │  │ API      │  │ API      │  │ News    │ │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │   │
│  │       │             │             │             │       │   │
│  │       └─────────────┼─────────────┼─────────────┘       │   │
│  │                     ▼                                   │   │
│  │              ┌──────────────┐                           │   │
│  │              │   FILTROS    │                           │   │
│  │              │ (filters/)   │                           │   │
│  │              └──────┬───────┘                           │   │
│  └─────────────────────┼───────────────────────────────────┘   │
│                        ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BANCO DE DADOS                              │   │
│  │  ┌─────────────┐         ┌─────────────────┐            │   │
│  │  │   SQLite    │   OU    │    Supabase     │            │   │
│  │  │   (local)   │         │    (nuvem)      │            │   │
│  │  └─────────────┘         └─────────────────┘            │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              GERADOR HTML (generators/)                  │   │
│  │              Dashboard com 4 abas                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

## Estrutura de Arquivos

```
trend-monitor/
├── main.py                  # Orquestrador principal
├── config.py                # Configuracoes centrais
├── database.py              # Cliente SQLite (local)
├── database_supabase.py     # Cliente Supabase (nuvem)
│
├── collectors/              # Coletores de dados
│   ├── __init__.py
│   ├── google_trends.py     # pytrends
│   ├── youtube.py           # YouTube Data API v3
│   ├── reddit.py            # PRAW
│   └── hackernews.py        # HN API publica
│
├── filters/                 # Filtros e scoring
│   ├── __init__.py
│   └── relevance.py         # Score 0-100 por subnicho
│
├── generators/              # Geradores de output
│   ├── __init__.py
│   └── html_report.py       # Jinja2 templates
│
├── templates/               # Templates HTML
│   └── dashboard.html       # Template do dashboard
│
├── data/                    # Dados coletados
│   ├── trends_*.json        # JSON diario
│   └── trends.db            # SQLite local
│
├── output/                  # Saida gerada
│   └── trends-dashboard-*.html
│
├── docs/                    # Documentacao
│   └── *.md
│
├── .env                     # Credenciais (nao versionar!)
├── .env.example             # Template de credenciais
└── requirements.txt         # Dependencias Python
```

## Fluxo de Dados

### 1. Coleta
```
APIs Externas → Coletores → Dados Raw (JSON)
```

Cada coletor retorna lista de dicts:
```python
{
    "title": "Titulo do trend",
    "source": "youtube",
    "country": "BR",
    "volume": 125000,
    "url": "https://...",
    "collected_at": "2025-01-13T06:00:00"
}
```

### 2. Filtragem
```
Dados Raw → RelevanceFilter → Dados Filtrados + Score
```

O filtro calcula score (0-100) baseado em:
- Match de keywords do subnicho
- Volume/popularidade
- Presenca em multiplas fontes

### 3. Persistencia
```
Dados Filtrados → Database → trends table
                          → patterns table
```

**Tabela trends:**
- Todos os trends coletados
- Unique por (title, source, date)

**Tabela patterns:**
- Analise de recorrencia
- Detecta evergreen (7+ dias)

### 4. Geracao
```
Database + Filtrados → HTMLGenerator → Dashboard HTML
```

## Tabelas do Banco

### trends
```sql
CREATE TABLE trends (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,           -- google_trends, youtube, reddit, hackernews
    country TEXT DEFAULT 'global',
    language TEXT DEFAULT 'en',
    volume INTEGER DEFAULT 0,
    url TEXT,
    collected_at TIMESTAMPTZ,
    collected_date DATE,
    raw_data JSONB,
    UNIQUE(title, source, collected_date)
);
```

### trend_patterns
```sql
CREATE TABLE trend_patterns (
    id SERIAL PRIMARY KEY,
    title_normalized TEXT UNIQUE,
    first_seen DATE,
    last_seen DATE,
    days_active INTEGER DEFAULT 1,
    total_volume BIGINT DEFAULT 0,
    is_evergreen BOOLEAN DEFAULT FALSE,  -- true se days_active >= 7
    is_growing BOOLEAN DEFAULT FALSE
);
```

### collections
```sql
CREATE TABLE collections (
    id SERIAL PRIMARY KEY,
    collected_date DATE UNIQUE,
    collected_at TIMESTAMPTZ,
    total_trends INTEGER,
    sources_used JSONB,
    status TEXT DEFAULT 'completed'
);
```

## Paises Monitorados

| Codigo | Pais | Idioma |
|--------|------|--------|
| US | Estados Unidos | Ingles |
| BR | Brasil | Portugues |
| ES | Espanha | Espanhol |
| MX | Mexico | Espanhol |
| FR | Franca | Frances |
| JP | Japao | Japones |
| KR | Coreia do Sul | Coreano |

## Pontos de Extensao

### Adicionar novo coletor
1. Criar arquivo em `collectors/`
2. Implementar classe com metodo `collect_all()`
3. Registrar em `collectors/__init__.py`
4. Adicionar chamada em `main.py`

### Adicionar novo subnicho
1. Editar `SUBNICHOS` em `config.py`
2. Definir keywords em PT, EN, ES

### Mudar banco de dados
1. Implementar mesma interface de `database.py`
2. Metodos: `save_trends()`, `update_patterns()`, `get_evergreen_trends()`
